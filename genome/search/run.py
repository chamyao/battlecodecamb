"""Search loop for genomes, and the FunSearch baseline on the same harness (the evolvability check).

    python3 -m genome.search.run --run g-test --arm genome --seed genome/examples/starter.genome \
        --opponents builtin:starter --budget 0.5 --max-programs 20
    python3 -m genome.search.run --run p-test --arm policy --seed policies/candidates/style-gconv1.policy ...
    python3 -m genome.search.run --run g-dry --arm genome --no-llm ...     # tune + ID crossover only, no API

Both arms: islands and parent sampling from funsearch/database.py, Claude Haiku with Opus every 10th
call, the same hard budget, the same opponents, paired seeds and two-stage confirmation (score.py), and
the same share of constant-tuning children. They differ only in the representation and its operators:
- genome: edge-scoped mutation (Claude), crossover by gene ID (or Claude crossover by meaning when the
  parents are unrelated), constant tuning (ES);
- policy: funsearch/llm.py's prompt (two parents, write an improved version), funsearch/tune.py constants.

Results: runs/<name>/programs.jsonl (append-only; a rerun resumes). Report: genome/search/report.py.
"""
import argparse
import json
import os
import signal
import sys
import itertools
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from funsearch.database import Database, Program

from . import edit, operators
from .claude import BudgetExceeded, Claude
from .score import ROOT, Scorer, brief

SPEND = ROOT / "genome" / "SPEND.md"


