"""Early disengage (FunSearch lead, docs/TOP_TEAMS_RULES.md on analysis/sprint1: top teams leave fights at ~0.8 HP, we
at 0.3). On tune-5 + safe recall R8-H0.3 (recall_screen.py): when hurt below D and an enemy champion is within 8,
retreat home instead of fighting on; optionally also recall when clear below C. Scored like recall_screen.py.
usage: disengage_screen.py [VARIANT ...]"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fight_metrics import metrics
from funsearch.recall_screen import safe_recall

ANCHOR = "# safe recall (tune line)"


def disengage(t, d, c=None):
    assert t.count(ANCHOR) == 1
    new = f"""# early disengage (tune line, TOP_TEAMS_RULES): hurt below {d} with an enemy champion within 8 -> retreat home
if not at_spawn and health() < {d} * max_health() and enemies_within(8) > 0:
    let home0 = closest( spawn_region(ally()) )
    dash_to(0, home0)
    dash_to(1, home0)
    move_towards(home0)
    end_turn()
"""
    if c is not None:
        new += f"""if not at_spawn and health() < {c} * max_health() and enemies_within(8) == 0 and not in_danger():
    recall()
    end_turn()
"""
    return t.replace(ANCHOR, new + ANCHOR)


V = {"R8": None, "D0.5": (0.5,), "D0.7": (0.7,), "D0.8": (0.8,), "D0.7-C0.5": (0.7, 0.5), "D0.8-C0.6": (0.8, 0.6)}


BASE = "policies/tune-5.policy"  # DISENGAGE_BASE overrides: a base that already has the safe recall


def run(name):
    import os
    bf = os.environ.get("DISENGAGE_BASE")
    base = open(bf or BASE).read()
    r8 = base if bf else safe_recall(base, 8, 0.3)
    t = r8 if V[name] is None else disengage(r8, *V[name])
    pol = compile_text(t)
    r = {}
    for on in ("v7zg-cast", "opp-metadraft"):
        r[on] = metrics(pol, compile_file(f"policies/{on}.policy"), games=80, seed=9421)
    if V[name] is None:
        return name, r
    r["vs_base"] = h2h(pol, compile_text(r8), 400, 9422, threads=1)["win_rate"]
    return name, r


if __name__ == "__main__":
    names = sys.argv[1:] or list(V)
    log = open("runs/tune/disengage_screen.log", "a")
    with ProcessPoolExecutor(3) as ex:
        for name, r in ex.map(run, names):
            line = f"{name}: {json.dumps(r)}"
            print(line, flush=True); log.write(line + "\n"); log.flush()
