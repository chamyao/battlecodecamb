"""Child constant hill-climb (funsearch.tune: literals, changed_constants, mutate_literal, climb_child)."""
import random

from funsearch.tune import changed_constants, climb_child, literals, mutate_literal
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
    assert [(x["name"], x["value"]) for x in changed_constants(PARENT, CHILD)] == [("SLACK", "1")]
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
    def ev(t, k):  # rewards larger SLACK, deterministic
        return 0.5 + 0.05 * float(t.split("SLACK = ")[1].split("\n")[0])
    best, info = climb_child(PARENT, CHILD, ev, steps=10, rng=random.Random(0), margin=0.02)
    assert info["after"] >= info["before"]
    assert ("SLACK" in info["changed"]) == (best != CHILD)
    flat, info2 = climb_child(PARENT, CHILD, lambda t, k: 0.5, steps=5, rng=random.Random(0))
    assert flat == CHILD and info2["changed"] == {}
    same, none = climb_child(PARENT, PARENT, lambda t, k: 0.5)
    assert same == PARENT and none is None


def test_bit_arithmetic_is_never_tuned():
    t = "let v = read_shared(7)\nlet lock = v - 2 * floor(v / 2)\nif ((v - (4 * floor((v / 4)))) == 0):\n    end_turn()\nlet h = 0.5\n"
    assert [x["value"] for x in literals(t)] == ["0.5"]
