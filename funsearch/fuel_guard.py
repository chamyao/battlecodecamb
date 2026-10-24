"""tune-3 candidates: tune-2 with a policy-level fuel guard on optional dashes, threshold F tuned.

Scope "all": every dash_to call (retreat and camp-goal dashes). Scope "goal": only the camp-goal dash.
Reports suspensions per game on 01big-world (the policy as A and as B) and the win rate."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

DEF_OLD = "def dash_to(slot, t):\n    if ability_ready(slot):\n"
GOAL_OLD = "if exists(goal) and distance(position(), goal) > 4:\n"


def guard(base, f, scope):
    if scope == "all":
        assert base.count(DEF_OLD) == 1
        return base.replace(DEF_OLD, f"def dash_to(slot, t):\n    # fuel guard (tune line): a dash plus the move after it can overrun a near-cap turn\n"
                                     f"    if ability_ready(slot) and fuel_remaining() > {f}:\n")
    assert base.count(GOAL_OLD) == 1
    return base.replace(GOAL_OLD, f"# fuel guard (tune line): skip the optional dash on a near-cap turn\n"
                                  f"if exists(goal) and distance(position(), goal) > 4 and fuel_remaining() > {f}:\n")


def big_world(pol, opp, games=200, seed=31):
    # per-game seeds (no --bot-seeds): with --bot-seeds every game on one map is the same pair of games
    out = subprocess.run([str(EVAL_BIN), "--a", pol, "--b", opp, "--games", str(games), "--threads", "4",
                          "--seed", str(seed), str(ROOT / "maps" / "01big-world.map26a")],
                         capture_output=True, text=True, timeout=7200)
    return json.loads(out.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    base = open("policies/tune-2.policy").read()
    bpol = compile_text(base)
    log = open("runs/tune/fuel-guard2.log", "a")
    cands = {"tune-2": base}
    for scope in ("all", "goal"):
        for f in (45000, 50000, 55000, 60000, 70000):
            cands[f"{scope}-{f}"] = guard(base, f, scope)
    for name, text in cands.items():
        pol = compile_text(text)
        bw = big_world(pol, bpol)
        chk = h2h(pol, bpol, 80, 1, bot_seeds=True)
        allm = h2h(pol, bpol, 400, 9007)
        r = {"bigworld_susp": bw["a_suspensions"], "bigworld_wr": bw["win_rate"], "bigworld_fuel": bw["a_fuel_per_game"],
             "cambc_check": chk["win_rate"], "check_susp": chk["a_suspensions"],
             "all400_wr": allm["win_rate"], "all400_susp": allm["a_suspensions"]}
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
