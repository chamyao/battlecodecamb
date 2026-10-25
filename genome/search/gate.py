"""Ladder gate for arena genomes, and a gatekeeper that applies it to running arenas from their pushed state.

Every game is fixed by its map and side: genome-vs-genome games do not depend on the seed, and policies are
seeded as deployed (--bot-seeds). So a pair has exactly 80 distinct games (40 maps x 2 sides), and the gate
plays each once (SE ~5.6 points at 50%); repeating them adds no evidence. Variety comes from maps and opponents.

Gate (outside selection), for one genome:
1. head to head vs the live bot (--ref): the 80 games; passes at >= --min-wins (default 43/80 = 53.75%);
2. every fixed anchor: its 80 games; no drop > --regress vs the live bot's own rate there;
3. fuel x10 re-play of the head to head (behavioural vs fuel-only strength), logged.

Gatekeeper (works on arenas that are already running, without restarting them):

    python3 -m genome.search.gate --out $OUT --arena arenaA-1/arena --arena arenaB-1/arena --every 600

Every --every seconds it fetches origin/remote/genome, and for each arena takes the top --top live genomes by
rating with >= --min-games games that have not been screened yet, and gates them. Results: <out>/gates.jsonl,
passing genomes in <out>/candidates/. Stops when every arena's job has an rc file, or after --max-hours.
"""
import argparse
import json
import os
import urllib.request
import subprocess
import time
from pathlib import Path

from funsearch.evaluate import MAPS, ROOT

from .. import build as gbuild
from .score import Scorer

SEED = 1  # irrelevant to the outcome (games are fixed by map and side); kept for the command line
ANCHORS = ("policies/v7.policy", "policies/candidates/tune-v20-L1.policy",
           "policies/candidates/rall2-ca4-lean-g.policy", "policies/opp-tune5-metadraft.policy")
REF = "policies/candidates/style-gconv1.policy"


def rate(a, b, threads, fuel_mult=1.0):
    """(wins, games) of side spec a vs b over the 80 distinct games: every map once from each side."""
    maps = sorted(MAPS)
    st = Scorer([], threads=threads, fuel_mult=fuel_mult, bot_seeds=True).play(a, b, SEED, 2 * len(maps), maps=maps)
    if "error" in st:
        raise RuntimeError(st["error"])
    return st["a_wins"], st["games"]


ARENA_URL = os.environ.get("ARENA_URL", "https://138-201-121-171.sslip.io/arena")


def _http(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"X-Arena-Client": "genome-search"}),
                                timeout=60) as r:
        return r.read().decode()


def spec_of(path_or_text, kind=None):
    return Scorer([], threads=1)._spec(path_or_text, kind)


