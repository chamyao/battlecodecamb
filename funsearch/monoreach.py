"""00lost-world fix: tune-5 loses there to every opponent (34% mean, 0/20 vs opp-metab: 0 gems, 28 deaths a game to
the monolith at (1,15)). The gems around that monolith are goals (only monolith tiles are excluded), and the first camp
in range can be the monolith itself; vs a bot that takes the safe camps, the scoreless-after-300 fallback also sends
everyone at it. Variants on tune-5: drop camp goals within the monolith's reach (5), the r800 fallback, both; screened
all-map vs tune-5 (400 games, seed 9351) plus 00lost-world per opponent (20 games a side)."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.mono_fix import mono

GOALS = "let goals = minus( minus( minus( camp_spawns, respawning_visible_spawns() ), monolith_tiles() ), golem_tiles() )\n"


def reach(t, r=5):
    assert t.count(GOALS) == 1
    return t.replace(GOALS, f"let goals = minus( minus( minus( camp_spawns, respawning_visible_spawns() ), ring(monolith_tiles(), {r}) ), golem_tiles() )\n")


if __name__ == "__main__":
    base = open("policies/tune-5.policy").read()
    bpol = compile_text(base)
    cands = {"tune-5": base, "reach5": reach(base), "reach6": reach(base, 6), "r800": mono(base, "round_number() > 800"),
             "reach5+r800": reach(mono(base, "round_number() > 800"))}
    only = set(sys.argv[1:])
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-metab", "v7zg-cast", "opp-icecream")}
    log = open("runs/tune/monoreach.log", "a")
    for name, t in cands.items():
        if only and name not in only:
            continue
        pol = compile_text(t)
        r = {}
        if name != "tune-5":
            r["all400"] = h2h(pol, bpol, 400, 9351)["win_rate"]
        def f(on):
            a = play(pol, opps[on], "maps/00lost-world.map26a", 20, 61)
            b = play(opps[on], pol, "maps/00lost-world.map26a", 20, 62)
            return on, round((a["wins"] + 1 - b["wins"]) / 2, 3), a["gems"], a["deaths"]
        with ThreadPoolExecutor(3) as ex:
            for on, w, g, d in ex.map(f, opps):
                r[f"lost-world/{on}"] = [w, g, d]
        line = f"{name}: {json.dumps(r)}"
        print(line, flush=True); log.write(line + "\n"); log.flush()
