"""Score prompt-bench children (and their parents, and a measured null) against fixed opponents, CPU only.

    python3 -m genome.search.benchscore --out runs/benchscore --bench promptbench-2/bench --bench promptbench-r1b/bench \
        --state arenaA-1=<dir> --state arenaA-3=<dir> --null-from promptbench-2/bench --arena-engine <sha>

For every valid child of each bench (read from origin/remote/genome, as each bench finishes), every parent, and
--null children per parent of the --null-from bench (constant tuning with sigma --null-sigma: tiny changes, no API):
the 80 distinct games (40 maps x 2 sides, bot seeds) vs each opponent; the null children also vs their parent.
Parents are the reference: child minus parent on the same games. One line per (genome, opponent) in benchscore.jsonl
with bench, prompt, parent, cell. Matches run on the arena service (--arena-engine) or locally.
"""
import argparse
import json
import random
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from funsearch.evaluate import ROOT

from . import operators
from .gate import ArenaRater, LocalRater

OPPONENTS = ("policies/candidates/style-gconv1.policy", "policies/candidates/tune-v20-L1.policy",
             "policies/candidates/rall2-ca4-lean-g.policy", "policies/v7.policy", "policies/opp-tune5-metadraft.policy",
             "policies/candidates/tune-v20-L1c.policy")


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def show(path):
    r = git("show", f"origin/remote/genome:{path}")
    return r.stdout if r.returncode == 0 else None


class Scorer:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.rater = ArenaRater(a.arena_engine) if a.arena_engine else LocalRater()
        self.lock = threading.Lock()
        self.done = set()
        p = self.out / "benchscore.jsonl"
        if p.exists():
            self.done = {(r["genome"], r["opponent"]) for r in map(json.loads, open(p))}
        self.states = dict(s.split("=", 1) for s in a.state)

    def write(self, rec):
        with self.lock, open(self.out / "benchscore.jsonl", "a") as f:
            f.write(json.dumps({"t": round(time.time()), **rec}) + "\n")
            self.done.add((rec["genome"], rec["opponent"]))

    def parent_text(self, name):
        if name == "seed":
            return (ROOT / "genome/seeds/v23.genome").read_text()
        job, g = name.split(":")
        d = Path(self.states[job])
        s = json.loads((d / "state.json").read_text())
        return (d / s["members"][g]["path"]).read_text()

    def tasks_for(self, gid, text, meta, opponents, parent_text=None):
        out = []
        for opp in opponents:
            if (gid, Path(opp).stem) not in self.done:
                out.append((gid, text, meta, opp, None))
        if parent_text is not None and (gid, "parent") not in self.done:
            out.append((gid, text, meta, "parent", parent_text))
        return out

    def run_task(self, t):
        gid, text, meta, opp, ptext = t
        try:
            a = self.rater.side(text, "genome")
            b = self.rater.side(ptext, "genome") if opp == "parent" else self.rater.side(str(ROOT / opp))
            w, n = self.rater.rate(a, b, self.a.threads)
        except Exception as e:
            print(f"{gid} vs {opp}: {type(e).__name__}: {e}", flush=True)
            return
        self.write({"genome": gid, "opponent": "parent" if opp == "parent" else Path(opp).stem, "wins": w, "games": n,
                    **meta})

    def bench_tasks(self, bench):
        setup = None
        rounds = show(f"{bench}/rounds.jsonl")
        if rounds:
            for line in rounds.splitlines():
                r = json.loads(line)
                if r.get("event") == "setup":
                    setup = r
        kids = show(f"{bench}/children.jsonl") or ""
        retested = {json.loads(l)["prompt"] for l in kids.splitlines() if l.strip() and json.loads(l).get("tag") == "retest"}
        tasks = []
        for name in (setup or {}).get("parents", []):
            tasks += self.tasks_for(f"parent:{name}", self.parent_text(name), {"kind": "parent", "parent": name},
                                    OPPONENTS)
        for line in kids.splitlines():
            r = json.loads(line)
            if r.get("error") or r.get("tag") != "bench":
                continue
            # new benches name files per phase and record them; old ones used r<round>-<prompt>-<cell>, which a
            # retest phase overwrote for its prompts (those children are skipped when the bench had a retest)
            if "file" in r:
                path = f"{bench}/{r['file']}"
            elif r["prompt"] in retested:
                continue
            else:
                path = f"{bench}/genomes/r{r['round']}-{r['prompt']}-{r['cell']}.genome"
            text = show(path)
            if text is None:
                continue
            gid = f"{bench.split('/')[0]}:r{r['round']}-{r['prompt']}-{r['cell']}"
            tasks += self.tasks_for(gid, text, {"kind": "child", "bench": bench.split("/")[0], "prompt": r["prompt"],
                                                "parent": r["parent"], "cell": r["cell"],
                                                "vs_parent": r.get("wins")}, OPPONENTS)
        return tasks, setup is not None and git("cat-file", "-e", f"origin/remote/genome:{bench.split('/')[0]}/rc").returncode == 0

    def null_tasks(self, bench):
        rounds = show(f"{bench}/rounds.jsonl") or ""
        setup = next((json.loads(l) for l in rounds.splitlines() if json.loads(l).get("event") == "setup"), None)
        if not setup:
            return [], False
        tasks = []
        for name in setup["parents"]:
            ptext = self.parent_text(name)
            for k in range(self.a.null):
                c = operators.tune(ptext, random.Random(f"{name}:{k}"), sigma=self.a.null_sigma)
                if c.source is None:
                    continue
                gid = f"null:{name}:{k}"
                (self.out / "null").mkdir(exist_ok=True)
                (self.out / "null" / f"{gid.replace(':', '_')}.genome").write_text(c.source)
                tasks += self.tasks_for(gid, c.source, {"kind": "null", "parent": name, "cell": k,
                                                        "changes": c.log.get("changes")}, OPPONENTS, parent_text=ptext)
        return tasks, True

    def run(self):
        finished = set()
        nulls_done = False
        with ThreadPoolExecutor(self.a.workers) as ex:
            while True:
                git("fetch", "-q", "origin", "remote/genome")
                tasks = []
                if not nulls_done:
                    t, nulls_done = self.null_tasks(self.a.null_from)
                    tasks += t
                for b in self.a.bench:
                    if b in finished:
                        continue
                    t, over = self.bench_tasks(b)
                    tasks += t
                    if over and not t:
                        finished.add(b)
                print(f"[{time.strftime('%H:%M:%S')}] {len(tasks)} matches to play; finished benches {sorted(finished)}",
                      flush=True)
                list(ex.map(self.run_task, tasks))
                if len(finished) == len(self.a.bench) and nulls_done:
                    break
                if not tasks:
                    time.sleep(self.a.every)
        print("done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--bench", action="append", required=True, help="bench output dir on remote/genome")
    ap.add_argument("--state", action="append", default=[], help="job=dir: arena state holding the parents")
    ap.add_argument("--null-from", required=True, help="bench whose parents get the null children")
    ap.add_argument("--null", type=int, default=8)
    ap.add_argument("--null-sigma", type=float, default=0.02)
    ap.add_argument("--arena-engine", default="")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--every", type=float, default=300)
    a = ap.parse_args()
    Scorer(a).run()


if __name__ == "__main__":
    main()
