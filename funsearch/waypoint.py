"""Intermediate targets for long moves (coordinator's lead): when the target is more than D away, walk to the
nearest tile of a ring of radius distance - D around the target set, so the walk searches stay short.

Scopes: "goal" = retreat-home and camp-goal moves; "all" = also the three altar moves of a tribute trip.
usage: waypoint.py BASE TAG"""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fuel_guard import big_world

MACRO = '''
# tune line: long moves go via a waypoint D tiles out, so the walk searches stay short
def go_to(s, t):
    if distance(position(), t) > {d}:
        let mid = closest( ring( s, distance(position(), t) - {d} ) )
        if exists(mid):
            move_towards(mid)
        else:
            move_towards(t)
    else:
        move_towards(t)
'''

EDITS = {
    "goal": [("        move_towards(home)\n", "        go_to(spawn_region(ally()), home)\n"),
             ("move_towards( goal )\nlet camp2", "go_to( filter( goals, within(0, goal) ), goal )\nlet camp2")],
    "all": [("        move_towards(target)\n", "        go_to( filter( safe_altar_ring, within(0, target) ), target )\n"),
            ("        move_towards(target2)\n", "        go_to( filter( safe_altar_ring, within(0, target2) ), target2 )\n"),
            ("    move_towards( altar_goal )\n", "    go_to( filter( altar_ring, within(0, altar_goal) ), altar_goal )\n")],
}
ANCHOR = "def dash_to(slot, t):\n"


def waypoint(base, d, scope):
    t = base.replace(ANCHOR, MACRO.format(d=d).lstrip("\n") + "\n" + ANCHOR, 1)
    for old, new in EDITS["goal"] + (EDITS["all"] if scope == "all" else []):
        assert t.count(old) == 1, old
        t = t.replace(old, new)
    return t


if __name__ == "__main__":
    base_file, tag = sys.argv[1], sys.argv[2]
    base = open(base_file).read()
    bpol = compile_text(base)
    log = open(f"runs/tune/waypoint-{tag}.log", "a")
    cands = {}
    for scope in ("goal", "all"):
        for d in (10, 16, 24, 36):
            cands[f"{scope}-{d}"] = waypoint(base, d, scope)
    for name, text in cands.items():
        pol = compile_text(text)
        bw = big_world(pol, bpol, games=200, seed=51)
        allm = h2h(pol, bpol, 200, 11)
        r = {"bigworld_susp": bw["a_suspensions"], "bigworld_wr": bw["win_rate"], "all200_wr": allm["win_rate"],
             "all200_susp": allm["a_suspensions"], "fuel_per_game": allm["a_fuel_per_game"]}
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
