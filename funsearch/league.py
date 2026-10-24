"""Self-play league: FunSearch generations against our own best policies.

    python3 -m funsearch.league --name league --budget 15

The league starts as --members (current best first). Each generation is a FunSearch run
(runs/<name>-g<k>) seeded with the current best and scored against starter (sanity floor, low
weight), the current best (heavy) and the older members. Every --round programs (a round
boundary) the run's top 3 distinct programs are validated on fresh seeds. A candidate is promoted
when its head-to-head win rate against the best is clearly above 50% (lower confidence bound,
--z standard errors; borderline results get a second batch of fresh games) and it drops no more
than --regress against any older member. A promoted policy is written to
policies/<prefix><n>.policy, joins the league as the new best, and the next generation starts
from it. Without a promotion the generation continues. Spend is capped at --budget.

Outside changes enter only at round boundaries, so the search is not restarted mid-round:
- runs/<name>.challengers: policy paths, one per line (e.g. a new hand-made version). At the next
  boundary each is judged by the same rule as the run's own candidates; a winner becomes the best.
  Every challenger is also injected into the run as a parent and joins the fixed opponents from
  the next generation on.
- runs/<name>.hold: the league waits at the next boundary until the file is removed (merge or
  rebuild the simulator meanwhile).
The cambc-exact check (all maps x 2 sides, --bot-seeds) is logged for each promotion; >= --cambc-min
(vs --cambc-ref, the live ladder bot, when given; else vs the best) marks it ladder-ready.
"""
import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

from .evaluate import EVAL_BIN, ROOT, evaluate

FRESH_SEEDS = (5_000_011, 6_000_011)  # validation only; the runs use eval seeds 0 and 1
MORE_SEEDS = (7_000_011, 8_000_011)  # second batch for borderline head-to-head results


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


def top_distinct(run, k):
    progs = [json.loads(line) for line in open(ROOT / "runs" / run / "programs.jsonl")]
    out, seen = [], set()
    for p in sorted((p for p in progs if p["error"] is None and p["model"] != "seed"
                     and not p["model"].startswith("inject")),
                    key=lambda p: -p["score"]):
        key = p["metrics"].get("screen_fp") or p["text"]
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
        if len(out) == k:
            break
    return out


CACHE = ROOT / "runs" / "validation_cache.jsonl"  # survives container restarts


def _cached_eval(text, opp, games, threads, seed):
    """(wins, games) of text vs one opponent, cached on disk by content: validation is long, and a
    container restart in the middle of it should only lose the evaluation in flight."""
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
        print(f"validation error vs {opp} (seed {seed}): {r.error}", flush=True)
        return None
    m = next(iter(r.per_opponent.values()))
    with open(CACHE, "a") as f:
        f.write(json.dumps({"key": key, "wins": m["a_wins"], "games": m["games"]}) + "\n")
    return m["a_wins"], m["games"]


def win_rates(text, opponents, games, threads, seeds=FRESH_SEEDS, counts=False):
    """Win rate per opponent over the fresh seeds (games per opponent per seed); with counts,
    (wins, games) pairs instead."""
    totals = {}
    for seed in seeds:
        for opp in opponents:
            res = _cached_eval(text, opp, games, threads, seed)
            if res is None:
                return None
            name = Path(opp).stem if opp.endswith(".policy") else opp
            w, n = totals.get(name, (0.0, 0))
            totals[name] = (w + res[0], n + res[1])
    return totals if counts else {name: w / n for name, (w, n) in totals.items()}


def clearly_better(text, best, first, games, threads, z):
    """Head to head vs best: (passes, win rate, games). Passes when the win rate's lower bound
    (z standard errors) is above 50%; a borderline first batch (>= 50%) gets a second one."""
    w, n = first
    if n and w / n < 0.5 + z * 0.5 / n ** 0.5 and w / n >= 0.5:
        more = win_rates(text, [best], games, threads, seeds=MORE_SEEDS, counts=True)
        if more:
            w2, n2 = more[Path(best).stem]
            w, n = w + w2, n + n2
    rate = w / n if n else 0.0
    return rate >= 0.5 + z * 0.5 / n ** 0.5, rate, n


def commit(path, message, session):
    """Commit and push one file; a lock keeps parallel leagues from racing on the git index."""
    with open(ROOT / "runs" / ".git.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run(["git", "add", str(path)], cwd=ROOT)
        subprocess.run(["git", "commit", "-qm", message + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                        f"Claude-Session: {session}", "--", str(path)],
                       cwd=ROOT)
        for attempt in range(4):
            if subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=ROOT).returncode == 0:
                break
            time.sleep(2 ** (attempt + 1))


