"""Targeted fix for 01starvation: before walking into a dangerous camp group with a bag, tribute first.
After the camp goal is chosen: if gems() >= 10 and group_threat(goal) >= T, tribute at an adjacent altar or walk
to the nearest safe altar tile. Elk are 60 each, wolves 20 (starvation's elk x4 group is 240).
Scored like bank_fix.py, plus the metab stand-in."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play

OLD = "let goal = closest(goals)\n"


def threat_bank(base, t):
    new = (OLD + f"# bank before a dangerous group (tune line, 01starvation): elk 60, wolf 20 per camp\n"
           f"if exists(goal) and gems() >= 10 and group_threat(goal) >= {t}:\n"
           f"    let bank_altar = first( filter( altars(), within(1, position()) ) )\n"
           f"    if exists(bank_altar):\n"
           f"        tribute(bank_altar)\n"
           f"        end_turn()\n"
           f"    move_towards( closest(safe_altar_ring) )\n"
           f"    end_turn()\n")
    assert base.count(OLD) == 1
    return base.replace(OLD, new)


if __name__ == "__main__":
    base = open("policies/tune-3.policy").read()
    bpol = compile_text(base)
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
    log = open("runs/tune/threatbank.log", "a")
    for name, text in [("tune-3", base)] + [(f"T{t}", threat_bank(base, t)) for t in (60, 120, 180, 240)]:
        pol = compile_text(text)
        r = {} if name == "tune-3" else {"all400": h2h(pol, bpol, 400, 9017)["win_rate"],
                                         "cambc80": h2h(pol, bpol, 80, 1, bot_seeds=True)["win_rate"]}
        for m in ("01starvation", "01hooks"):
            for on, op in opps.items():
                s = play(pol, op, f"maps/{m}.map26a", 40, 21)
                r[f"{m}/{on}"] = [s["wins"], s["gems"], s["gems_lost"]]
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
