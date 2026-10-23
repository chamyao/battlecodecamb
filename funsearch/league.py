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
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

from .evaluate import ROOT, evaluate

FRESH_SEEDS = (5_000_011, 6_000_011)  # validation only; the runs use eval seeds 0 and 1


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


def win_rates(text, opponents, games, threads):
    """Win rate per opponent over the fresh seeds (games per opponent per seed)."""
    totals = {}
    for seed in FRESH_SEEDS:
        r = evaluate(text, opponents=tuple(opponents), games=games, threads=threads, seed=seed)
        if not r.ok:
            return None
        for name, m in r.per_opponent.items():
            w, n = totals.get(name, (0.0, 0))
            totals[name] = (w + m["a_wins"], n + m["games"])
    return {name: w / n for name, (w, n) in totals.items()}


def commit(path, message):
    """Commit and push one file; a lock keeps parallel leagues from racing on the git index."""
    with open(ROOT / "runs" / ".git.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run(["git", "add", str(path)], cwd=ROOT)
        subprocess.run(["git", "commit", "-qm", message + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                        "Claude-Session: https://claude.ai/code/session_019XKtAwh5HoipabJVsbdMKj", "--", str(path)],
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
    ap.add_argument("--no-commit", action="store_true", help="don't git-commit promoted policies (tests)")
    ap.add_argument("--prefix", default="fs-", help="promoted policies are policies/<prefix><n>.policy")
    ap.add_argument("--line", default="", help="line tag written into promoted policies' headers")
    args, run_args = ap.parse_known_args()  # anything else goes to funsearch.run

    members = args.members.split(",")
    state_path = ROOT / "runs" / f"{args.name}.json"
    logfile = ROOT / "runs" / f"{args.name}.log"
    state = json.loads(state_path.read_text()) if state_path.exists() else {"gen": 1, "members": members}
    members = state["members"]

    while state["gen"] <= args.max_generations:
        fixed = [f for f in args.fixed.split(",") if f]
        best, older = members[0], members[1:] + [f for f in fixed if f not in members]
        run = f"{args.name}-g{state['gen']}"
        left = args.budget - spent(args.name)
        if left <= 0.01:
            log(f"budget spent (${spent(args.name):.2f})", logfile)
            break
        opponents = [f"builtin:starter@{args.starter_weight}", f"{best}@{args.best_weight}", *older]
        log(f"{run}: +{args.round} programs, best {best}, league {older}, ${left:.2f} left", logfile)
        subprocess.run([sys.executable, "-m", "funsearch.run", "--run", run, "--budget", f"{left:.2f}",
                        "--max-programs", str(args.round), "--seed-policy", best,
                        "--opponents", ",".join(opponents), *run_args],
                       cwd=ROOT, stdout=open(ROOT / "runs" / f"{run}.log", "a"), stderr=subprocess.STDOUT)
        if (ROOT / "runs" / run / "STOP").exists():
            log("STOP file present: pausing the league", logfile)
            break

        # validate: the current best's own rates against the older members are the bar
        league = [best, *older]
        bar = win_rates(Path(best).read_text(), older, args.val_games, args.threads) if older else {}
        promoted = None
        for p in top_distinct(run, 3):
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
                    promoted = (p, h2h, rates)
        if promoted is None:
            log(f"  no promotion; {run} continues", logfile)
            continue

        p, h2h, rates = promoted
        taken = [f.stem[len(args.prefix):] for f in (ROOT / "policies").glob(f"{args.prefix}*.policy")]
        n = 1 + max([int(t) for t in taken if t.isdigit()], default=0)
        name = f"{args.prefix}{n}"
        out = ROOT / "policies" / f"{name}.policy"
        tag = f" [{args.line} line]" if args.line else ""
        header = (f"# {name}{tag}: league {run} #{p['id']}; beat {Path(best).stem} {h2h:.1%} head to head on "
                  f"{2 * args.val_games} fresh games.\n")
        out.write_text(header + p["text"])
        summary = ", ".join(f"{k} {v:.1%}" for k, v in rates.items())
        log(f"  PROMOTED {out.name}: {summary}", logfile)
        if not args.no_commit:
            commit(out, f"policies/{name}: league promotion{tag} ({run} #{p['id']})\n\n"
                        f"Fresh-seed win rates ({2 * args.val_games} games each): {summary}")
        members = [str(out.relative_to(ROOT)), *(m for m in league if m not in fixed)][: 1 + args.keep]
        state = {"gen": state["gen"] + 1, "members": members}
        state_path.write_text(json.dumps(state))


if __name__ == "__main__":
    main()
