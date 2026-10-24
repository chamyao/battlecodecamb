"""Offline A/B of model-free loop changes on a finished generation (no API spend).

Replays one generation's database (runs/<run>/programs.jsonl) on the current build:

  climb  per-child hill-climb (funsearch.tune.climb_child, run.py's --tune-children settings) on the children
         that run.py would have climbed; each child is re-scored untuned and tuned on the same confirmation games.
  screen fixed-subset screen (current: seed 0, 32 games/opponent, 14 of 40 maps) vs a stratified screen (same games,
         every map tiled across opponents), both against a ground truth of all maps x both sides (80 games/opponent).
  stage  league tuning stage (funsearch.league.tune_candidate) on the top 3 candidates; untuned and tuned are
         validated like the league does (fresh seeds, 2 x val-games vs every opponent, h2h vs the best).

    python3 -m funsearch.loop_ab --run pure4-g4 --best policies/fs-p2.policy \
        --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/rall2-ca4-lean-g.policy,... --out runs/ab-g4.json
"""
import argparse
import json
import random
import time
import types
from pathlib import Path

from . import league
from .evaluate import ROOT, evaluate
from .tune import climb_child, climb_targets


def _w(o):
    return float(o.rsplit("@", 1)[1]) if "@" in o else 1.0


def climb_arm(progs, opponents, args, log):
    by_id = {p["id"]: p for p in progs}
    tune_opps = tuple(sorted((o for o in opponents if not o.startswith("builtin:starter")), key=lambda o: -_w(o))[:4])
    cands = []
    for p in progs:
        if p["error"] is not None or p["model"] == "seed" or not p["parents"]:
            continue
        par = max((by_id[i] for i in p["parents"] if i in by_id), key=lambda q: q["score"], default=None)
        if par is None or not climb_targets(par["text"], p["text"]):
            continue
        # run.py climbs a child only if its screen is within tune-slack of the parent's
        if p["metrics"].get("screen_score", p["score"]) >= par["metrics"].get("screen_score", par["score"]) - 0.15:
            cands.append((p, par))
    cands.sort(key=lambda c: -c[0]["score"])
    cands = cands[: args.climb_n]
    rows = []
    for k, (p, par) in enumerate(cands):
        seed = 100000 + k

        def ev(t):
            r = evaluate(t, opponents=tune_opps, games=args.tune_games, threads=args.threads, seed=seed)
            return r.score if r.ok else None
        t0 = time.time()
        tuned, info = climb_child(par["text"], p["text"], ev, steps=4, rng=random.Random(k), margin=0.03, max_rejects=2)
        secs = time.time() - t0
        row = {"id": p["id"], "climb_seconds": round(secs, 1), "evals": info["evals"] if info else 0,
               "changed": info["changed"] if info else {}}
        if tuned != p["text"]:
            # re-score both on the same confirmation games, not the climb's own games
            a = evaluate(p["text"], opponents=tuple(opponents), games=args.rescore_games, threads=args.threads, seed=1)
            b = evaluate(tuned, opponents=tuple(opponents), games=args.rescore_games, threads=args.threads, seed=1)
            row.update(untuned=round(a.score, 4), tuned=round(b.score, 4), delta=round(b.score - a.score, 4))
        rows.append(row)
        log(f"climb #{p['id']}: {row}")
    return rows


def stage_arm(run, opponents, best, args, log):
    fixed = [o for o in opponents if not o.startswith("builtin:") and o.rsplit("@", 1)[0] != best]
    older = [o.rsplit("@", 1)[0] for o in fixed]
    st = types.SimpleNamespace(stage_tune_steps=6, stage_tune_games=8, threads=args.threads)
    rows = []
    for p in league.top_distinct(run, 3):
        t0 = time.time()
        q = league.tune_candidate(p, opponents, st, None, run)
        secs = time.time() - t0
        row = {"id": p["id"], "stage_seconds": round(secs, 1), "kept": bool(q.get("tuned"))}
        for name, text in [("untuned", p["text"])] + ([("tuned", q["text"])] if q.get("tuned") else []):
            t1 = time.time()
            rates = league.win_rates(text, ["builtin:starter", best, *older], args.val_games, args.threads)
            row[name] = {"h2h": round(rates[Path(best).stem], 4),
                         "rates": {k: round(v, 4) for k, v in rates.items()}, "val_seconds": round(time.time() - t1, 1)}
        rows.append(row)
        log(f"stage #{p['id']}: {row}")
    return rows


def screen_arm(progs, opponents, args, log):
    import statistics as st
    valid = sorted((p for p in progs if p["error"] is None), key=lambda p: p["score"])
    step = max(1, len(valid) // args.screen_n)
    sample = valid[::step][: args.screen_n]
    rows = []
    for p in sample:
        t = p["text"]
        cur = evaluate(t, opponents=tuple(opponents), games=args.games, threads=args.threads, seed=0)
        strat = evaluate(t, opponents=tuple(opponents), games=args.games, threads=args.threads, seed=0, stratify=True)
        truth = evaluate(t, opponents=tuple(opponents), games=80, threads=args.threads, seed=12345, stratify=True)
        if not (cur.ok and strat.ok and truth.ok):
            continue
        rows.append({"id": p["id"], "current": round(cur.score, 4), "stratified": round(strat.score, 4),
                     "truth": round(truth.score, 4)})
        log(f"screen #{p['id']}: {rows[-1]}")

    def rank(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0] * len(xs)
        for k, i in enumerate(order):
            r[i] = k
        return r
    tr = [r["truth"] for r in rows]
    summary = {}
    for key in ("current", "stratified"):
        xs = [r[key] for r in rows]
        top = sorted(range(len(rows)), key=lambda i: -xs[i])[:5]
        true_top = sorted(range(len(rows)), key=lambda i: -tr[i])[:5]
        summary[key] = {"pearson": round(st.correlation(xs, tr), 3), "spearman": round(st.correlation(rank(xs), rank(tr)), 3),
                        "mean_bias": round(st.mean(x - y for x, y in zip(xs, tr)), 4),
                        "top5_overlap": len(set(top) & set(true_top))}
    log(f"screen summary: {summary}")
    return {"rows": rows, "summary": summary}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--best", required=True)
    ap.add_argument("--opponents", required=True, help="the run's weighted opponents, as given to funsearch.run")
    ap.add_argument("--arms", default="climb,stage")
    ap.add_argument("--screen-n", type=int, default=60, help="programs (spread over the score range) in the screen arm")
    ap.add_argument("--games", type=int, default=32, help="screen games per opponent (run.py --games)")
    ap.add_argument("--climb-n", type=int, default=24, help="children replayed in the climb arm")
    ap.add_argument("--tune-games", type=int, default=8)
    ap.add_argument("--rescore-games", type=int, default=64)
    ap.add_argument("--val-games", type=int, default=400)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    opponents = args.opponents.split(",")
    progs = [json.loads(l) for l in open(ROOT / "runs" / args.run / "programs.jsonl")]
    league.log = lambda m, f=None: print(m, flush=True)
    out = {"run": args.run, "best": args.best, "opponents": opponents}
    if "climb" in args.arms:
        out["climb"] = climb_arm(progs, opponents, args, print)
        Path(args.out).write_text(json.dumps(out, indent=1))
    if "screen" in args.arms:
        out["screen"] = screen_arm(progs, opponents, args, print)
        Path(args.out).write_text(json.dumps(out, indent=1))
    if "stage" in args.arms:
        out["stage"] = stage_arm(args.run, opponents, args.best, args, print)
        Path(args.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
