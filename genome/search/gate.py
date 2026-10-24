"""Ladder gate for arena genomes, and a gatekeeper that applies it to running arenas from their pushed state.

Gate (outside selection), for one genome:
1. screen: --screen-games games vs the live bot (--ref) on a fresh seed; continue only at >= --screen-min;
2. head to head vs the live bot: 2 x --h2h games on fresh seeds; passes when the win rate's lower bound
   (--z standard errors) is above 50% (>= 53.5% over 800); a borderline batch gets 800 more;
3. every fixed anchor: 2 x --anchor-games games; no drop > --regress vs the live bot's own rate there;
4. fuel x10 re-score of the head to head (behavioural vs fuel-only strength), logged.

Gatekeeper (works on arenas that are already running, without restarting them):

    python3 -m genome.search.gate --out $OUT --arena arenaA-1/arena --arena arenaB-1/arena --every 600

Every --every seconds it fetches origin/remote/genome, and for each arena takes the top --top live genomes by
rating with >= --min-games games that have not been screened yet, and gates them. Results: <out>/gates.jsonl,
passing genomes in <out>/candidates/. Stops when every arena's job has an rc file, or after --max-hours.
"""
import argparse
import json
import subprocess
import time
from pathlib import Path

from funsearch.evaluate import ROOT

from .. import build as gbuild
from .score import Scorer

SCREEN_SEED = 3_000_017
FRESH_SEEDS = (5_000_011, 6_000_011)
MORE_SEEDS = (7_000_011, 8_000_011)
ANCHORS = ("policies/v7.policy", "policies/candidates/tune-v20-L1.policy",
           "policies/candidates/rall2-ca4-lean-g.policy", "policies/opp-tune5-metadraft.policy")
REF = "policies/candidates/style-gconv1.policy"


def rate(a, b, seeds, games, threads, fuel_mult=1.0):
    sc = Scorer([], threads=threads, fuel_mult=fuel_mult)
    w = n = 0
    for sd in seeds:
        st = sc.play(a, b, sd, games)
        if "error" in st:
            raise RuntimeError(st["error"])
        w, n = w + st["a_wins"], n + st["games"]
    return w, n


def spec_of(path_or_text, kind=None):
    return Scorer([], threads=1)._spec(path_or_text, kind)


def gate(text, ref, anchors, threads=5, screen_games=400, screen_min=0.55, h2h=400, anchor_games=200, z=2.0,
         regress=0.03, bars=None, log=print):
    """Gate one genome (source text). bars: cache {anchor: (wins, games)} of the reference's own rates."""
    spec, rspec = spec_of(text, "genome"), spec_of(ref)
    rec = {}
    w, n = rate(spec, rspec, (SCREEN_SEED,), screen_games, threads)
    rec["screen"] = w / n
    if w / n < screen_min:
        rec["passed"] = False
        return rec
    w, n = rate(spec, rspec, FRESH_SEEDS, h2h, threads)
    if 0.5 <= w / n < 0.5 + z * 0.5 / n ** 0.5:
        w2, n2 = rate(spec, rspec, MORE_SEEDS, h2h, threads)
        w, n = w + w2, n + n2
    rec.update(h2h=w / n, h2h_games=n, clear=w / n >= 0.5 + z * 0.5 / n ** 0.5)
    bars = {} if bars is None else bars
    drops = {}
    for anc in anchors:
        key = f"{Path(ref).name}|{Path(anc).name}"
        if key not in bars:
            bars[key] = rate(rspec, spec_of(anc), FRESH_SEEDS, anchor_games, threads)
        bw, bn = bars[key]
        cw, cn = rate(spec, spec_of(anc), FRESH_SEEDS, anchor_games, threads)
        drops[Path(anc).stem] = round(cw / cn - bw / bn, 3)
    rec["anchor_deltas"] = drops
    fw, fn = rate(spec, rspec, FRESH_SEEDS[:1], h2h, threads, fuel_mult=10.0)
    rec["h2h_fuel10"] = fw / fn
    rec["passed"] = rec["clear"] and min(drops.values(), default=0.0) >= -regress
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
    ap.add_argument("--anchors", default=",".join(str(ROOT / a) for a in ANCHORS))
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-games", type=int, default=200)
    ap.add_argument("--every", type=float, default=600)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--screen-games", type=int, default=400)
    ap.add_argument("--screen-min", type=float, default=0.55)
    ap.add_argument("--max-hours", type=float, default=12)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "candidates").mkdir(parents=True, exist_ok=True)
    anchors = args.anchors.split(",")
    seen, bars = set(), {}
    gates = out / "gates.jsonl"
    if gates.exists():
        seen = {json.loads(l)["key"] for l in open(gates)}
    # genomes earlier gatekeeper jobs already gated stay gated
    ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "origin/remote/genome"],
                        capture_output=True, text=True).stdout.split()
    for path in ls:
        if path.startswith("gatekeeper-") and path.endswith("/gates.jsonl"):
            txt = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/remote/genome:{path}"],
                                 capture_output=True, text=True).stdout
            seen |= {json.loads(l)["key"] for l in txt.splitlines() if l.strip()}

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
            if chain.endswith("*"):  # every job <prefix>N on jobs/genome, in order: a chain of resumes
                import re
                names = git("ls-tree", "--name-only", "origin/jobs/genome").stdout.split()
                jobs = sorted({n[:-3] for n in names if n.startswith(chain[:-1]) and n.endswith(".sh")},
                              key=lambda j: int(re.sub(r"\D", "", j[len(chain) - 1:]) or 0))
                dirs = [f"{j}/arena" for j in jobs]
                done = all(git("cat-file", "-e", f"origin/remote/genome:{j}/rc").returncode == 0 for j in jobs)
            else:
                dirs = chain.split("+")
                done = git("cat-file", "-e", f"origin/remote/genome:{dirs[-1].split('/')[0]}/rc").returncode == 0
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
            live = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"]
                    and m["games"] >= args.min_games]
            for m in sorted(live, key=lambda m: -m["mu"])[:args.top]:
                # one key per genome across a chain of resumed jobs, per reference bot
                key = f"{dirs[0]}:{m['name']}@{Path(args.ref).stem}"
                if key in seen:
                    continue
                seen.add(key)
                g = git("show", f"origin/remote/genome:{arena}/{m['path']}")
                if g.returncode != 0:
                    log(f"{key}: genome file missing")
                    continue
                log(f"gate {key} (mu {m['mu']:.2f}, {m['games']} games)")
                try:
                    rec = gate(g.stdout, args.ref, anchors, args.threads, args.screen_games, args.screen_min,
                               bars=bars, log=log)
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
                    (out / "candidates" / f"{job}-{m['name']}.genome").write_text(g.stdout)
        if finished == len(args.arena):
            log("all arenas finished")
            break
        time.sleep(max(0, args.every - (time.time() - t0)))


if __name__ == "__main__":
    main()