def log_spend(run, programs, cost):
    text = SPEND.read_text()
    totals = re.findall(r"\|\s*\$?([\d.]+)\s*\|\s*$", text, re.M)
    total = (float(totals[-1]) if totals else 0.0) + cost
    with open(SPEND, "a") as f:
        f.write(f"| {time.strftime('%Y-%m-%d')} | genome/search {run} | {programs} | {cost:.2f} | {total:.2f} |\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", default="", help="results directory (default runs/<run>)")
    ap.add_argument("--arm", choices=["genome", "policy"], required=True)
    ap.add_argument("--seed", required=True, help="seed program (.genome or .policy); a comma list puts seed i on "
                                                   "island i mod --islands")
    ap.add_argument("--opponents", required=True, help="comma list: builtin:x, .policy, .pol or .genome")
    ap.add_argument("--budget", type=float, default=1.0, help="hard cap on Claude spend, USD")
    ap.add_argument("--opus-every", type=int, default=10)
    ap.add_argument("--max-programs", type=int, default=100)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--eval-threads", type=int, default=2)
    ap.add_argument("--screen-games", type=int, default=40, help="games per opponent, screen")
    ap.add_argument("--confirm-games", type=int, default=120, help="games per opponent, confirmation")
    ap.add_argument("--confirm-margin", type=float, default=0.1,
                    help="also confirm children within this of the best (funsearch rule)")
    ap.add_argument("--beat-margin", type=float, default=0.03, help="confirmed gain that counts as beating")
    ap.add_argument("--tune-rate", type=float, default=0.15, help="share of constant-tuning children")
    ap.add_argument("--cross-rate", type=float, default=0.15, help="genome arm: share of crossover children")
    ap.add_argument("--two-edge-prob", type=float, default=0.25,
                    help="starting share of two-edge mutations; then shifted toward the size that gives confirmed "
                         "gains (Laplace-smoothed gain rate per edge count, clipped to 0.1-0.6)")
    ap.add_argument("--islands", type=int, default=4)
    ap.add_argument("--no-llm", action="store_true", help="tuning and ID crossover only (testing)")
    ap.add_argument("--bot-seeds", action="store_true",
                    help="policies seeded as deployed: every game is fixed by map and side, so screen and confirm "
                         "both play the 2 x maps distinct games (set --screen-games/--confirm-games to 80)")
    ap.add_argument("--fitness", choices=["score", "wins", "fight"], default="score",
                    help="score: win rate + gem-margin bonus; wins: win rate only; fight: win rate + --kill-weight x our kills per game")
    ap.add_argument("--kill-weight", type=float, default=0.1, help="--fitness fight: weight of our kills per game")
    args = ap.parse_args(argv)

    out = Path(args.out) if args.out else ROOT / "runs" / args.run
    out.mkdir(parents=True, exist_ok=True)
    db = Database(out / "programs.jsonl", islands=args.islands)
    db.load()
    kind = args.arm
    scorer = Scorer(args.opponents.split(","), args.screen_games, args.confirm_games, threads=args.eval_threads,
                    bot_seeds=args.bot_seeds, fitness=args.fitness, kill_weight=args.kill_weight,
                    **({"confirm_seed": 0} if args.bot_seeds else {}))  # same games: confirm reuses the screen
    claude = None if args.no_llm else Claude(args.budget, opus_every=args.opus_every)
    spent0 = sum(p.metrics.get("cost", 0.0) for p in db.all)
    if claude:
        claude.spent = spent0

    if not db.all:
        seeds = args.seed.split(",")
        for i, path in enumerate(seeds):
            text = Path(path).read_text()
            s, c = scorer.screen(text, kind), scorer.confirm(text, kind)
            if not c.ok:
                raise SystemExit(f"seed {path} failed: {c.error}")
            m = {"screen": s.score, "confirm": c.score, "op": "seed", "per_opponent": c.per_opponent,
                 "seed_file": Path(path).name}
            if len(seeds) == 1:
                db.seed(text, c.score, m)
            else:
                for isl in range(i % args.islands, args.islands, len(seeds)) if len(seeds) < args.islands else \
                        [i % args.islands]:
                    db.add(Program(0, isl, text, c.score, model="seed", metrics=m))
            print(f"seed {Path(path).name} screen {s.score:.3f} confirm {c.score:.3f} ({brief(c)})", flush=True)

    rng = random.Random(len(db.all) * 7919 + 1)
    rng_lock = threading.Lock()
    counter = itertools.count(len(db.all))
    stop = threading.Event()
    started = len(db.all)
    t0 = time.time()

    def pscore(p, confirm=False):
        """Screen/confirm results of a stored program (recomputed from the cache, deterministic)."""
        return scorer.confirm(p.text, kind) if confirm else scorer.screen(p.text, kind)

    def two_edge_prob():
        """Shift edit size toward what gives confirmed gains (docs/GENOME.md, Mutation)."""
        k = 8  # prior strength, in children, around --two-edge-prob
        rate = {}
        for e in (1, 2):
            ps = [p for p in db.all if p.metrics.get("log", {}).get("n_edges") == e]
            gains = sum(1 for p in ps if p.metrics.get("beats_parent"))
            rate[e] = (gains + 0.05 * k) / (len(ps) + k)
        prior = args.two_edge_prob / (1 - args.two_edge_prob)
        odds = prior * rate[2] / rate[1]
        return min(0.6, max(0.1, odds / (1 + odds)))

    def propose(parents, n):
        with rng_lock:
            r = random.Random(rng.random())
        best = parents[-1]
        u = r.random()
        if u < args.tune_rate or args.no_llm and (len(parents) < 2 or u < 0.5):
            if kind == "genome":
                return operators.tune(best.text, r), [best]
            from funsearch.tune import mutate_constants
            t = mutate_constants(best.text, r, n_changes=r.choice([1, 1, 2, 3]))
            c = operators.Child(t, "tune", None if t != best.text else "no change",
                                {"lines_changed": edit.line_diff(best.text, t)})
            if c.error:
                c.source = None
            return c, [best]
        if kind == "genome":
            prefix = f"c{n}"
            if len(parents) == 2 and parents[0].text != parents[1].text and (
                    args.no_llm or u < args.tune_rate + args.cross_rate):
                a, b = parents[1], parents[0]
                if operators.relatedness(a.text, b.text) >= 0.5:
                    return operators.crossover(a.text, b.text, r), [a, b]
                if not args.no_llm:
                    return operators.llm_cross(a.text, a.score, b.text, b.score, claude, prefix), [a, b]
            if args.no_llm:
                return operators.tune(best.text, r), [best]
            return operators.mutate(best.text, claude, r, prefix, brief(pscore(best)), two_edge_prob()), [best]
        # policy arm: the existing FunSearch proposer prompt
        from funsearch.llm import SYSTEM
        shown = "\n\n".join(f"## Version {i} (score {p.score:.3f})\n```policy\n{p.text.strip()}\n```"
                            for i, p in enumerate(parents))
        user = f"{shown}\n\n## Version {len(parents)}\nWrite it."
        text, model, cost, info = claude.ask([SYSTEM], user)
        m = re.search(r"```policy\n(.*?)```", text or "", re.S)
        child = operators.Child(m.group(1) if m else None, "llm", None, {"llm": info}, model, cost)
        if child.source is None:
            child.error = "refusal" if text is None else "no policy in reply"
        elif child.source.strip() == best.text.strip():
            child.source, child.error = None, "no change"
        else:
            child.log["lines_changed"] = edit.line_diff(best.text, child.source)
        return child, list(parents) if len(parents) == 2 and parents[0].text != parents[1].text else [best]

    def one(_):
        if stop.is_set() or len(db.all) - started >= args.max_programs:
            return
        island, parents = db.sample(k=2)
        if not parents:
            return
        n = next(counter)
        try:
            child, ps = propose(parents, n)
        except BudgetExceeded as e:
            print(e, flush=True)
            stop.set()
            return
        except Exception as e:  # API failure etc.: log and continue
            print(f"[{n}] proposer failed: {type(e).__name__}: {e}", flush=True)
            return
        m = {"op": child.op, "model": child.model, "cost": child.cost, "log": child.log,
             "parent_ids": [p.id for p in ps]}
        if child.source is None:
            pid = db.add(Program(0, island, "", float("-inf"), [p.id for p in ps], child.model or child.op,
                                 child.error, m))
            print(f"[{pid}] {child.op} {child.model}: invalid: {child.error[:100]}", flush=True)
            return
        s = scorer.screen(child.source, kind)
        if not s.ok:
            pid = db.add(Program(0, island, child.source, float("-inf"), [p.id for p in ps],
                                 child.model or child.op, s.error, m))
            print(f"[{pid}] {child.op}: eval error: {s.error[:100]}", flush=True)
            return
        pr = [pscore(p) for p in ps]
        m["screen"] = s.score
        m["parent_screen"] = [r.score for r in pr]
        m["delta_screen"] = s.score - max(r.score for r in pr)
        m["twin"] = any(s.fingerprint == r.fingerprint for r in pr)
        best_now = db.best()[0]
        score = s.score
        if m["delta_screen"] > 0 or s.score >= best_now.score - args.confirm_margin:
            c = scorer.confirm(child.source, kind)
            pc = [pscore(p, confirm=True) for p in ps]
            m["confirm"] = c.score
            m["parent_confirm"] = [r.score for r in pc]
            m["delta_confirm"] = c.score - max(r.score for r in pc)
            m["beats_parent"] = m["delta_confirm"] > args.beat_margin
            m["per_opponent"] = c.per_opponent
            score = c.score
        else:
            m["per_opponent"] = s.per_opponent
        pid = db.add(Program(0, island, child.source, score, [p.id for p in ps], child.model or child.op, None, m))
        best = db.best()[0]
        if best.id == pid:
            write_top()
        spent = f" ${claude.spent:.2f}" if claude else ""
        conf = f" confirm {m['delta_confirm']:+.3f}" if "confirm" in m else ""
        size = child.log.get("lines_changed", "?")
        print(f"[{pid}] {child.op} {child.model} isl {island}: screen {m['delta_screen']:+.3f}{conf}"
              f"{' twin' if m['twin'] else ''} ({size} lines) | best {best.score:.3f} (#{best.id}){spent} | "
              f"{time.time() - t0:.0f}s", flush=True)

    def write_top(n=10):
        """best.<kind> and top.jsonl (the n best: id, score, lineage, per-opponent stats, text): small files a caller
        can fetch while programs.jsonl grows past a file-size limit."""
        with top_lock:
            ranked = sorted((p for p in db.all if p.error is None and p.score > float("-inf")), key=lambda p: -p.score)
            (out / f"best.{kind}").write_text(ranked[0].text)
            with open(out / "top.jsonl.tmp", "w") as f:
                for p in ranked[:n]:
                    f.write(json.dumps({"id": p.id, "score": p.score, "island": p.island, "parents": p.parents,
                                        "op": (p.metrics or {}).get("op"), "per_opponent": (p.metrics or {}).get("per_opponent"),
                                        "text": p.text}) + "\n")
            os.replace(out / "top.jsonl.tmp", out / "top.jsonl")

    top_lock = threading.Lock()
    signal.signal(signal.SIGTERM, lambda *_: (stop.set(), sys.exit(143)))  # a stopped run still writes best/top
    try:
        with ThreadPoolExecutor(args.workers) as pool:
            list(pool.map(one, range(args.max_programs * 2)))
    finally:
        best = db.best()[0]
        write_top()
        new = db.all[started:]
        cost = (claude.spent - spent0) if claude else 0.0
        if cost > 0 and not args.out:
            log_spend(args.run, len(new), cost)
        n_err = sum(1 for p in new if p.error)
        print(f"done: {len(new)} programs ({n_err} invalid), spent ${cost:.2f}; best #{best.id} {best.score:.3f}")


if __name__ == "__main__":
    main()
