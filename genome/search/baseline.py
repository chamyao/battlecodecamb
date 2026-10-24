"""Baseline of genomes vs the fixed anchors on fixed seeds (e.g. at a resume onto a new runtime).

    python3 -m genome.search.baseline --out base.jsonl --state arenaA-1/arena --top 3 --seed-genome genome/seeds/v23.genome

Plays the seed genome and the top --top live genomes (by mu, >= --min-games games) of an arena state against
each fixed anchor over the 80 distinct games (every map from both sides; games are fixed by map and side, with
policies seeded as deployed), and appends one JSON line per (genome, anchor). --games/--seeds are ignored.
"""
import argparse
import json
import time
from pathlib import Path

from funsearch.evaluate import ROOT

from .gate import ANCHORS, REF, rate, spec_of

SEEDS = (2_000_003,)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True, help="arena output dir (state.json, genomes/)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-games", type=int, default=40)
    ap.add_argument("--all", action="store_true", help="every live genome of the state (ignores --top/--min-games)")
    ap.add_argument("--seed-genome", default=str(ROOT / "genome/seeds/v23.genome"))
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--tag", default="")
    ap.add_argument("--anchors", default="", help="comma list of opponents (default: the live-bot reference and the "
                                                  "4 fixed anchors)")
    ap.add_argument("--no-seed", action="store_true")
    ap.add_argument("--names", default="", help="comma list of genome names to measure instead of the top --top")
    ap.add_argument("--seeds", default="", help="comma list of game seeds (default 2000003)")
    args = ap.parse_args()
    d = Path(args.state)
    s = json.loads((d / "state.json").read_text())
    live = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"] and m["games"] >= args.min_games]
    who = [] if args.no_seed else [("seed", Path(args.seed_genome).read_text(), None)]
    if args.all:
        allg = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"]]
        who += [(m["name"], (d / m["path"]).read_text(), m["mu"]) for m in sorted(allg, key=lambda m: -m["mu"])]
    elif args.names:
        allm = s["members"]
        who += [(n, (d / allm[n]["path"]).read_text(), allm[n]["mu"]) for n in args.names.split(",")]
    else:
        who += [(m["name"], (d / m["path"]).read_text(), m["mu"]) for m in sorted(live, key=lambda m: -m["mu"])[:args.top]]
    seeds = tuple(int(x) for x in args.seeds.split(",")) if args.seeds else SEEDS
    for name, text, mu in who:
        spec = spec_of(text, "genome")
        for anc in (args.anchors.split(",") if args.anchors else (REF,) + ANCHORS):
            w, n = rate(spec, spec_of(str(ROOT / anc)), args.threads)
            rec = {"tag": args.tag, "genome": name, "mu_old": mu, "anchor": Path(anc).stem, "wins": w, "games": n,
                   "win_rate": w / n, "games_distinct": "80 (40 maps x 2 sides, bot seeds)", "t": round(time.time())}
            with open(args.out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
