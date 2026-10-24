"""Refine the 00lost-world fix (monoreach.py): damage wakes a camp's whole group (GameRules), so the gems in a
monolith's group are the danger, not every camp within reach. reach5 failed the map-fix bar (lost 00contest and
01corridors / 01shortcut on both sides in cambc80: gold or gems near a monolith but not in its group). Variants on
tune-5: goals minus the monolith groups (mgroup); mgroup + no stray monolith attacks outside the fallback (mgroup+na).
Per map (20 games a side vs v7zg-cast and opp-metab) on lost-world, contest, corridors, shortcut; all-map 400 seed 9391."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.monoreach import GOALS, reach

CAMP = "let camp = first( filter( camps, in_attack_range() ) )\nif exists(camp):\n"


def mgroup(t):
    assert t.count(GOALS) == 1
    return t.replace(GOALS, "let goals = minus( minus( minus( minus( camp_spawns, respawning_visible_spawns() ), monolith_tiles() ), golem_tiles() ), group_tiles( monolith_tiles() ) )\n")


def noattack(t):
    # the weakest camp in range is a monolith (20,000 hp) only when nothing else is: skip it unless in the fallback
    assert t.count(CAMP) == 1
    return t.replace(CAMP, "let camp = weakest( filter( camps, in_attack_range() ) )\n"
                     "if exists(camp) and ( not contains( monolith_tiles(), unit_position(camp) ) or team_score(ally()) == 0 ):\n")


if __name__ == "__main__":
    base = open("policies/tune-5.policy").read()
    bpol = compile_text(base)
    cands = {"tune-5": base, "reach5": reach(base), "mgroup": mgroup(base), "mgroup+na": noattack(mgroup(base)), "na": noattack(base)}
    only = set(sys.argv[1:])
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("v7zg-cast", "opp-metab")}
    maps = ("00lost-world", "00contest", "01corridors", "01shortcut")
    log = open("runs/tune/monogroup.log", "a")
    for name, t in cands.items():
        if only and name not in only:
            continue
        pol = compile_text(t)
        r = {}
        if name != "tune-5":
            r["all400"] = h2h(pol, bpol, 400, 9391)["win_rate"]
        jobs = [(m, on) for m in maps for on in opps]
        def f(j):
            m, on = j
            a = play(pol, opps[on], f"maps/{m}.map26a", 20, 81)
            b = play(opps[on], pol, f"maps/{m}.map26a", 20, 82)
            return j, round((a["wins"] + 1 - b["wins"]) / 2, 3), a["deaths"]
        with ThreadPoolExecutor(4) as ex:
            for (m, on), w, d in ex.map(f, jobs):
                r[f"{m}/{on}"] = [w, d]
        line = f"{name}: {json.dumps(r)}"
        print(line, flush=True); log.write(line + "\n"); log.flush()
