"""Hand fight tests on v19 (FunSearch lead, from docs/TOP_TEAMS_FIGHTS.md on analysis/sprint1).
(a) an enemy champion within 5 pre-empts camp attacks: a-engage (walk at it), a-back (step away), a-skip (carry on
    to the goal, no camp hits); (b) target choice in the attack block instead of the weakest in range: b-tt (the team
    target when in range), b-rich (the richest: carriers), b-dd (prefer VV / HoR / Vendetta, the top teams' killers,
    among the weakest, nearest and richest in range). Writes policies/candidates/tune-v19-<variant>.policy."""
import sys
sys.path.insert(0, '.')

BASE = open("policies/tune-v19.policy").read()
CAMP = "let camp = first( filter( camps, in_attack_range() ) )\nif exists(camp):\n"
CAMP2 = "let camp2 = first( filter( camps, in_attack_range() ) )\nif exists(camp2):\n"
ENEMY = "let enemy = weakest( filter( foes, in_attack_range() ) )\n"


def pre_empt(t, mode):
    assert t.count(CAMP) == 1 and t.count(CAMP2) == 1
    step = {"engage": "    move_towards( unit_position(rival) )\n    end_turn()\n",
            "back": "    move_away_from( unit_position(rival) )\n    end_turn()\n", "skip": ""}[mode]
    pre = ("# PRE-EMPT (tune line, TOP_TEAMS_FIGHTS): with an enemy champion within 5, don't start a camp fight\n"
           "let rival_near = enemies_within(5) > 0\n")
    if step:
        pre += ("if rival_near and fuel_remaining() > 60000:\n    let rival = nearest( foes )\n    if exists(rival):\n"
                + "".join("    " + l for l in step.splitlines(True)))
    t = t.replace(CAMP, pre + "let camp = first( filter( camps, in_attack_range() ) )\nif exists(camp) and not rival_near:\n")
    return t.replace(CAMP2, "let camp2 = first( filter( camps, in_attack_range() ) )\nif exists(camp2) and not rival_near:\n")


HIT = """    cast_on(0, {u})
    cast_on(1, {u})
    attack({u})
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
    attack({u})
    end_turn()
"""
REACH = "(distance( position(), unit_position({u}) ) <= 1 or (i_am_ranged() and distance( position(), unit_position({u}) ) <= 3))"
NOT_SPAWN = "not contains( spawn_region(enemy()), unit_position({u}) )"


def pick_first(t, header, cands):
    """Before the default attack block (weakest in range): attack the first candidate (name, let-expression,
    condition) that exists, is in reach and off its spawn."""
    assert t.count(ENEMY) == 1
    blk = header
    for name, expr, cond in cands:
        blk += f"let {name} = {expr}\n"
        c = f"exists({name}) and {REACH.format(u=name)} and {NOT_SPAWN.format(u=name)}" + (f" and ({cond.format(u=name)})" if cond else "")
        blk += f"if {c}:\n" + HIT.format(u=name)
    return t.replace(ENEMY, blk + ENEMY)


def target_tt(t):
    return pick_first(t, "# TARGET (tune line): the team target (cast-ahead names the nearest enemy within 4) when in reach\n",
                      [("tt", "team_target()", "")])


def target_rich(t):
    return pick_first(t, "# TARGET (tune line): a carrier in reach first (its gems become ours)\n",
                      [("e_rich", "richest( filter( foes, in_attack_range() ) )", "unit_gems({u}) > 0")])


DD = "unit_is({u}, champ_vesper_vale()) or unit_is({u}, champ_heart_of_ruin()) or unit_is({u}, champ_vendetta())"


def target_dd(t):
    return pick_first(t, "# TARGET (tune line): the top teams' killers (VV, HoR, Vendetta) first, among the weakest / nearest in reach\n",
                      [("e_weak", "weakest( filter( foes, in_attack_range() ) )", DD),
                       ("e_near", "nearest( filter( foes, in_attack_range() ) )", DD)])


if __name__ == "__main__":
    out = {"a-engage": pre_empt(BASE, "engage"), "a-back": pre_empt(BASE, "back"), "a-skip": pre_empt(BASE, "skip"),
           "b-tt": target_tt(BASE), "b-rich": target_rich(BASE), "b-dd": target_dd(BASE)}
    for k, v in out.items():
        open(f"policies/candidates/tune-v19-{k}.policy", "w").write(f"# tune-v19-{k} [tune line]: hand fight test on v19 (funsearch/hand_fight.py)\n" + v)
    print(" ".join(f"policies/candidates/tune-v19-{k}.policy" for k in out))
