"""Search for the strongest genome: islands + operators + league promotion + adaptive operator mix.

    python3 -m genome.search.strength --out runs/strength1 --seed genome/seeds/v23.genome \
        --pool policies/candidates/style-gconv1.policy@3,policies/v7.policy,... --budget 8

Generations. Each generation runs islands (funsearch/database.py) seeded with the current best genome.
Children come from four operator arms (operators.py): edge mutation with 1 edge, with 2 edges, crossover
(by gene ID when the parents are related, by meaning otherwise) and constant tuning. A child is screened
against the pool on paired seeds; one that screens above its parent is confirmed on more paired games
with the parent; a confirmed gain > --beat-margin is an improvement.

Fitness pool: the fixed opponents (--pool, `spec@weight`), the current best genome (--best-weight) and
the last --keep-promoted promoted genomes.

Every --round children (a round boundary):
- the top --candidates distinct children of the generation are validated on fresh seeds: head to head
  against the current best (--val-h2h games per seed over two seeds; passes when the win rate's lower
  bound, --z standard errors, is above 50%: >= 53.5% over 800 games; a borderline batch gets a second
  one) and per pool member (--val-games per seed; no drop > --regress against any member vs the best);
- a passing candidate (the best head to head if several) is promoted: written to <out>/promoted/,
  added to the pool, and the next generation starts from it;
- every new improvement is re-scored once with fuel x10 for both sides (behavioural vs fuel-only gain);
- the operator mix is updated: Thompson sampling on each arm's confirmed-improvement rate per child
  (Beta prior), with a floor so no arm drops to zero (docs/GENOME.md: shift effort toward what gives
  confirmed gains);
- <out>/report.md gets a section (genome/search/evoreport.py) and <out>/state.json is rewritten.
"""
import argparse
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from funsearch.database import Database, Program

from . import evoreport, operators
from .claude import BudgetExceeded, Claude
from .score import Scorer, brief

ARMS = ("mutate1", "mutate2", "cross", "tune")
FRESH_SEEDS = (5_000_011, 6_000_011)  # validation only; the search uses seeds 0 (screen) and 1 (confirm)
MORE_SEEDS = (7_000_011, 8_000_011)   # second batch for borderline head-to-head results


