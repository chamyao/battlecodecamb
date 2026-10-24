"""Genome search operators without the API: edge-scoped merge rules, ID crossover, constant tuning."""
import random
from pathlib import Path

import pytest

from genome import lang
from genome.search import edit, operators

FARMER = (Path(__file__).resolve().parent.parent / "genome" / "examples" / "farmer.genome").read_text()

REPLY = '''```python
@gene("g3", "where I want to walk", parents=["zz"])
def goal() -> Tiles:
    if gems() >= BAG:
        return near_altars()
    return safe_camps()

@gene("new", "camp spawns away from enemies", parents=["g3"])
def safe_camps() -> Tiles:
    acc = camp_spawns()
    for e in enemies():
        acc = acc - near(e.pos, 3)
    return acc
```'''


def test_mutation_merge_keeps_other_genes():
    child, st = operators.apply_mutation(FARMER, REPLY, {"g3", "g5"}, "c1")
    g = lang.parse(child)
    assert st["genes_changed"] == ["g3"] and st["genes_added"] == ["c1a"]
    assert g.genes["safe_camps"].parents == ["g3"] and g.genes["goal"].parents == []
    _, _, pg = edit.segments(FARMER)
    _, _, cg = edit.segments(child)
    assert all(pg[i] == cg[i] for i in pg if i != "g3")


def test_mutation_rejects_fixed_gene_change():
    bad = REPLY.replace("```python\n", '```python\n@gene("g2", "x")\ndef attack_value(u: Unit) -> Num:\n    return 3\n\n')
    with pytest.raises(edit.EditError):
        operators.apply_mutation(FARMER, bad, {"g3", "g5"}, "c1")


def test_mutation_prunes_uncalled():
    reply = '```python\n@gene("g3", "camps only")\ndef goal() -> Tiles:\n    return camp_spawns()\n```'
    child, st = operators.apply_mutation(FARMER, reply, {"g3", "g5"}, "c1")
    assert st["genes_removed"] == ["g4"] and "BAG" not in child


def test_crossover_and_tune():
    rng = random.Random(0)
    other = FARMER.replace("return 20 + 10", "return 25 + 10").replace("return 40 if", "return 45 if")
    c = operators.crossover(FARMER, other, rng)
    assert c.error is None and lang.parse(c.source)
    t = operators.tune(FARMER, rng)
    assert t.error is None and t.log["changes"] and lang.parse(t.source)
