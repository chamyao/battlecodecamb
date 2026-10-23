"""Re-score policies on fresh games (seeds the search never uses), e.g. before committing a new best.

    python3 -m funsearch.validate runs/pilot/best.policy policies/v1.policy --games 400
    python3 -m funsearch.validate --run long --top 3      # the run's top 3 distinct programs
"""
import argparse
import json

from .evaluate import ROOT, evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("policies", nargs="*")
    ap.add_argument("--run", help="also validate the top programs of runs/<name>")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--games", type=int, default=400, help="games per opponent")
    ap.add_argument("--opponents", default=f"builtin:starter,{ROOT / 'policies' / 'v1.policy'}")
    ap.add_argument("--seed", type=int, default=1_000_003, help="far from the search's eval seeds (0, 1)")
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    paths = list(args.policies)
    if args.run:
        out = ROOT / "runs" / args.run / "top"
        out.mkdir(exist_ok=True)
        progs = [json.loads(line) for line in open(ROOT / "runs" / args.run / "programs.jsonl")]
        seen = set()
        for p in sorted((p for p in progs if p["error"] is None), key=lambda p: -p["score"]):
            if p["text"] in seen:
                continue
            seen.add(p["text"])
            path = out / f"p{p['id']}.policy"
            path.write_text(p["text"])
            print(f"{path}: run score {p['score']:.3f}")
            paths.append(str(path))
            if len(seen) == args.top:
                break
    for path in paths:
        r = evaluate(open(path).read(), opponents=tuple(args.opponents.split(",")), games=args.games,
                     threads=args.threads, seed=args.seed)
        if not r.ok:
            print(f"{path}: error {r.error}")
            continue
        per = ", ".join(f"{k} win {v['win_rate']:.3f} (gems {v['a_gems']:.0f}-{v['b_gems']:.0f})"
                        for k, v in r.per_opponent.items())
        print(f"{path}: score {r.score:.3f} | {per}", flush=True)


if __name__ == "__main__":
    main()
