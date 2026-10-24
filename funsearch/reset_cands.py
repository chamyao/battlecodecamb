"""Tune-line candidates rebased on tune5-reset (coord/league de2576f): camp reset (attack, cast_self the reset, attack
again, as tune5-reset does against champions), safe recall R8-H0.3, the map fixes (r800 + T240 + monolith groups),
and their stack. Writes runs/tune/league/r-*.policy for tools/league.py."""
import os, sys
sys.path.insert(0, '.')
from funsearch.mono_fix import mono
from funsearch.threat_bank import threat_bank
from funsearch.monogroup import mgroup
from funsearch.recall_screen import safe_recall

CAMP = """    cast_on(0, camp)
    cast_on(1, camp)
    attack(camp)
    end_turn()
"""


def camp_reset(t):
    assert t.count(CAMP) == 1
    return t.replace(CAMP, """    cast_on(0, camp)
    cast_on(1, camp)
    attack(camp)
    # attack reset on camps too (tune line): a second basic attack after the first
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
    attack(camp)
    end_turn()
""")


def fixes(t):
    return mgroup(threat_bank(mono(t, "round_number() > 800"), 240))


if __name__ == "__main__":
    b = open("policies/tune5-reset.policy").read()
    c = {"r-campreset": camp_reset(b), "r-recall8": safe_recall(b, 8, 0.3), "r-fixes": fixes(b),
         "r-all": safe_recall(camp_reset(fixes(b)), 8, 0.3)}
    os.makedirs("runs/tune/league", exist_ok=True)
    for k, v in c.items():
        open(f"runs/tune/league/{k}.policy", "w").write(f"# {k}: tune line candidate on tune5-reset\n" + v)
    print(" ".join(f"runs/tune/league/{k}.policy" for k in c))
