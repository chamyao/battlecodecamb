"""Camp-skip rule (coordinator's formula) on a base policy, with its strength scale K tuned.

Skip the closest goal's camp group when group_threat * group_hp / (K * (1 + allies_within(4))) > health().
There is no strength() block, so K stands in for our damage per turn. The group lookup runs only on
risky turns (computing it every turn cost ~25M fuel per game)."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

OLD = "let goal = closest(goals)\n"


def skip_variant(base, k):
    """Only on a risky turn: look up the goal's group and walk to the closest goal outside it."""
    new = (f"let goal = closest(goals)\n"
           f"# skip a camp group we would lose to (scale K = {k} stands in for our strength; tune line)\n"
           f"if exists(goal) and group_threat(goal) * group_hp(goal) > {k} * (1 + allies_within(4)) * health():\n"
           f"    let alt = closest( minus( goals, group_tiles( filter( goals, within(0, goal) ) ) ) )\n"
           f"    if exists(alt):\n"
           f"        move_towards(alt)\n"
           f"        end_turn()\n")
    assert base.count(OLD) == 1
    return base.replace(OLD, new)


if __name__ == "__main__":
    base_file, tag, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    base = open(base_file).read()
    bpol = compile_text(base)
    cands = {f"skipK={k}": skip_variant(base, k) for k in (10, 20, 40, 80, 160, 320, 640)}
    log = open(f"runs/tune/screen-{tag}.log", "a")
    res = screen(cands, bpol, games=200, seed=seed, log=lambda s: (log.write(s + "\n"), log.flush()))
    json.dump(res, open(f"runs/tune/screen-{tag}.json", "w"))
