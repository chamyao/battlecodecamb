"""Smallest fix for the starvation/hooks collapse: cash in a moderate bag (>= 10) when hurt or threatened,
keep bag >= 25 otherwise (carried gems are destroyed by camp deaths and taken by champion kills)."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play

OLD = "let bag_ready = gems() >= 25 or round_number() > 1500 or health() < 0.3 * max_health()\n"
FIXES = {
    "hurt10-0.5": "(gems() >= 10 and health() < 0.5 * max_health())",
    "hurt10-0.6": "(gems() >= 10 and health() < 0.6 * max_health())",
    "threat10-r6": "(gems() >= 10 and enemies_within(6) > 0)",
    "hurt10-0.5+threat": "(gems() >= 10 and (health() < 0.5 * max_health() or enemies_within(6) > 0))",
    "danger10": "(gems() >= 10 and in_danger())",
}


def fix(base, extra):
    assert base.count(OLD) == 1
    return base.replace(OLD, "# bank a moderate bag when hurt or threatened (tune line: 01starvation/01hooks)\n" + OLD.rstrip("\n") + f" or {extra}\n")


if __name__ == "__main__":
    base = open("policies/tune-3.policy").read()
    bpol = compile_text(base)
    opps = {"opp-icecream": compile_file("policies/opp-icecream.policy"), "v7zg-cast": compile_file("policies/v7zg-cast.policy")}
    log = open("runs/tune/bankfix.log", "a")
    for name, extra in FIXES.items():
        pol = compile_text(fix(base, extra))
        r = {"all400": h2h(pol, bpol, 400, 9013)["win_rate"], "cambc80": h2h(pol, bpol, 80, 1, bot_seeds=True)["win_rate"]}
        for m in ("01starvation", "01hooks"):
            for on, op in opps.items():
                s = play(pol, op, f"maps/{m}.map26a", 40, 21)
                r[f"{m}/{on}"] = [s["wins"], s["gems"], s["gems_lost"]]
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
