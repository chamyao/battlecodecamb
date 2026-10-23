"""Re-score policies on fresh games (seeds the search never uses), e.g. before committing a new best.

    python3 -m funsearch.validate runs/pilot/best.policy policies/v1.policy --games 400
"""
import argparse

from .evaluate import ROOT, evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("policies", nargs="+")
    ap.add_argument("--games", type=int, default=400, help="games per opponent")
    ap.add_argument("--opponents", default=f"builtin:starter,{ROOT / 'policies' / 'v1.policy'}")
    ap.add_argument("--seed", type=int, default=1_000_003, help="far from the search's eval seeds (0, 1)")
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args()
    for path in args.policies:
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
