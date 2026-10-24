"""Safe recall (FunSearch lead priority (b), docs/TOP_TEAMS.md: 23% of tune-5's ladder deaths to the top teams came
mid-recall, which damage cancels). Never start a recall with an enemy champion within R tiles: retreat first (home,
or away from the nearest enemy), recall only when clear. Grid over R and the low-HP threshold H on tune-5.
Scored by the TOP_TEAMS metrics (fight_metrics.py) vs v7zg-cast and opp-metadraft (80 games each, all maps,
seed 9421) and win rate vs tune-5 (400 games, seed 9422).
usage: recall_screen.py [VARIANT ...]"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fight_metrics import metrics

LOW = """if not at_spawn and health() < 0.3 * max_health():
    if in_danger():
        let home = closest( spawn_region(ally()) )
        dash_to(0, home)
        dash_to(1, home)
        move_towards(home)
        end_turn()
    recall()
    end_turn()
if not at_spawn and gems() > 0 and health() < 0.5 * max_health() and not in_danger():
    recall()
    end_turn()
"""


def safe_recall(t, r, h, away=False):
    assert t.count(LOW) == 1
    danger = f"(in_danger() or enemies_within({r}) > 0)"
    step = ("        let foe = nearest( enemies_visible() )\n        if exists(foe):\n"
            "            move_away_from( unit_position(foe) )\n            end_turn()\n") if away else ""
    new = f"""# safe recall (tune line): never start a recall with an enemy champion within {r}; retreat first, recall when clear
if not at_spawn and health() < {h} * max_health():
    if {danger}:
{step}        let home = closest( spawn_region(ally()) )
        dash_to(0, home)
        dash_to(1, home)
        move_towards(home)
        end_turn()
    recall()
    end_turn()
if not at_spawn and gems() > 0 and health() < 0.5 * max_health() and not {danger}:
    recall()
    end_turn()
"""
    return t.replace(LOW, new)


V = {"tune-5": None}
for r in (6, 8, 10):
    for h in (0.3, 0.4, 0.5):
        V[f"R{r}-H{h}"] = (r, h, False)
V["R8-H0.3-away"] = (8, 0.3, True)
V["R8-H0.4-away"] = (8, 0.4, True)


def run(name):
    base = open("policies/tune-5.policy").read()
    t = base if V[name] is None else safe_recall(base, *V[name])
    pol = compile_text(t)
    r = {}
    for on in ("v7zg-cast", "opp-metadraft"):
        r[on] = metrics(pol, compile_file(f"policies/{on}.policy"), games=80, seed=9421)
    if V[name] is not None:
        r["vs_t5"] = h2h(pol, compile_text(base), 400, 9422, threads=1)["win_rate"]
    return name, r


if __name__ == "__main__":
    names = sys.argv[1:] or list(V)
    log = open("runs/tune/recall_screen.log", "a")
    with ProcessPoolExecutor(4) as ex:
        for name, r in ex.map(run, names):
            line = f"{name}: {json.dumps(r)}"
            print(line, flush=True); log.write(line + "\n"); log.flush()
