"""Child constant hill-climb (funsearch.tune: literals, changed_constants, mutate_literal, climb_child)."""
import random

from funsearch.tune import changed_constants, climb_child, climb_targets, code_lines, literals, mutate_literal
from policygen.text import parse

PARENT = """# v1: header line
if is_draft():
    pick( random_champion(unpicked_champions()) )
    end_turn()
RANGE = 6
if ability_ready(1) and health() > 0.5 * max_health():
    write_shared(7, 3)
end_turn()
"""
CHILD = PARENT.replace("# v1: header line\n", "# v1: header line\n# v2: slack\n").replace(
    "RANGE = 6\n", "RANGE = 6\nSLACK = 1\n").replace("health() > 0.5", "health() > 0.6")


def test_literals_skip_comments_and_index_args():
    vals = [x["value"] for x in literals(PARENT)]
    assert vals == ["6", "0.5"]  # ability_ready(1) index excluded, write_shared line skipped, comments skipped


def test_changed_constants_prefers_named():
    assert [(x["name"], x["value"]) for x in changed_constants(PARENT, CHILD)] == [("SLACK", "1"), (None, "0.6")]
    assert changed_constants(PARENT, PARENT) == []


def test_changed_constants_falls_back_to_changed_lines():
    child = PARENT.replace("health() > 0.5", "health() > 0.6")
    assert [x["value"] for x in changed_constants(PARENT, child)] == ["0.6"]


def test_mutate_literal_keeps_text_and_parses():
    lit = changed_constants(PARENT, CHILD)[0]
    out, new = mutate_literal(CHILD, lit, random.Random(3))
    assert out.startswith("# v1: header line\n# v2: slack\n") and f"SLACK = {new}" in out
    parse(out)


def test_climb_accepts_only_clear_gains():
    def ev(t):  # rewards larger SLACK, deterministic
        return 0.5 + 0.05 * float(t.split("SLACK = ")[1].split("\n")[0])
    best, info = climb_child(PARENT, CHILD, ev, steps=10, rng=random.Random(0), margin=0.02, max_rejects=10)
    assert info["after"] >= info["before"]
    assert ("SLACK" in info["changed"]) == (best != CHILD)
    flat, info2 = climb_child(PARENT, CHILD, lambda t: 0.5, steps=5, rng=random.Random(0), max_rejects=2)
    assert flat == CHILD and info2["changed"] == {} and info2["evals"] == 3  # incumbent + 2 rejected steps
    based, info3 = climb_child(PARENT, CHILD, lambda t: 0.5, steps=5, rng=random.Random(0), max_rejects=2, base=0.5)
    assert info3["evals"] == 2  # incumbent score reused
    same, none = climb_child(PARENT, PARENT, lambda t: 0.5)
    assert same == PARENT and none is None


def test_bit_arithmetic_is_never_tuned():
    t = "let v = read_shared(7)\nlet lock = v - 2 * floor(v / 2)\nif ((v - (4 * floor((v / 4)))) == 0):\n    end_turn()\nlet h = 0.5\n"
    assert [x["value"] for x in literals(t)] == ["0.5"]


def test_edited_region_without_new_constants():
    child = PARENT.replace("if ability_ready(1) and health()", "if ability_ready(1) and alive() and health()")
    assert [x["value"] for x in climb_targets(PARENT, child)] == ["0.5"]


def test_rewrite_falls_back_to_all():
    child = "RANGE = 9\nlet a = 0.25\nlet b = 4\n"
    assert [x["value"] for x in climb_targets(PARENT, child)] == ["9", "0.25", "4"]


def test_comment_only_change_is_no_code_change():
    assert code_lines(PARENT) == code_lines(PARENT.replace("# v1: header line", "# v1: header line, reworded") + "\n# end\n")


def test_equality_flags_not_tuned_and_zero_moves_up():
    t = "if lk_placed == 0 and lk_bought != 1:\n    end_turn()\nif enemies_within(5) > 0:\n    end_turn()\n"
    lits = literals(t)
    assert [x["value"] for x in lits] == ["5", "0"]
    out, new = mutate_literal(t, lits[1], random.Random(0))
    assert new == "1"
