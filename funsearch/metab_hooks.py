"""Make opp-metab reproduce metab-v3 on 01hooks (docs/ARENA_METAB_V3.md on analysis/sprint1): in the arena metab-v3
beat tune-3 1001-33 there, holding the altar zone as a group of four, 66 captures, 5-10 deaths. The current stand-in
loses hooks to tune-5 (about 116 gems, 20 captures, 14 deaths). Variants of opp-metab, each played as A vs tune-5
on 01hooks (and 01starvation vs tune-3 to keep that reproduction), per-game seeds.
usage: metab_hooks.py [VARIANT ...]"""
import json, sys, itertools
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play

BASE = open("policies/opp-metab.policy").read()
INTRUDER = "let intruder = nearest( enemies_visible() )\n"
EDITS = {
    # stay with the group: alone (no ally within 3) and not holding a capture -> walk to the nearest ally
    "C": [(INTRUDER, "let mate = nearest( allies_visible() )\nif exists(mate) and allies_within(3) == 0 and not contains( capturable_spawns(), position() ) and gems() < 10:\n    move_towards( unit_position(mate) )\n    end_turn()\n" + INTRUDER)],
    # recall earlier (metab-v3 recalls at median 33-58% health)
    "R": [("health() < 0.45 * max_health():", "health() < 0.55 * max_health():")],
    # chase intruders anywhere within 8 of an altar, from up to 7 away
    "Z": [("keep defend_zone = ring( altars(), 6 )", "keep defend_zone = ring( altars(), 8 )"),
          ("distance( position(), unit_position(intruder) ) <= 5", "distance( position(), unit_position(intruder) ) <= 7")],
}


def variant(keys):
    t = BASE
    for k in keys:
        for o, n in EDITS[k]:
            assert t.count(o) == 1, (k, o)
            t = t.replace(o, n)
    return t


def run(name):
    keys = [] if name == "base" else list(name)
    t = variant(keys)
    pol = compile_text(t)
    t5 = compile_file("policies/tune-5.policy")
    t3 = compile_file("policies/tune-3.policy")
    h = play(pol, t5, "maps/01hooks.map26a", 40, 501)
    s = play(pol, t3, "maps/01starvation.map26a", 20, 502)
    return name, {"hooks_vs_t5": h, "starv_vs_t3": {k: s[k] for k in ("wins", "gems", "opp_gems")}}


if __name__ == "__main__":
    names = sys.argv[1:] or ["base", "C", "R", "Z", "CR", "CZ", "CRZ"]
    log = open("runs/tune/metab_hooks.log", "a")
    with ProcessPoolExecutor(4) as ex:
        for name, r in ex.map(run, names):
            line = f"{name}: {json.dumps(r)}"
            print(line, flush=True); log.write(line + "\n"); log.flush()
