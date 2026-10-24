"""FunSearch loop: sample parents -> propose -> score in the simulator -> store.

    python3 -m funsearch.run --run pilot --budget 2 --max-programs 200
    python3 -m funsearch.run --run test --proposer mutate --max-programs 40   # no API calls

Results go to runs/<name>/programs.jsonl (append-only; a rerun resumes) and
runs/<name>/best.policy. `touch runs/<name>/STOP` pauses a run gracefully (delete it to resume). The Claude proposer needs FUNSEARCH_ANTHROPIC_KEY, FUNSEARCH_API_KEY or ANTHROPIC_API_KEY.
"""
import argparse
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .database import Database, Program, cell_of
from .evaluate import ROOT, evaluate, executed_blocks
from .tune import mutate_constants


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--proposer", choices=["claude", "mutate"], default="claude")
    ap.add_argument("--budget", type=float, default=2.0, help="hard cap on Claude spend, USD")
    ap.add_argument("--opus-every", type=int, default=10, help="every Nth call uses Opus (0 = never)")
    ap.add_argument("--max-programs", type=int, default=200)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--games", type=int, default=32, help="games per opponent per evaluation")
    ap.add_argument("--confirm-games", type=int, default=160,
                    help="re-score candidates near the top on this many fresh games; stored score")
    ap.add_argument("--confirm-margin", type=float, default=0.1)
    ap.add_argument("--early-stop", type=float, default=0.08,
                    help="drop a candidate whose first quarter of confirmation games scores this far below "
                         "the best (0 = always play the full confirmation)")
    ap.add_argument("--eval-threads", type=int, default=2)
    ap.add_argument("--opponents", default=f"builtin:starter,{ROOT / 'policies' / 'v1.policy'}")
    ap.add_argument("--seed-policy", default=str(ROOT / "policies" / "v1.policy"))
    ap.add_argument("--inject", default="", help="policy paths added as parents (one island each, scored with "
                                                 "the run's opponents) unless already in the database")
    ap.add_argument("--eval-seed", type=int, default=0, help="same games for every program (fair comparison)")
    ap.add_argument("--islands", type=int, default=4)
    # exploration mode (opt-in): per-call prompt variants (axis, change type, framing, catalog, evidence,
    # crossover), a quality-diversity archive of behaviour cells, gentler selection, per-island bases
    ap.add_argument("--explore", action="store_true")
    ap.add_argument("--temperature", type=float, default=None, help="parent softmax temperature (default 0.05; "
                                                                    "0.2 with --explore)")
    ap.add_argument("--reset-every", type=int, default=None, help="programs between island resets (default 200; "
                                                                  "500 with --explore)")
    ap.add_argument("--archive-share", type=float, default=0.5,
                    help="with --explore: share of parent draws taken from random behaviour cells")
    ap.add_argument("--change-weights", default="0.55,0.3,0.15",
                    help="with --explore: weights of the edit, plan and rewrite change types (rewrites always use "
                         "Opus; in the first test they all scored ~-0.2)")
    ap.add_argument("--axes", default="", help="with --explore: comma-separated axis menu (default: all axes)")
    ap.add_argument("--novelty-lambda", type=float, default=0.0,
                    help="with --explore: weight of the executed-block rarity novelty in parent selection "
                         "(weight exp(score/T + lambda * novelty)); never used in scores or promotion")
    ap.add_argument("--island-seeds", default="", help="comma-separated policies, one per island (cycled), "
                                                      "instead of --seed-policy on every island")
    args = ap.parse_args()
    temperature = args.temperature if args.temperature is not None else (0.2 if args.explore else 0.05)
    reset_every = args.reset_every if args.reset_every is not None else (500 if args.explore else 200)

    out = ROOT / "runs" / args.run
    out.mkdir(parents=True, exist_ok=True)
    db = Database(out / "programs.jsonl", islands=args.islands, temperature=temperature, reset_every=reset_every)
    db.novelty_lambda = args.novelty_lambda if args.explore else 0.0
    db.load()
    opponents = tuple(args.opponents.split(","))

    def fingerprint(per_opponent):
        """Screening outcome; games are deterministic, so equal fingerprints mean equal play."""
        return json.dumps({k: {f: v for f, v in m.items() if f != "seconds"}
                           for k, m in sorted(per_opponent.items()) if isinstance(m, dict)}, sort_keys=True)

    # confirmed results by screening fingerprint: a child that plays exactly like a confirmed
    # program (a comment or dead-code edit) reuses its confirmation instead of replaying it
    confirmed = {p.metrics["screen_fp"]: p for p in db.all
                 if p.metrics.get("confirmed") and "screen_fp" in p.metrics}

    def score(text, confirm=False):
        r = evaluate(text, opponents=opponents, games=args.games, threads=args.eval_threads, seed=args.eval_seed)
        if not r.ok:
            return r
        fp = fingerprint(r.per_opponent)
        twin = confirmed.get(fp)
        if twin is not None:
            r.score = twin.score
            r.per_opponent = {k: v for k, v in twin.metrics.items() if k != "cost"}
            r.per_opponent["same_play_as"] = twin.id
            return r
        best = db.best()
        if confirm or not best or r.score >= best[0].score - args.confirm_margin:
            # screening passed: the stored score comes from a larger, separate sample
            screen = r.score
            if not confirm and best and args.early_stop:
                # first quarter of the confirmation games (interp_eval's games are a prefix of a
                # longer run with the same seed): a candidate clearly below the best stops here
                quarter = max(2, args.confirm_games // 8 * 2)
                q = evaluate(text, opponents=opponents, games=quarter, threads=args.eval_threads,
                             seed=args.eval_seed + 1)
                if q.ok and q.score < best[0].score - args.early_stop:
                    q.per_opponent["screen_score"] = screen
                    q.per_opponent["screen_fp"] = fp
                    q.per_opponent["confirm_stopped"] = quarter
                    return q
            r = evaluate(text, opponents=opponents, games=args.confirm_games, threads=args.eval_threads,
                         seed=args.eval_seed + 1)
            if not r.ok:
                return r
            r.per_opponent["screen_score"] = screen
            r.per_opponent["confirmed"] = True
            r.per_opponent["screen_fp"] = fp
        else:
            r.per_opponent["screen_fp"] = fp
        return r

    if not db.all:
        seeds = [x for x in args.island_seeds.split(",") if x] or [args.seed_policy]
        for k, path in enumerate(seeds[: args.islands]):
            seed_text = Path(path).read_text()
            r = score(seed_text, confirm=True)
            if not r.ok:
                raise SystemExit(f"seed policy {path} failed: {r.error}")
            if args.explore:
                blocks = executed_blocks(seed_text)
                if blocks is not None:
                    r.per_opponent["exec_blocks"] = sorted(blocks)
            islands = range(k, args.islands, len(seeds[: args.islands]))
            db.seed(seed_text, r.score, r.per_opponent, islands=islands)
            confirmed[r.per_opponent["screen_fp"]] = db.all[-1]
            print(f"seed {Path(path).stem} score {r.score:.3f} (islands {list(islands)})")
    have = {p.text for p in db.all}
    for k, path in enumerate(x for x in args.inject.split(",") if x):
        text = Path(path).read_text()
        if text in have:
            continue
        r = score(text, confirm=True)
        if r.ok:
            pid = db.add(Program(0, k % args.islands, text, r.score, [], f"inject:{Path(path).stem}", None,
                                 r.per_opponent))
            confirmed.setdefault(r.per_opponent["screen_fp"], db.all[-1])
            print(f"injected {path} as #{pid} (island {k % args.islands}): score {r.score:.3f}", flush=True)

    proposer = None
    if args.proposer == "claude":
        from .llm import BudgetExceeded, Proposer
        proposer = Proposer(args.budget, opus_every=args.opus_every)
    if args.explore:
        from .llm import sample_variant
    change_weights = tuple(float(x) for x in args.change_weights.split(","))
    axes = [a for a in args.axes.split(",") if a]
    if args.explore and axes:
        from .llm import AXES
        unknown = [a for a in axes if a not in AXES]
        if unknown:
            raise SystemExit(f"unknown --axes {unknown}; known: {list(AXES)}")
    variant_lock = threading.Lock()
    proposals_lock = threading.Lock()

    def log_proposals(pid, score, model, proposals):
        """Block wishes (# PROPOSE: lines) go to proposals.jsonl for the language owner."""
        if not proposals:
            return
        with proposals_lock, open(out / "proposals.jsonl", "a") as f:
            for text in proposals:
                f.write(json.dumps({"program": pid, "score": score, "model": model, "proposal": text}) + "\n")

    rng = random.Random(len(db.all))
    stop = threading.Event()
    started = len(db.all)
    t0 = time.time()

    def one(_):
        if (out / "STOP").exists():  # graceful pause: in-flight calls finish, no new ones start
            stop.set()
        if stop.is_set() or len(db.all) - started >= args.max_programs:
            return
        variant = None
        with variant_lock:
            use_archive = args.explore and rng.random() < args.archive_share
        drawn = db.sample_archive(k=2) if use_archive else None
        island, parents = drawn or db.sample(k=2)
        if not parents:
            return
        if args.explore:
            with variant_lock:
                variant = sample_variant(rng, len(parents), change_weights, axes)
                vrng = random.Random(rng.random())
            variant["source"] = "archive" if drawn else "island"
        if proposer:
            try:
                text, model, cost, proposals = proposer.propose([(p.text, p.score, p.metrics) for p in parents],
                                                                variant=variant, rng=vrng if variant else None)
            except BudgetExceeded as e:
                print(e)
                stop.set()
                return
        else:
            text, model, cost, proposals = mutate_constants(parents[-1].text, rng, n_changes=2), "mutate", 0.0, []
        if text is None:
            pid = db.add(Program(0, island, "", float("-inf"), [p.id for p in parents], model, "no policy in reply",
                                 {"cost": cost, **({"variant": variant} if variant else {})}))
            log_proposals(pid, None, model, proposals)
            return
        r = score(text)
        r.per_opponent["cost"] = cost
        if variant:
            r.per_opponent["variant"] = variant
            if r.ok:
                r.per_opponent["cell"] = cell_of(text, r.per_opponent)
                blocks = executed_blocks(text)
                if blocks is not None:
                    r.per_opponent["exec_blocks"] = sorted(blocks)
        p = Program(0, island, text, r.score, [p.id for p in parents], model, r.error, r.per_opponent)
        pid = db.add(p)
        if r.ok and r.per_opponent.get("confirmed") and "same_play_as" not in r.per_opponent:
            confirmed.setdefault(r.per_opponent["screen_fp"], p)
        log_proposals(pid, r.score if r.ok else None, model, proposals)
        best = db.best()[0]
        spent = f" ${proposer.spent:.2f}" if proposer else ""
        status = f"error: {r.error[:80]}" if r.error else f"score {r.score:.3f}"
        print(f"[{pid}] {model} island {island}: {status} | best {best.score:.3f} (#{best.id}){spent} | {time.time() - t0:.0f}s",
              flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(one, range(args.max_programs)))

    best = db.best()[0]
    (out / "best.policy").write_text(best.text)
    n_err = sum(1 for p in db.all[started:] if p.error)
    spent = f", spent ${proposer.spent:.2f}" if proposer else ""
    print(f"done: {len(db.all) - started} programs ({n_err} invalid){spent}; best #{best.id} score {best.score:.3f} -> {out / 'best.policy'}")


if __name__ == "__main__":
    main()
