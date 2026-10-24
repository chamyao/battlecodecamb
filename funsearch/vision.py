"""Cheap vision rules on v20 (tune-fight-2s: ward our own tile when in a bush with no enemy in sight; FunSearch lead).
A ward is placed within 2 tiles, sees 6 and recharges over 10 turns; one active ward per champion. Variants:
w-any (own tile with no enemy in sight, bush or not), w-altar (carrying: ward an altar within 2 first),
w-goal (ward the camp goal when within 2), w-altar+goal. Writes policies/candidates/tune-v20-<variant>.policy."""
import sys

BASE = open("policies/tune-v20.policy").read()
BUSH = "if count(foes) == 0 and contains( bushes(), position() ):\n    place_ward( position() )\n"
GOAL = "let goal = closest(goals)\n"
ALTAR = ("# ward (tune line vision): carrying, an altar within 2 gets the ward (vision of the bank spot)\n"
         "if gems() > 0:\n    let ward_altar = first( filter( altars(), within(2, position()) ) )\n"
         "    if exists(ward_altar):\n        place_ward(ward_altar)\n")
GOALW = ("# ward (tune line vision): the camp goal within 2 gets the ward (vision of the camp and its respawn)\n"
         "if exists(goal) and count(foes) == 0 and distance( position(), goal ) <= 2:\n    place_ward(goal)\n")


def variants():
    assert BASE.count(BUSH) == 1 and BASE.count(GOAL) == 1
    any_ = BASE.replace(BUSH, "# ward (tune line vision): our own tile, with no enemy in sight (bush or not)\n"
                        "if count(foes) == 0:\n    place_ward( position() )\n")
    alt = BASE.replace(BUSH, ALTAR + BUSH)
    goal = BASE.replace(GOAL, GOAL + GOALW)
    return {"w-any": any_, "w-altar": alt, "w-goal": goal, "w-altar+goal": alt.replace(GOAL, GOAL + GOALW)}


if __name__ == "__main__":
    for k, v in variants().items():
        open(f"policies/candidates/tune-v20-{k}.policy", "w").write(f"# tune-v20-{k} [tune line]: vision rule test on v20 (funsearch/vision.py)\n" + v)
        print(f"policies/candidates/tune-v20-{k}.policy")