def cambc_check(text, best, threads):
    """Win rate vs `best` over every map x both sides with deploy-bot seeding (--bot-seeds), which
    reproduces real cambc games exactly: the final check before a promotion is trusted."""
    from .evaluate import EVAL_BIN, MAPS, _compiled_opponent
    from policygen.compile import to_prefix
    from policygen.text import parse
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
        f.write(to_prefix(parse(text)))
    try:
        out = subprocess.run([str(EVAL_BIN), "--a", f.name, "--b", _compiled_opponent(best), "--games",
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
    ap.add_argument("--z", type=float, default=2.0,
                    help="promotion needs the head-to-head win rate this many standard errors above 50%%")
    ap.add_argument("--regress", type=float, default=0.03, help="allowed drop vs an older member")
    ap.add_argument("--val-games", type=int, default=400, help="per opponent per fresh seed")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--max-generations", type=int, default=20)
    ap.add_argument("--keep", type=int, default=3, help="older members kept besides the best")
    ap.add_argument("--fixed", default="", help="opponents always in the league (e.g. a style the bests "
                                                "lack, like altar locking); never dropped or promoted")
    ap.add_argument("--cambc-min", type=float, default=0.55,
                    help="cambc-exact win rate vs the best (all maps x 2 sides) that marks a promotion ladder-ready")
    ap.add_argument("--cambc-ref", default="",
                    help="live ladder bot: when set, ladder-ready means cambc-exact >= --cambc-min vs this policy "
                         "(the vs-best check is still logged)")
    ap.add_argument("--no-commit", action="store_true", help="don't git-commit promoted policies (tests)")
    ap.add_argument("--prefix", default="fs-", help="promoted policies are policies/<prefix><n>.policy")
    ap.add_argument("--line", default="", help="line tag written into promoted policies' headers")
    ap.add_argument("--session", default="https://claude.ai/code/session_019XKtAwh5HoipabJVsbdMKj",
                    help="Claude-Session trailer for promotion commits")
    args, run_args = ap.parse_known_args()  # anything else goes to funsearch.run

    members = args.members.split(",")
    state_path = ROOT / "runs" / f"{args.name}.json"
    logfile = ROOT / "runs" / f"{args.name}.log"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"gen": 1, "members": members}
    members = state["members"]

    while state["gen"] <= args.max_generations:
        fixed = [f for f in args.fixed.split(",") if f] + [f for f in state.get("fixed_extra", []) if f not in args.fixed]
        best, older = members[0], members[1:] + [f for f in fixed if f not in members]
        run = f"{args.name}-g{state['gen']}"
        left = args.budget - spent(args.name)
        if left <= 0.01:
            log(f"budget spent (${spent(args.name):.2f})", logfile)
            break
        opponents = [f"builtin:starter@{args.starter_weight}", f"{best}@{args.best_weight}", *older]
        # round boundaries are multiples of --round programs in the run, so a restart (container
        # reboot) resumes the current round instead of starting a new one
        db_file = ROOT / "runs" / run / "programs.jsonl"
        done = max(0, sum(1 for _ in open(db_file)) - 4) if db_file.exists() else 0
        todo = args.round - done % args.round
        if done and done % args.round == 0 and state.get("validated", {}).get(run, 0) < done:
            todo = 0  # restarted exactly at a boundary that was never validated: validate it now
        log(f"{run}: +{todo} programs to the next boundary ({done} so far), best {best}, league {older}, "
            f"${left:.2f} left", logfile)
        if todo:
            subprocess.run([sys.executable, "-m", "funsearch.run", "--run", run, "--budget", f"{left:.2f}",
                            "--max-programs", str(todo), "--seed-policy", best,
                            "--opponents", ",".join(opponents),
                            *(["--inject", ",".join(state["inject"])] if state.get("inject") else []), *run_args],
                           cwd=ROOT, stdout=open(ROOT / "runs" / f"{run}.log", "a"), stderr=subprocess.STDOUT)
        if (ROOT / "runs" / run / "STOP").exists():
            log("STOP file present: pausing the league", logfile)
            break

        hold = ROOT / "runs" / f"{args.name}.hold"
        if hold.exists():
            log(f"hold file present: waiting at the round boundary (remove {hold.name} to go on)", logfile)
            while hold.exists():
                time.sleep(30)
            log("hold released", logfile)

        # candidates: the run's top programs plus queued challengers, judged by the same rule
        cfile = ROOT / "runs" / f"{args.name}.challengers"
        queued = [c.strip() for c in cfile.read_text().splitlines() if c.strip()] if cfile.exists() else []
        queued = [c for c in queued if c not in state.get("challengers", []) and c != best]
        # challengers taken from the file but not yet judged (a restart during validation)
        queued = list(dict.fromkeys(state.get("pending", []) + queued))
        missing = [c for c in queued if not (ROOT / c).exists()]
        if missing:  # not merged yet: keep them queued for the next boundary
            log(f"  challengers not found yet, kept queued: {missing}", logfile)
            queued = [c for c in queued if c not in missing]
        if queued or missing:
            cfile.write_text("".join(f"{c}\n" for c in missing))
            state["challengers"] = list(dict.fromkeys(state.get("challengers", []) + queued))
            state["pending"] = queued
            state_path.write_text(json.dumps(state))
            log(f"  challengers: {queued}", logfile)
        tried = set(state.get("tried", []))  # candidates already judged against this best
        candidates = [(f"#{p['id']}", p["text"], p) for p in top_distinct(run, 3)
                      if (p["metrics"].get("screen_fp") or p["text"]) not in tried]
        candidates += [(c, Path(ROOT / c).read_text(), None) for c in queued]

        league = [best, *older]
        bar = win_rates(Path(best).read_text(), older, args.val_games, args.threads) if older else {}
        promoted = None
        for label, text, p in candidates:
            counts = win_rates(text, ["builtin:starter", *league], args.val_games, args.threads, counts=True)
            if counts is None:
                log(f"  {label}: skipped, evaluation failed (see {args.name}.out)", logfile)
                continue
            rates = {k: w / n for k, (w, n) in counts.items()}
            worst = min((rates[Path(o).stem] - bar[Path(o).stem] for o in older if Path(o).stem in rates),
                        default=0.0)
            ok, h2h, n = clearly_better(text, best, counts[Path(best).stem], args.val_games, args.threads, args.z)
            log(f"  {label}: " + ", ".join(f"{k} {v:.3f}" for k, v in rates.items())
                + f" | h2h {h2h:.3f} over {n} games ({'clear' if ok else 'not clear'}), "
                  f"worst change vs older {worst:+.3f}", logfile)
            if p is not None:
                tried.add(p["metrics"].get("screen_fp") or p["text"])
            if ok and worst >= -args.regress and (promoted is None or h2h > promoted[2]):
                promoted = (label, text, h2h, n, rates, p)
        state["tried"] = sorted(tried)
        state["pending"] = []
        db_done = max(0, sum(1 for _ in open(db_file)) - 4) if db_file.exists() else 0
        state.setdefault("validated", {})[run] = db_done
        state_path.write_text(json.dumps(state))
        if queued:
            # challengers become parents of this run and fixed opponents from the next generation
            state.setdefault("inject", []).extend(queued)
            state_path.write_text(json.dumps(state))
        if promoted is None:
            log(f"  no promotion; {run} continues", logfile)
            continue

        label, text, h2h, n, rates, p = promoted
        exact = cambc_check(text, best, args.threads)
        rates = {**rates, f"cambc-exact vs {Path(best).stem}": exact}
        ref = args.cambc_ref if args.cambc_ref and args.cambc_ref != best else ""
        if ref:
            log(f"    cambc-exact vs {Path(best).stem} (all maps x 2 sides): {exact:.3f}", logfile)
            exact = cambc_check(text, ref, args.threads)
            rates[f"cambc-exact vs {Path(ref).stem}"] = exact
        ready = exact >= args.cambc_min
        log(f"    cambc-exact vs {Path(ref or best).stem} (all maps x 2 sides): {exact:.3f}"
            + (" -> ladder-ready" if ready else ""), logfile)
        summary = ", ".join(f"{k} {v:.1%}" for k, v in rates.items())
        if p is None:  # a challenger won: it becomes the best as it is
            out = ROOT / label
            log(f"  PROMOTED challenger {label}: {summary}", logfile)
        else:
            taken = [f.stem[len(args.prefix):] for f in (ROOT / "policies").glob(f"{args.prefix}*.policy")]
            k = 1 + max([int(t) for t in taken if t.isdigit()], default=0)
            name = f"{args.prefix}{k}"
            out = ROOT / "policies" / f"{name}.policy"
            tag = f" [{args.line} line]" if args.line else ""
            header = (f"# {name}{tag}: league {run} {label}; beat {Path(best).stem} {h2h:.1%} head to head on "
                      f"{n} fresh games; cambc-exact vs {Path(ref or best).stem} {exact:.3f}"
                      f"{' (ladder-ready)' if ready else ''}.\n"
                      + (f"# line: {args.line}\n" if args.line else ""))
            out.write_text(header + text)
            log(f"  PROMOTED {out.name}: {summary}", logfile)
            if not args.no_commit:
                commit(out, f"policies/{name}: league promotion{tag} ({run} {label})\n\n"
                            f"Fresh-seed win rates ({2 * args.val_games} games each; head to head over {n}): {summary}", args.session)
        members = [str(out.relative_to(ROOT)), *(m for m in league if m not in fixed)][: 1 + args.keep]
        extra = [c for c in dict.fromkeys(state.get("fixed_extra", []) + state.get("inject", [])) if c not in members]
        state = {"gen": state["gen"] + 1, "members": members, "fixed_extra": extra,
                 "challengers": state.get("challengers", [])}
        state_path.write_text(json.dumps(state))


if __name__ == "__main__":
    main()