class ArenaRater:
    """Plays a gate's matches on the arena service (POST /matches: 80 games, every map from both sides, bot seeds)
    instead of locally: no run or EC2 slot needed."""

    def __init__(self, engine, priority=1):
        self.engine, self.priority = engine, priority  # gates go ahead of bulk scoring (priority 0)

    def side(self, text_or_path, kind=None):
        if kind == "genome":
            return {"text": text_or_path, "kind": "genome"}
        if str(text_or_path).endswith(".genome"):  # genome files go inline (they need not exist in the engine's tree)
            return {"text": Path(text_or_path).read_text(), "kind": "genome"}
        p = Path(text_or_path)
        rel = p.resolve().relative_to(ROOT) if p.is_absolute() or p.resolve().is_relative_to(ROOT) else p
        return f"repo:{rel.as_posix()}"

    def rate(self, a, b, threads=None, fuel_mult=1.0):
        body = json.dumps({"a": a, "b": b, "engine": self.engine, "fuel_mult": fuel_mult, "bot_seeds": True,
                           "priority": self.priority}).encode()
        req = urllib.request.Request(f"{ARENA_URL}/matches?wait=110", data=body, method="POST",
                                     headers={"X-Arena-Client": "genome-search", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=130) as r:
            m = json.loads(r.read())["match"]
        while m["status"] not in ("done", "failed", "cancelled"):
            m = json.loads(_http(f"{ARENA_URL}/matches/{m['id']}?wait=110"))
            m = m.get("match", m)
        if m["status"] != "done":
            raise RuntimeError(f"arena match {m['id']} {m['status']}")
        return m["result"]["a_wins"], m["result"]["games"]


class LocalRater:
    def side(self, text_or_path, kind=None):
        return spec_of(text_or_path, kind)

    def rate(self, a, b, threads, fuel_mult=1.0):
        return rate(a, b, threads, fuel_mult)


def gate(text, ref, anchors, threads=5, min_wins=43, regress=0.03, bars=None, log=print, rater=None):
    """Gate one genome (source text). bars: cache {key: (wins, games)} of the reference's own anchor rates."""
    R = rater or LocalRater()
    spec, rspec = R.side(text, "genome"), R.side(ref)
    w, n = R.rate(spec, rspec, threads)
    rec = {"h2h_wins": w, "h2h_games": n, "h2h": w / n, "clear": w >= min_wins}
    bars = {} if bars is None else bars
    drops = {}
    for anc in anchors:
        key = f"{Path(ref).name}|{Path(anc).name}|80"
        if key not in bars:
            bars[key] = R.rate(rspec, R.side(anc), threads)
        bw, bn = bars[key]
        cw, cn = R.rate(spec, R.side(anc), threads)
        drops[Path(anc).stem] = {"wins": cw, "ref_wins": bw, "games": cn, "delta": round((cw - bw) / cn, 3)}
    rec["anchor_deltas"] = drops
    fw, fn = R.rate(spec, rspec, threads, fuel_mult=10.0)
    rec.update(h2h_fuel10_wins=fw, h2h_fuel10=fw / fn)
    rec["passed"] = rec["clear"] and min((d["delta"] for d in drops.values()), default=0.0) >= -regress
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--arena", action="append", required=True,
                    help="arena dir on remote/genome, a chain of resumed jobs' dirs joined by +, or a job prefix "
                         "ending in * (arenaA-*: every arenaA-N job on jobs/genome, finished when all have an rc); "
                         "(e.g. arenaB-1/arena+arenaB-2/arena): the latest pushed one is read, and the chain is "
                         "finished when its last job has an rc file")
    ap.add_argument("--ref", default=str(ROOT / REF), help="the live ladder bot")
    ap.add_argument("--anchors", action="append", default=None,
                    help="comma list of anchors for the drop check; may be repeated (lists are joined)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-games", type=int, default=200)
    ap.add_argument("--every", type=float, default=600)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--min-wins", type=int, default=43, help="head-to-head wins out of 80 to pass")
    ap.add_argument("--regate-from", default="", help="OLDREF:N: genomes gated vs OLDREF (file stem) with fewer than "
                                                      "N head-to-head wins are not re-gated vs the new --ref")
    ap.add_argument("--arena-engine", default="", help="play the gate's matches on the arena service at this engine "
                                                      "(commit sha or ref) instead of locally")
    ap.add_argument("--max-hours", type=float, default=12)
    ap.add_argument("--fresh", action="store_true",
                    help="ignore earlier gatekeepers' gates (a new runtime: every genome is gated again)")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "candidates").mkdir(parents=True, exist_ok=True)
    anchors = [a for part in (args.anchors or [",".join(str(ROOT / a) for a in ANCHORS)]) for a in part.split(",") if a]
    seen, bars = set(), {}
    gates = out / "gates.jsonl"
    if gates.exists():
        seen = {json.loads(l)["key"] for l in open(gates)}
    # genomes earlier gatekeeper jobs already gated stay gated
    ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "origin/remote/genome"],
                        capture_output=True, text=True).stdout.split()
    for path in ([] if args.fresh else ls):
        if path.startswith("gatekeeper-") and path.endswith("/gates.jsonl"):
            txt = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/remote/genome:{path}"],
                                 capture_output=True, text=True).stdout
            seen |= {json.loads(l)["key"] for l in txt.splitlines() if l.strip()}
            if args.regate_from:  # after a live-bot change: re-gate only genomes that beat the old live bot
                old, _, need = args.regate_from.partition(":")
                for l in txt.splitlines():
                    r = json.loads(l) if l.strip() else {}
                    if f"@{old}/80" in r.get("key", "") and r.get("h2h_wins", 0) < int(need or 43):
                        seen.add(r["key"].replace(f"@{old}/80", f"@{Path(args.ref).stem}/80"))
    ref_text = Path(args.ref).read_text() if args.ref.endswith(".genome") else None

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)

    def git(*a):
        return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)

    t_end = time.time() + args.max_hours * 3600
    while time.time() < t_end:
        t0 = time.time()
        f = git("fetch", "-q", "origin", "remote/genome")
        if f.returncode != 0:
            log(f"fetch failed: {f.stderr.strip()[:200]}")
        finished = 0
        git("fetch", "-q", "origin", "jobs/genome")
        for chain in args.arena:
            if chain.startswith("jobs:"):  # same as <prefix>* (for callers that refuse '*' in arguments)
                chain = chain[5:] + "*"
            if chain.startswith("api:"):  # an arena-service run: api:<run id>:<dir under the worktree>[=<key name>]
                spec, _, keyname = chain[4:].partition("=")
                run_id, _, rdir = spec.partition(":")
                base = f"{ARENA_URL}/runs/{run_id}"
                try:
                    status = json.loads(_http(base))["status"]
                    s = json.loads(_http(f"{base}/files/{rdir}/state.json"))
                except Exception as e:
                    log(f"{chain}: {type(e).__name__}: {e}")
                    continue
                finished += status in ("exited", "failed", "stopped", "cancelled")
                fetch = lambda p, base=base, rdir=rdir: _http(f"{base}/files/{rdir}/{p}")
                dirs, arena, job = [keyname or chain], chain, f"run{run_id}"
            elif chain.endswith("*"):  # every job <prefix>N on jobs/genome, in order: a chain of resumes
                import re
                names = git("ls-tree", "--name-only", "origin/jobs/genome").stdout.split()
                jobs = sorted({n[:-3] for n in names if n.startswith(chain[:-1]) and n.endswith(".sh")},
                              key=lambda j: int(re.sub(r"\D", "", j[len(chain) - 1:]) or 0))
                dirs = [f"{j}/arena" for j in jobs]
                done = all(git("cat-file", "-e", f"origin/remote/genome:{j}/rc").returncode == 0 for j in jobs)
            else:
                dirs = chain.split("+")
                done = git("cat-file", "-e", f"origin/remote/genome:{dirs[-1].split('/')[0]}/rc").returncode == 0
            if not chain.startswith("api:"):
                if not dirs:
                    continue
                finished += done
                have = [d for d in dirs if git("cat-file", "-e", f"origin/remote/genome:{d}/state.json").returncode == 0]
                arena = have[-1] if have else dirs[0]
                job = arena.split("/")[0]
                st = git("show", f"origin/remote/genome:{arena}/state.json")
                if st.returncode != 0:
                    log(f"{arena}: no state yet")
                    continue
                s = json.loads(st.stdout)

                def fetch(p, arena=arena):
                    g = git("show", f"origin/remote/genome:{arena}/{p}")
                    if g.returncode != 0:
                        raise FileNotFoundError(p)
                    return g.stdout
            live = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"]
                    and m["games"] >= args.min_games]
            for m in sorted(live, key=lambda m: -m["mu"])[:args.top]:
                # one key per genome across a chain of resumed jobs, per reference bot
                key = f"{dirs[0]}:{m['name']}@{Path(args.ref).stem}/80"
                if key in seen:
                    continue
                seen.add(key)
                if ref_text is not None and m.get("path") and fetch(m["path"]).strip() == ref_text.strip():
                    continue  # the live bot itself
                try:
                    text = fetch(m["path"])
                except Exception:
                    log(f"{key}: genome file missing")
                    continue
                log(f"gate {key} (mu {m['mu']:.2f}, {m['games']} games)")
                try:
                    rec = gate(text, args.ref, anchors, args.threads, args.min_wins, bars=bars, log=log,
                               rater=ArenaRater(args.arena_engine) if args.arena_engine else None)
                except Exception as e:
                    log(f"{key}: {type(e).__name__}: {e}")
                    continue
                rec = {"key": key, "arena": arena, "name": m["name"], "mu": m["mu"], "games": m["games"],
                       "ref": Path(args.ref).name, "t": round(time.time()), **rec}
                with open(gates, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
                log(f"{key}: {json.dumps({k: v for k, v in rec.items() if k not in ('key', 'arena', 't')})}"
                    f" -> {'CANDIDATE' if rec['passed'] else 'no'}")
                if rec["passed"]:
                    (out / "candidates" / f"{job}-{m['name']}.genome").write_text(text)
        if finished == len(args.arena):
            log("all arenas finished")
            break
        time.sleep(max(0, args.every - (time.time() - t0)))


if __name__ == "__main__":
    main()