class Bandit:
    """Thompson sampling over operator arms on confirmed improvements per child, with a uniform floor."""

    def __init__(self, arms, floor, prior=(0.5, 10.0)):
        self.arms, self.floor, self.prior = arms, floor, prior
        self.n = {a: 0 for a in arms}
        self.g = {a: 0 for a in arms}

    def pick(self, rng):
        if rng.random() < self.floor * len(self.arms):
            return rng.choice(self.arms)
        a0, b0 = self.prior
        return max(self.arms, key=lambda a: rng.betavariate(a0 + self.g[a], b0 + self.n[a] - self.g[a]))

    def update(self, arm, gain):
        self.n[arm] += 1
        self.g[arm] += int(gain)

    def shares(self, samples=4000, seed=0):
        rng = random.Random(seed)
        c = {a: 0 for a in self.arms}
        for _ in range(samples):
            c[self.pick(rng)] += 1
        return {a: round(v / samples, 3) for a, v in c.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", required=True, help="seed genome")
    ap.add_argument("--pool", required=True, help="fixed opponents, comma list of spec[@weight]")
    ap.add_argument("--best-weight", type=float, default=2.0, help="weight of the current best genome in the pool")
    ap.add_argument("--keep-promoted", type=int, default=3, help="older promoted genomes kept in the pool")
    ap.add_argument("--budget", type=float, default=8.0)
    ap.add_argument("--opus-every", type=int, default=10)
    ap.add_argument("--max-programs", type=int, default=5000)
    ap.add_argument("--round", type=int, default=60, help="children per round (promotion boundary)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--threads", type=int, default=5, help="total simulator threads")
    ap.add_argument("--screen-games", type=int, default=40)
    ap.add_argument("--confirm-games", type=int, default=120)
    ap.add_argument("--beat-margin", type=float, default=0.03)
    ap.add_argument("--islands", type=int, default=4)
    ap.add_argument("--floor", type=float, default=0.08, help="minimum share of each operator arm")
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--val-h2h", type=int, default=400, help="head-to-head games per fresh seed (2 seeds)")
    ap.add_argument("--val-games", type=int, default=200, help="games per pool member per fresh seed (2 seeds)")
    ap.add_argument("--z", type=float, default=2.0)
    ap.add_argument("--regress", type=float, default=0.03)
    ap.add_argument("--fuel10-games", type=int, default=120)
    args = ap.parse_args(argv)

    out = Path(args.out)
    (out / "promoted").mkdir(parents=True, exist_ok=True)
    log_path = out / "log.txt"

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(log_path, "a") as f:
            f.write(line + "\n")

    state_path = out / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "gen": 0, "best": str(Path(args.seed).resolve()), "promoted": [], "validated": [], "bandit": None,
        "fuel10": {}, "boundaries": []}
    fixed = args.pool.split(",")
    eval_threads = max(1, args.threads // args.workers)
    scorer = Scorer([], args.screen_games, args.confirm_games, threads=eval_threads)
    scorer10 = Scorer([], args.screen_games, args.fuel10_games, threads=args.threads, fuel_mult=10.0)
    claude = Claude(args.budget, opus_every=args.opus_every)
    bandit = Bandit(list(ARMS), args.floor)
    if state["bandit"]:
        bandit.n, bandit.g = state["bandit"]["n"], state["bandit"]["g"]
    claude.spent = sum(json.loads(l)["metrics"].get("cost", 0.0)
                       for p in out.glob("g*/programs.jsonl") for l in open(p))

    def pool():
        older = [f"{p}" for p in state["promoted"][:-1][-args.keep_promoted:]]
        return fixed + [f"{state['best']}@{args.best_weight}"] + older

    def save_state():
        state["bandit"] = {"n": bandit.n, "g": bandit.g}
        state_path.write_text(json.dumps(state, indent=1))

    rng = random.Random(1 + len(state["validated"]))
    rng_lock = threading.Lock()
    stop = threading.Event()

    while not stop.is_set():
        gen = state["gen"]
        scorer.set_opponents(pool())
        scorer10.set_opponents(pool())
        best_text = Path(state["best"]).read_text()
        gdir = out / f"g{gen}"
        gdir.mkdir(exist_ok=True)
        db = Database(gdir / "programs.jsonl", islands=args.islands)
        db.load()
        if not db.all:
            s, c = scorer.screen(best_text, "genome"), scorer.confirm(best_text, "genome")
            if not c.ok:
                raise SystemExit(f"best genome failed: {c.error}")
            db.seed(best_text, c.score, {"screen": s.score, "confirm": c.score, "op": "seed", "arm": "seed",
                                         "per_opponent": c.per_opponent})
            log(f"generation {gen}: best {Path(state['best']).name} screen {s.score:.3f} confirm {c.score:.3f} "
                f"({brief(c)})")
        counter = [len(db.all)]

        def propose(parents, n, arm):
            with rng_lock:
                r = random.Random(rng.random())
            best = parents[-1]
            prefix = f"g{gen}c{n}"
            if arm == "cross" and len(parents) == 2 and parents[0].text != parents[1].text:
                a, b = parents[1], parents[0]
                if operators.relatedness(a.text, b.text) >= 0.5:
                    c = operators.crossover(a.text, b.text, r)
                    if c.error not in ("child equals a parent", "parents identical where they share genes"):
                        return c, [a, b], arm
                    arm = "mutate1"  # the parents differ in too few genes for a new combination
                else:
                    return operators.llm_cross(a.text, a.score, b.text, b.score, claude, prefix), [a, b], arm
            if arm == "tune":
                return operators.tune(best.text, r), [best], arm
            two = 1.0 if arm == "mutate2" else 0.0
            return (operators.mutate(best.text, claude, r, prefix, brief(scorer.screen(best.text, "genome")), two),
                    [best], arm)

        def one(_):
            if stop.is_set():
                return
            island, parents = db.sample(k=2)
            if not parents:
                return
            with rng_lock:
                n = counter[0]
                counter[0] += 1
                arm = bandit.pick(rng)
            if arm == "cross" and (len(parents) < 2 or parents[0].text == parents[1].text):
                arm = "mutate1"  # no two distinct parents on this island yet
            try:
                child, ps, arm = propose(parents, n, arm)
            except BudgetExceeded as e:
                log(str(e))
                stop.set()
                return
            except Exception as e:
                log(f"[g{gen}c{n}] proposer failed: {type(e).__name__}: {e}")
                return
            m = {"op": child.op, "arm": arm, "model": child.model, "cost": child.cost, "log": child.log,
                 "parent_ids": [p.id for p in ps], "island": island, "gen": gen, "t": time.time(),
                 "spent": claude.spent}
            if child.source is None:
                pid = db.add(Program(0, island, "", float("-inf"), m["parent_ids"], child.model or child.op,
                                     child.error, m))
                bandit.update(arm, False)
                log(f"[g{gen}#{pid}] {arm}/{child.op} {child.model}: invalid: {child.error[:100]}")
                return
            s = scorer.screen(child.source, "genome")
            if not s.ok:
                pid = db.add(Program(0, island, child.source, float("-inf"), m["parent_ids"],
                                     child.model or child.op, s.error, m))
                bandit.update(arm, False)
                log(f"[g{gen}#{pid}] {arm}: eval error: {s.error[:100]}")
                return
            pr = [scorer.screen(p.text, "genome") for p in ps]
            m.update(screen=s.score, parent_screen=[r.score for r in pr],
                     delta_screen=s.score - max(r.score for r in pr),
                     twin=any(s.fingerprint == r.fingerprint for r in pr), fingerprint=s.fingerprint,
                     fuel=sum(st["a_fuel_per_game"] for st in s.per_opponent.values()) / len(s.per_opponent))
            score = s.score
            if m["delta_screen"] > 0:
                c = scorer.confirm(child.source, "genome")
                pc = [scorer.confirm(p.text, "genome") for p in ps]
                m.update(confirm=c.score, parent_confirm=[r.score for r in pc],
                         delta_confirm=c.score - max(r.score for r in pc), per_opponent=c.per_opponent)
                m["beats_parent"] = m["delta_confirm"] > args.beat_margin
                score = c.score
            else:
                m["per_opponent"] = s.per_opponent
            pid = db.add(Program(0, island, child.source, score, m["parent_ids"], child.model or child.op, None, m))
            with rng_lock:
                bandit.update(arm, m.get("beats_parent", False))
            conf = f" confirm {m['delta_confirm']:+.3f}" if "confirm" in m else ""
            log(f"[g{gen}#{pid}] {arm}/{child.op} {child.model} isl {island}: screen {m['delta_screen']:+.3f}{conf}"
                f"{' GAIN' if m.get('beats_parent') else ''}{' twin' if m['twin'] else ''} "
                f"({child.log.get('lines_changed', '?')} lines) ${claude.spent:.2f}")

        promoted = None
        while not stop.is_set() and promoted is None:
            start = len(db.all)
            with ThreadPoolExecutor(args.workers) as ex:
                list(ex.map(one, range(args.round)))
            total = sum(1 for p in out.glob("g*/programs.jsonl") for _ in open(p))
            promoted = boundary(db, gen, state, scorer, scorer10, args, log, best_text, pool, fixed)
            evoreport.write(out, state, bandit, args.beat_margin)
            save_state()
            if total >= args.max_programs:
                stop.set()
            if len(db.all) == start:  # nothing new (budget exhausted mid-round)
                break
        if promoted:
            n = len(state["promoted"]) + 1
            path = out / "promoted" / f"gen{n}.genome"
            path.write_text(promoted.text)
            state["promoted"].append(str(path.resolve()))
            state["best"] = str(path.resolve())
            state["gen"] = gen + 1
            save_state()
            log(f"PROMOTED g{gen}#{promoted.id} -> {path.name}; generation {gen + 1} starts from it")
    log(f"done: spent ${claude.spent:.2f}")


def boundary(db, gen, state, scorer, scorer10, args, log, best_text, pool, fixed):
    """Validate the top candidates; re-score new improvements at fuel x10. Returns the promoted Program."""
    # fuel x10 on improvements not yet re-scored
    for p in db.all:
        key = f"g{gen}#{p.id}"
        if p.error or not p.metrics.get("beats_parent") or key in state["fuel10"]:
            continue
        c = scorer10.confirm(p.text, "genome")
        ps = [scorer10.confirm(db.all[i].text, "genome") for i in p.metrics["parent_ids"]]
        d = c.score - max(r.score for r in ps)
        state["fuel10"][key] = {"delta_confirm": p.metrics["delta_confirm"], "delta_fuel10": d,
                                "behavioural": d > args.beat_margin}
        log(f"fuel x10 {key}: {p.metrics['delta_confirm']:+.3f} -> {d:+.3f} "
            f"({'behavioural' if d > args.beat_margin else 'fuel-only'})")
    # candidates: best stored score among confirmed children, distinct behaviour, not yet validated
    seen, cands = set(), []
    for p in sorted((p for p in db.all if not p.error and "confirm" in p.metrics
                     and p.metrics.get("op") != "seed"), key=lambda p: -p.score):
        key = p.metrics.get("fingerprint") or p.text
        if p.text == best_text or key in seen or f"g{gen}#{p.id}" in state["validated"]:
            continue
        if p.score <= db.all[0].score:  # must at least confirm above the generation's seed
            break
        seen.add(key)
        cands.append(p)
        if len(cands) == args.candidates:
            break
    if not cands:
        state["boundaries"].append({"gen": gen, "programs": len(db.all), "t": time.time(), "promoted": None})
        return None
    best_spec = scorer._spec(best_text, "genome")
    members = [o.rpartition("@")[0] if "@" in o and o.rsplit("@", 1)[1].replace(".", "").isdigit() else o
               for o in fixed] + state["promoted"][:-1][-args.keep_promoted:]

    def rate(a_spec, b, seeds, games):
        w = n = 0
        for sd in seeds:
            st = scorer.play(a_spec, scorer._spec(b) if not b.startswith("genome:") else b, sd, games,
                             threads=args.threads)
            w, n = w + st["a_wins"], n + st["games"]
        return w, n

    bars = state.setdefault("bars", {})  # the best's own validation results, computed once per best
    for m in members:
        k = f"{state['best']}|{m}"
        if k not in bars:
            bars[k] = rate(best_spec, m, FRESH_SEEDS, args.val_games)
    bar = {m: bars[f"{state['best']}|{m}"] for m in members}
    winner = None
    for p in cands:
        state["validated"].append(f"g{gen}#{p.id}")
        spec = scorer._spec(p.text, "genome")
        w, n = rate(spec, best_spec, FRESH_SEEDS, args.val_h2h)
        if 0.5 <= w / n < 0.5 + args.z * 0.5 / n ** 0.5:
            w2, n2 = rate(spec, best_spec, MORE_SEEDS, args.val_h2h)
            w, n = w + w2, n + n2
        h2h = w / n
        clear = h2h >= 0.5 + args.z * 0.5 / n ** 0.5
        drops = {}
        if clear:
            for m in members:
                wm, nm = rate(spec, m, FRESH_SEEDS, args.val_games)
                drops[Path(m).stem] = round(wm / nm - bar[m][0] / bar[m][1], 3)
        worst = min(drops.values(), default=0.0)
        ok = clear and worst >= -args.regress
        log(f"validate g{gen}#{p.id} ({p.metrics.get('arm')}): h2h {h2h:.3f} over {n} "
            f"({'clear' if clear else 'not clear'}); pool deltas {drops} -> {'PASS' if ok else 'fail'}")
        if ok and (winner is None or h2h > winner[1]):
            winner = (p, h2h, n, drops)
    state["boundaries"].append({"gen": gen, "programs": len(db.all), "t": time.time(),
                                "promoted": f"g{gen}#{winner[0].id}" if winner else None,
                                "h2h": winner[1] if winner else None, "drops": winner[3] if winner else None})
    return winner[0] if winner else None


if __name__ == "__main__":
    main()
