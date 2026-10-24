"""Split confirmed improvements into behavioural and fuel-only gains.

    python3 -m genome.search.fuel10 RUN_DIR --arm genome|policy --opponents A,B,C [--confirm-games 120]

Every child that beat its parent by the confirmed margin is re-scored once, with its parent(s), on the
same confirm games with every bot's fuel budget x10 (both sides). A gain that survives at 10x is
behavioural; one that vanishes came from spending less fuel (the seeds start with different fuel slack,
so the comparison counts the two kinds separately). Writes RUN_DIR/fuel10.json, read by report.py.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .score import Scorer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--arm", choices=["genome", "policy"], required=True)
    ap.add_argument("--opponents", required=True)
    ap.add_argument("--confirm-games", type=int, default=120)
    ap.add_argument("--beat-margin", type=float, default=0.03)
    ap.add_argument("--fuel-mult", type=float, default=10.0)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    progs = {}
    for line in open(Path(args.run) / "programs.jsonl"):
        p = json.loads(line)
        progs.setdefault(p["id"], p)
    scorer = Scorer(args.opponents.split(","), confirm_games=args.confirm_games, threads=args.threads,
                    fuel_mult=args.fuel_mult)
    gains = [p for p in progs.values() if not p["error"]
             and p["metrics"].get("delta_confirm", -1) > args.beat_margin]

    def one(p):
        c = scorer.confirm(p["text"], args.arm)
        ps = [scorer.confirm(progs[i]["text"], args.arm) for i in p["metrics"]["parent_ids"]]
        d = c.score - max(r.score for r in ps)
        return str(p["id"]), {"delta_confirm": p["metrics"]["delta_confirm"], "delta_fuel10": d,
                              "behavioural": d > args.beat_margin}

    with ThreadPoolExecutor(args.workers) as pool:
        out = dict(pool.map(one, gains))
    (Path(args.run) / "fuel10.json").write_text(json.dumps(out, indent=1))
    b = sum(v["behavioural"] for v in out.values())
    print(f"{len(out)} confirmed gains: {b} behavioural (survive at x{args.fuel_mult:g}), {len(out) - b} fuel-only")


if __name__ == "__main__":
    main()
