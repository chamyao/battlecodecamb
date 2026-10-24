"""Exploration of discrete choices FunSearch never tries (FunSearch lead), on tune5-campreset. Crude switch-ons, to see
whether any is worth handing to FunSearch.
  drafts SEED N: random-draft regression. N random 5-champion orders over all 12 champions, 80 games each (every map,
    both sides) vs tune5-campreset; least squares of win rate on "champion in our first 4 picks" (+ the 5th pick
    separately). Output runs/tune/explore-drafts.{log,json}.
  switches: lock (buy an altar lock at spawn; after a tribute, lock that altar: it blocks enemy tributes only),
    ward-altar (place the free ward on the nearest altar when within 3), hunter-vendetta / hunter-vv (that champion
    engages enemies within 7 while above 80% HP), and lock+ward. 400 games each vs tune5-campreset (seed 9461) +
    fight metrics vs v7zg-cast (80 games). Output runs/tune/explore-switches.log.
usage: explore.py drafts SEED N | explore.py switches [VARIANT ...]"""
import json, random, sys
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fight_metrics import metrics

import os
BASE = os.environ.get("EXPLORE_BASE", "policies/tune5-campreset.policy")
FIGHT_OPP = os.environ.get("EXPLORE_FIGHT_OPP", "policies/v7zg-cast.policy")
CHAMPS = ["ryth", "vesper_vale", "vendetta", "cassi_issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "heart_of_ruin"]

SPAWN = "if at_spawn:\n"
TRIB = "    if exists(altar):\n        tribute(altar)\n        end_turn()\n"
ENEMY = "let enemy = weakest( filter( enemies_visible(), in_attack_range() ) )\n"


def lock(t):
    t = t.replace(SPAWN, SPAWN + "    if not has_altar_lock():\n        buy_altar_lock()\n", 1)
    anchor = "# tribute only with a worthwhile bag"
    assert t.count(anchor) == 1
    return t.replace(anchor, "# altar lock (explore): with an empty bag next to an altar, lock it against enemy tributes\n"
                     "let near_altar = first( filter( altars(), within(2, position()) ) )\n"
                     "if gems() == 0 and has_altar_lock() and exists(near_altar) and not contains( locked_altars(), near_altar ):\n"
                     "    place_altar_lock(near_altar)\n    end_turn()\n" + anchor)


def ward(t):
    anchor = "# tribute only with a worthwhile bag"
    return t.replace(anchor, "# ward (explore): the free ward on the nearest altar when within 3 (it recharges over 10 turns)\n"
                     "let ward_altar = first( filter( altars(), within(3, position()) ) )\n"
                     "if exists(ward_altar) and random_int(10) == 0:\n    place_ward(ward_altar)\n" + anchor)


def hunter(t, champ):
    assert t.count(ENEMY) == 1
    return t.replace(ENEMY, f"# hunter role (explore): {champ} engages enemies within 7 while healthy\n"
                     f"let prey = nearest( enemies_visible() )\n"
                     f"if i_am(champ_{champ}()) and exists(prey) and health() > 0.8 * max_health() and distance( position(), unit_position(prey) ) <= 7 and not contains( spawn_region(enemy()), unit_position(prey) ):\n"
                     f"    move_towards( unit_position(prey) )\n" + ENEMY, 1)


SW = {"lock": lock, "ward-altar": ward, "hunter-vendetta": lambda t: hunter(t, "vendetta"),
      "hunter-vv": lambda t: hunter(t, "vesper_vale"), "lock+ward": lambda t: ward(lock(t))}


def run_switch(name):
    base = open(BASE).read()
    pol = compile_text(SW[name](base))
    r = {"vs_base": h2h(pol, compile_text(base), 400, 9461, threads=1)["win_rate"],
         "fight": metrics(pol, compile_file(FIGHT_OPP), games=80, seed=9462)}
    if name == "lock":
        r["fight_base"] = metrics(compile_text(base), compile_file(FIGHT_OPP), games=80, seed=9462)
    return name, r


def drafts(seed, n):
    rng = random.Random(seed)
    base = open(BASE).read()
    bpol = compile_text(base)
    log = open("runs/tune/explore-drafts.log", "a")
    rows = []
    for i in range(n):
        o = rng.sample(CHAMPS, 5)
        pol = compile_text(set_draft(base, chain_draft(o)))
        try:
            wr = h2h(pol, bpol, 80, seed * 1000 + i)["win_rate"]
        finally:
            Path(pol).unlink(missing_ok=True)
        rows.append((o, wr))
        log.write(f"{','.join(o)}: {wr:.4f}\n"); log.flush()
    # least squares: wr ~ b0 + sum_c b4[c] * [c in first 4] + sum_c b5[c] * [c is 5th]
    try:
        import numpy as np
    except ImportError:  # the rows are logged; fit offline
        json.dump({"rows": rows}, open("runs/tune/explore-drafts.json", "w"))
        return
    X = np.array([[1.0] + [float(c in o[:4]) for c in CHAMPS] + [float(c == o[4]) for c in CHAMPS] for o, _ in rows])
    y = np.array([w for _, w in rows])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    eff = {c: {"top4": round(float(b[1 + k]), 4), "fifth": round(float(b[13 + k]), 4)} for k, c in enumerate(CHAMPS)}
    json.dump({"intercept": float(b[0]), "effects": eff, "rows": rows}, open("runs/tune/explore-drafts.json", "w"), indent=1)
    for c, e in sorted(eff.items(), key=lambda kv: -kv[1]["top4"]):
        print(c, e, flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "drafts":
        drafts(int(sys.argv[2]), int(sys.argv[3]))
    else:
        names = sys.argv[2:] or list(SW)
        log = open(os.environ.get("EXPLORE_LOG", "runs/tune/explore-switches.log"), "a")
        with ProcessPoolExecutor(4) as ex:
            for name, r in ex.map(run_switch, names):
                line = f"{name}: {json.dumps(r)}"
                print(line, flush=True); log.write(line + "\n"); log.flush()
