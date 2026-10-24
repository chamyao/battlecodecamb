"""Self-play league: FunSearch generations against our own best policies.

    python3 -m funsearch.league --name league --budget 15

The league starts as --members (current best first). Each generation is a FunSearch run
(runs/<name>-g<k>) seeded with the current best and scored against starter (sanity floor, low
weight), the current best (heavy) and the older members. Every --round programs the run's top 3
distinct programs are validated on fresh seeds; a candidate is promoted when it beats the current
best head to head by --margin and does not regress against any older member. A promoted policy
is written to policies/fs-<n>.policy, joins the league as the new best, and the next generation
starts from it. Without a promotion the generation continues. Spend is summed over all
generations and capped at --budget.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from .evaluate import EVAL_BIN, ROOT, evaluate

FRESH_SEEDS = (5_000_011, 6_000_011)  # validation only; the runs use eval seeds 0 and 1
TUNE_SEED, HOLDOUT_SEED = 3_000_011, 4_000_011  # tuning stage: hill-climb games / independent check


def log(msg, path):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(path, "a") as f:
        f.write(line + "\n")


def spent(name):
    total = 0.0
    for path in (ROOT / "runs").glob(f"{name}-g*/programs.jsonl"):
        for line in open(path):
            total += json.loads(line)["metrics"].get("cost", 0.0)
    return total


def tune_candidate(p, opponents, args, logfile, run):
    """Rough tuning stage between the generation and validation: a few hill-climb steps over the candidate's
    named constants on one small fixed set of games (the run's weighted opponents), kept only if the tuned
    text also beats the untuned one on a small independent holdout set. Deliberately cheap (a few percent of
    validation time) and model-free (no API spend); the fresh-seed validation stays the real gate."""
    from .tune import named_constants, tune_named

    if not named_constants(p["text"]):
        return p

    def scorer(seed):
        def score(text):
            r = evaluate(text, opponents=tuple(opponents), games=args.tune_games, threads=args.threads, seed=seed)
            return r.score if r.ok else -1.0
        return score

    tuned, s, s0 = tune_named(p["text"], scorer(TUNE_SEED), steps=args.tune_steps, seed=p["id"], log=lambda m: None)
    if tuned == p["text"]:
        log(f"  tune #{p['id']}: no better constants ({args.tune_steps} steps, {s0:.3f})", logfile)
        return p
    hold = scorer(HOLDOUT_SEED)
    new, old = hold(tuned), hold(p["text"])
    before, after = named_constants(p["text"]), named_constants(tuned)
    changed = ", ".join(f"{k} {before[k]:g}->{after[k]:g}" for k in after if after[k] != before[k])
    keep = new > old
    log(f"  tune #{p['id']}: {changed}; tune games {s0:.3f}->{s:.3f}, holdout {old:.3f}->{new:.3f} "
        f"({'kept' if keep else 'dropped'})", logfile)
    with open(ROOT / "runs" / run / "tuned.jsonl", "a") as f:
        f.write(json.dumps({"id": p["id"], "kept": keep, "changed": changed, "tune": [s0, s],
                            "holdout": [old, new], "text": tuned}) + "\n")
    return {**p, "text": tuned, "tuned": True} if keep else p


def top_distinct(run, k):
    progs = [json.loads(line) for line in open(ROOT / "runs" / run / "programs.jsonl")]
    out, seen = [], set()
    for p in sorted((p for p in progs if p["error"] is None and p["model"] != "seed"),
                    key=lambda p: -p["score"]):
        key = p["metrics"].get("screen_fp") or p["text"]
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
        if len(out) == k:
            break
    return out


CACHE = ROOT / "runs" / "validation_cache.jsonl"  # survives restarts (ported from funsearch/runs b441fe6)


def _cached_eval(text, opp, games, threads, seed):
    """(wins, games) of text vs one opponent, cached on disk by content: validation is long, and a
    restart in the middle of it should only lose the evaluation in flight."""
    import hashlib
    key = hashlib.sha256("\0".join([text, opp, Path(ROOT / opp).read_text() if opp.endswith(".policy") else "",
                                    str(games), str(seed), str(EVAL_BIN.stat().st_mtime)]).encode()).hexdigest()
    if CACHE.exists():
        for line in open(CACHE):
            row = json.loads(line)
            if row["key"] == key:
                return row["wins"], row["games"]
    r = evaluate(text, opponents=(opp,), games=games, threads=threads, seed=seed)
    if not r.ok:
        return None
    m = next(iter(r.per_opponent.values()))
    with open(CACHE, "a") as f:
        f.write(json.dumps({"key": key, "wins": m["a_wins"], "games": m["games"]}) + "\n")
    return m["a_wins"], m["games"]


def win_rates(text, opponents, games, threads):
    """Win rate per opponent over the fresh seeds (games per opponent per seed). Evaluating one
    opponent at a time plays the same games as one batched call (same seed, same map prefix)."""
    totals = {}
    for seed in FRESH_SEEDS:
        for opp in opponents:
            res = _cached_eval(text, opp, games, threads, seed)
            if res is None:
                return None
            name = Path(opp).stem if opp.endswith(".policy") else opp
            w, n = totals.get(name, (0.0, 0))
            totals[name] = (w + res[0], n + res[1])
    return {name: w / n for name, (w, n) in totals.items()}


def listarg(spec):
    """Comma-separated paths, or @file (one per line or comma-separated), re-read on every call so a
    running league picks up a change at its next generation."""
    if spec.startswith("@"):
        spec = (ROOT / spec[1:]).read_text().replace("\n", ",")
    return [x.strip() for x in spec.split(",") if x.strip() and not x.strip().startswith("#")]


def cambc_check(text, opponent, threads):
    """Win rate vs `opponent` over every map x both sides with deploy-bot seeding (--bot-seeds), which
    reproduces real cambc games exactly: the final check before a promotion is trusted."""
    from .evaluate import EVAL_BIN, MAPS, _compiled_opponent
    from policygen.compile import to_prefix
    from policygen.text import parse
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
        f.write(to_prefix(parse(text)))
    try:
        out = subprocess.run([str(EVAL_BIN), "--a", f.name, "--b", _compiled_opponent(opponent), "--games",
                              str(2 * len(MAPS)), "--threads", str(threads), "--bot-seeds", *MAPS],
                             capture_output=True, text=True, timeout=3600)
        return json.loads(out.stdout)["win_rate"]
    finally:
        Path(f.name).unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="league")
    ap.add_argument("--budget", type=float, required=True, help="USD across all generations")
    ap.add_argument("--members", default="policies/fs-1.policy,policies/v2.policy",
                    help="league, current best first")
    ap.add_argument("--best-weight", type=float, default=3.0)
    ap.add_argument("--starter-weight", type=float, default=0.25)
    ap.add_argument("--round", type=int, default=150, help="programs between validations")
    ap.add_argument("--margin", type=float, default=0.05, help="head-to-head win rate over 50%% to promote")
    ap.add_argument("--regress", type=float, default=0.03, help="allowed drop vs an older member")
    ap.add_argument("--val-games", type=int, default=400, help="per opponent per fresh seed")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--max-generations", type=int, default=20)
    ap.add_argument("--keep", type=int, default=3, help="older members kept besides the best")
    ap.add_argument("--fixed", default="", help="opponents always in the league (e.g. a style the bests "
                                                "lack, like altar locking); never dropped or promoted")
    ap.add_argument("--cambc-min", type=float, default=0.55,
                    help="also required: win rate vs the best over all maps x 2 sides with --bot-seeds")
    ap.add_argument("--cambc-also", default="", help="also log the cambc-exact win rate vs these policies "
                                                     "(e.g. the ladder version; informational)")
    ap.add_argument("--policy-prefix", default="fs-", help="promoted policies are policies/<prefix><n>.policy")
    ap.add_argument("--line", default="", help="line name written into promoted headers with the lineage "
                                              "(e.g. pure: programs descend only from FunSearch outputs)")
    ap.add_argument("--session", default="https://claude.ai/code/session_019XKtAwh5HoipabJVsbdMKj",
                    help="Claude-Session trailer for promotion commits")
    ap.add_argument("--tune-steps", type=int, default=0,
                    help="rough tuning stage before validation: hill-climb steps over the top candidates' named "
                         "constants (0 = off; 6 is the intended rough setting)")
    ap.add_argument("--tune-games", type=int, default=8, help="games per opponent per tuning evaluation (kept tiny)")
    ap.add_argument("--tune-k", type=int, default=3, help="how many of the top candidates get the tuning stage")
    ap.add_argument("--no-commit", action="store_true", help="don't git-commit promoted policies (tests)")
    args, run_args = ap.parse_known_args()  # anything else goes to funsearch.run

    members = args.members.split(",")
    state_path = ROOT / "runs" / f"{args.name}.json"
    logfile = ROOT / "runs" / f"{args.name}.log"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"gen": 1, "members": members}
    members = state["members"]

    while state["gen"] <= args.max_generations:
        # the fixed opponents are frozen per generation (in the state), so a changed --fixed @file
        # takes effect at the next generation and a resumed one keeps the opponents it started with
        if "fixed" not in state:
            state["fixed"] = listarg(args.fixed)
            state_path.write_text(json.dumps(state))
        fixed = state["fixed"]
        best, older = members[0], members[1:] + [f for f in fixed if f not in members]
        run = f"{args.name}-g{state['gen']}"
        left = args.budget - spent(args.name)
        if left <= 0.01:
            log(f"budget spent (${spent(args.name):.2f})", logfile)
            break
        opponents = [f"builtin:starter@{args.starter_weight}", f"{best}@{args.best_weight}", *older]
        # validate when the generation's database reaches its target size (seed + rounds), so a
        # resume after a restart doesn't start the round count again
        if "target" not in state:
            state["target"] = 1 + args.round
            state_path.write_text(json.dumps(state))
        db_file = ROOT / "runs" / run / "programs.jsonl"
        todo = max(0, state["target"] - (sum(1 for _ in open(db_file)) if db_file.exists() else 0))
        log(f"{run}: +{todo} programs (to {state['target']}), best {best}, league {older}, ${left:.2f} left", logfile)
        subprocess.run([sys.executable, "-m", "funsearch.run", "--run", run, "--budget", f"{left:.2f}",
                        "--max-programs", str(todo), "--seed-policy", best,
                        "--opponents", ",".join(opponents), *run_args],
                       cwd=ROOT, stdout=open(ROOT / "runs" / f"{run}.log", "a"), stderr=subprocess.STDOUT)
        if (ROOT / "runs" / run / "STOP").exists():
            log("STOP file present: pausing the league", logfile)
            break

        # validate: the current best's own rates against the older members are the bar
        league = [best, *older]
        bar = win_rates(Path(best).read_text(), older, args.val_games, args.threads) if older else {}
        promoted = None
        cands = top_distinct(run, 3)
        if args.tune_steps:
            cands = [tune_candidate(p, opponents, args, logfile, run) if i < args.tune_k else p
                     for i, p in enumerate(cands)]
        for p in cands:
            rates = win_rates(p["text"], ["builtin:starter", *league], args.val_games, args.threads)
            if rates is None:
                continue
            h2h = rates[Path(best).stem]
            worst = min((rates[Path(o).stem] - bar[Path(o).stem] for o in older), default=0.0)
            log(f"  #{p['id']} (run score {p['score']:.3f}): " + ", ".join(f"{k} {v:.3f}" for k, v in rates.items())
                + f" | h2h {h2h:.3f}, worst change vs older {worst:+.3f}", logfile)
            if h2h >= 0.5 + args.margin and worst >= -args.regress and (promoted is None or h2h > promoted[1]):
                exact = cambc_check(p["text"], best, args.threads)
                log(f"    cambc-exact vs {Path(best).stem} (all maps x 2 sides): {exact:.3f}", logfile)
                if exact >= args.cambc_min:
                    rates = {**rates, f"cambc-exact vs {Path(best).stem}": exact}
                    for o in listarg(args.cambc_also):
                        rates[f"cambc-exact vs {Path(o).stem}"] = cambc_check(p["text"], o, args.threads)
                        log(f"    cambc-exact vs {Path(o).stem}: {rates[f'cambc-exact vs {Path(o).stem}']:.3f}", logfile)
                    promoted = (p, h2h, rates)
        if promoted is None:
            log(f"  no promotion; {run} continues", logfile)
            state["target"] += args.round
            state_path.write_text(json.dumps(state))
            continue

        p, h2h, rates = promoted
        pre = args.policy_prefix
        n = 1 + max((int(f.stem[len(pre):]) for f in (ROOT / "policies").glob(f"{pre}*.policy")
                     if f.stem[len(pre):].isdigit()), default=0)
        out = ROOT / "policies" / f"{pre}{n}.policy"
        tag = " + tune" if p.get("tuned") else ""
        header = (f"# {pre}{n}: league {run} #{p['id']}{tag}; beat {Path(best).stem} {h2h:.1%} head to head on "
                  f"{2 * args.val_games} fresh games.\n")
        if args.line:
            # lineage: the parent's chain (from its header) plus this generation
            prev = next((l.split(":", 1)[1].strip() for l in Path(best).read_text().splitlines()
                         if l.startswith("# lineage:")), Path(best).stem)
            header += f"# line: {args.line}\n# lineage: {prev} -> {run} #{p['id']}{tag} = {pre}{n}\n"
        out.write_text(header + p["text"])
        summary = ", ".join(f"{k} {v:.1%}" for k, v in rates.items())
        log(f"  PROMOTED {out.name}: {summary}", logfile)
        if not args.no_commit:
            subprocess.run(["git", "add", str(out)], cwd=ROOT)
            subprocess.run(["git", "commit", "-qm", f"policies/{pre}{n}: league promotion ({run} #{p['id']})\n\n"
                            f"Fresh-seed win rates ({2 * args.val_games} games each): {summary}\n\n"
                            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                            f"Claude-Session: {args.session}"], cwd=ROOT)
            subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=ROOT)
        members = [str(out.relative_to(ROOT)), *(m for m in league if m not in fixed)][: 1 + args.keep]
        state = {"gen": state["gen"] + 1, "members": members}
        state_path.write_text(json.dumps(state))


if __name__ == "__main__":
    main()
