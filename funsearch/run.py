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

from .database import Database, Program
from .evaluate import ROOT, evaluate
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
    ap.add_argument("--eval-threads", type=int, default=2)
    ap.add_argument("--opponents", default=f"builtin:starter,{ROOT / 'policies' / 'v1.policy'}")
    ap.add_argument("--seed-policy", default=str(ROOT / "policies" / "v1.policy"))
    ap.add_argument("--eval-seed", type=int, default=0, help="same games for every program (fair comparison)")
    ap.add_argument("--islands", type=int, default=4)
    args = ap.parse_args()

    out = ROOT / "runs" / args.run
    out.mkdir(parents=True, exist_ok=True)
    db = Database(out / "programs.jsonl", islands=args.islands)
    db.load()
    opponents = tuple(args.opponents.split(","))

    def score(text, confirm=False):
        r = evaluate(text, opponents=opponents, games=args.games, threads=args.eval_threads, seed=args.eval_seed)
        best = db.best()
        if r.ok and (confirm or not best or r.score >= best[0].score - args.confirm_margin):
            # screening passed: the stored score comes from a larger, separate sample
            screen = r.score
            r = evaluate(text, opponents=opponents, games=args.confirm_games, threads=args.eval_threads,
                         seed=args.eval_seed + 1)
            r.per_opponent["screen_score"] = screen
            r.per_opponent["confirmed"] = True
        return r

    if not db.all:
        seed_text = Path(args.seed_policy).read_text()
        r = score(seed_text, confirm=True)
        if not r.ok:
            raise SystemExit(f"seed policy failed: {r.error}")
        db.seed(seed_text, r.score, r.per_opponent)
        print(f"seed score {r.score:.3f}")

    proposer = None
    if args.proposer == "claude":
        from .llm import BudgetExceeded, Proposer
        proposer = Proposer(args.budget, opus_every=args.opus_every)
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
        island, parents = db.sample(k=2)
        if not parents:
            return
        if proposer:
            try:
                text, model, cost, proposals = proposer.propose([(p.text, p.score, p.metrics) for p in parents])
            except BudgetExceeded as e:
                print(e)
                stop.set()
                return
        else:
            text, model, cost, proposals = mutate_constants(parents[-1].text, rng, n_changes=2), "mutate", 0.0, []
        if text is None:
            pid = db.add(Program(0, island, "", float("-inf"), [p.id for p in parents], model, "no policy in reply",
                                 {"cost": cost}))
            log_proposals(pid, None, model, proposals)
            return
        r = score(text)
        r.per_opponent["cost"] = cost
        p = Program(0, island, text, r.score, [p.id for p in parents], model, r.error, r.per_opponent)
        pid = db.add(p)
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
