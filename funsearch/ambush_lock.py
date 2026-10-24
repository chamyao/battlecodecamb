"""Bush ambush and lock-once tests on v20 (FunSearch lead). v20 wards its own tile in a bush; the bush is what helps.
A1: on a camp approach (goal within 6), step into an adjacent bush that is strictly closer to the goal (cover on the
    way; strictly closer means no back-and-forth). A2: an enemy champion visible within 6 and out of reach, healthy:
    step into an adjacent bush strictly closer to it. Bushes come from a keep (bushes within 3 of a camp spawn), never
    a per-turn filter over bushes(); both fuel-gated > 60000.
L1: lock once per team (shared byte 7): buy one altar lock, place it on an altar within 2 once our bag is empty
    (locks block only enemy tributes; locked_altars() is enemy-only since the lockfix, deploy/v0 b9452ee).
L3: as L1, only an altar within 12 of the enemy spawn region.
Writes policies/candidates/tune-v20-<variant>.policy."""
import sys

BASE = open("policies/tune-v20.policy").read()
KEEP = "keep camp_spawns = camp_spawn_tiles()\n"
DASH = "# tunable: dash toward a camp goal only when it is farther than this\n"
ENEMY = "let enemy = weakest( filter( foes, in_attack_range() ) )\n"
SPAWN = "if at_spawn:\n"
TRIB = "# tribute only with a worthwhile bag"
COVER_KEEP = KEEP + "# bushes near camps (static): cover for ambushes without a per-turn filter over bushes()\nkeep camp_bushes = minus( bushes(), minus( bushes(), ring( camp_spawn_tiles(), 3 ) ) )\n"
A1 = ("# AMBUSH (tune line): on a camp approach, an adjacent bush strictly closer to the goal: step into it\n"
      "if exists(goal) and fuel_remaining() > 60000 and count(foes) == 0 and distance(position(), goal) <= 6 and not contains( bushes(), position() ):\n"
      "    let cover = first( filter( camp_bushes, within(1, position()) ) )\n"
      "    if exists(cover) and distance(cover, goal) < distance(position(), goal):\n"
      "        move_towards(cover)\n        end_turn()\n")
A2 = ("# AMBUSH (tune line): healthy, an enemy within 6 out of reach: an adjacent bush strictly closer to it, step in\n"
      "if fuel_remaining() > 60000 and health() > 0.7 * max_health() and not contains( bushes(), position() ):\n"
      "    let prey0 = nearest( foes )\n"
      "    if exists(prey0) and distance(position(), unit_position(prey0)) <= 6 and distance(position(), unit_position(prey0)) > 1:\n"
      "        let cover2 = first( filter( camp_bushes, within(1, position()) ) )\n"
      "        if exists(cover2) and distance(cover2, unit_position(prey0)) < distance(position(), unit_position(prey0)):\n"
      "            move_towards(cover2)\n            end_turn()\n")


def ambush(t, a1, a2):
    assert t.count(KEEP) == 1 and t.count(DASH) == 1 and t.count(ENEMY) == 1
    t = t.replace(KEEP, COVER_KEEP)
    if a1:
        t = t.replace(DASH, A1 + DASH)
    if a2:
        t = t.replace(ENEMY, A2 + ENEMY)
    return t


def lock_once(t, near_enemy=None):
    assert t.count(SPAWN) == 1 and t.count(TRIB) == 1
    t = t.replace(SPAWN, SPAWN + "    # lock once (tune line): one altar lock per team per game (shared byte 7 = placed)\n"
                  "    if read_shared(7) == 0 and not has_altar_lock():\n        buy_altar_lock()\n", 1)
    cond = "" if near_enemy is None else f" and contains( ring( spawn_region(enemy()), {near_enemy} ), lock_altar )"
    return t.replace(TRIB, "# lock once (tune line): bag empty next to an altar: lock it against enemy tributes, once per team\n"
                     "if gems() == 0 and has_altar_lock() and read_shared(7) == 0:\n"
                     "    let lock_altar = first( filter( altars(), within(2, position()) ) )\n"
                     f"    if exists(lock_altar){cond}:\n"
                     "        place_altar_lock(lock_altar)\n        write_shared(7, 1)\n        end_turn()\n" + TRIB)


if __name__ == "__main__":
    out = {"A1": ambush(BASE, True, False), "A2": ambush(BASE, False, True), "A1A2": ambush(BASE, True, True),
           "L1": lock_once(BASE), "L3": lock_once(BASE, 12)}
    for k, v in out.items():
        open(f"policies/candidates/tune-v20-{k}.policy", "w").write(f"# tune-v20-{k} [tune line]: test on v20 (funsearch/ambush_lock.py)\n" + v)
        print(f"policies/candidates/tune-v20-{k}.policy")
