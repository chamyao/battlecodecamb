import random
from pathlib import Path

import pytest

from policygen.blocks import TYPES
from policygen.grammar import MIN_DEPTH, GrammarState, Vocab, decode, encode, sample
from policygen.text import format_policy, parse

STARTER = (Path(__file__).parent.parent / "policies" / "starter.policy").read_text()
VOCAB = Vocab()


def test_every_type_is_producible():
    assert all(MIN_DEPTH[t] < float("inf") for t in TYPES)


def test_starter_parses():
    steps = parse(STARTER)
    assert len(steps) > 10


def test_text_round_trip():
    steps = parse(STARTER)
    assert format_policy(parse(format_policy(steps))) == format_policy(steps)


def test_token_round_trip():
    ids, consts = encode(parse(STARTER), VOCAB)
    back = decode(ids, consts, VOCAB)
    assert encode(back, VOCAB) == (ids, consts)


def test_mask_accepts_starter():
    ids, _ = encode(parse(STARTER), VOCAB)
    state = GrammarState(VOCAB)
    for i in ids:
        state.push(i)
    assert state.done


def test_mask_rejects_type_errors():
    state = GrammarState(VOCAB)
    state.push(VOCAB.ids["move_towards(Tile)"])
    assert VOCAB.ids["health()"] not in state.allowed()
    assert VOCAB.ids["position()"] in state.allowed()


@pytest.mark.parametrize("seed", range(2000))
def test_samples_are_valid(seed):
    ids, consts = sample(VOCAB, random.Random(seed))
    assert len(ids) <= VOCAB.limits.max_tokens
    steps = decode(ids, consts, VOCAB)
    text = format_policy(steps)
    reparsed = parse(text)  # type-checks again from text
    assert encode(reparsed, VOCAB) == (ids, consts)


def test_python_habits():
    steps = parse("if gems() != 0 and True:\n    let x = -gems()\n    set_priority(x)\n")
    assert format_policy(steps)
    for bad in ("set_priority(gems() % 2)", "if 1 < gems() < 3:\n    recall()\n"):
        with pytest.raises(SyntaxError):
            parse(bad)


MACROS = """
def low_health(frac):
    return health() < frac * max_health()

def go_home():
    let home = closest(spawn_region(ally()))
    move_towards(home)
    end_turn()

if low_health(0.3):
    go_home()
if low_health(0.5) and gems() > 0:
    go_home()
recall()
"""


def test_macros_expand_inline():
    steps = parse(MACROS)
    text = format_policy(steps)
    assert "def " not in text and text.count("move_towards") == 2
    assert format_policy(parse(text)) == text  # the expansion is an ordinary policy


def test_macro_errors():
    with pytest.raises(SyntaxError):
        parse("def f():\n    f()\nf()\n")
    with pytest.raises(TypeError):
        parse("def f(x):\n    return x\nrecall()\nset_priority(f())\n")
    with pytest.raises(TypeError):
        parse("def g():\n    recall()\nif g():\n    recall()\n")
