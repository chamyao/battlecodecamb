"""Shared helper library (funsearch.helpers)."""
import json

from funsearch.helpers import extract_defs, harvest, normalise, prompt_section, tag

PARENT = """# p
if is_draft():
    pick( random_champion(unpicked_champions()) )
    end_turn()
end_turn()
"""
HELPER = """def hit(u):
    # comment
    let p = unit_position(u)
    if distance(p, position()) <= 1:
        attack(u)
"""
CHILD = HELPER + PARENT


def test_extract_and_normalise_ignore_names_and_comments():
    (name, (params, src)), = extract_defs(CHILD).items()
    assert name == "hit" and params == ["u"]
    renamed = HELPER.replace("hit", "strike").replace("(u)", "(target)").replace("u)", "target)").replace("# comment", "")
    (n2, (p2, s2)), = extract_defs(renamed).items()
    assert normalise(name, params, src) == normalise(n2, p2, s2)


def test_harvest_ranks_introduced_helpers_and_tags(tmp_path):
    rows = [dict(id=0, island=0, text=PARENT, score=0.5, parents=[], model="seed", error=None, metrics={}),
            dict(id=1, island=0, text=CHILD, score=0.6, parents=[0], model="m", error=None, metrics={}),
            dict(id=2, island=0, text=CHILD, score=0.62, parents=[1], model="m", error=None, metrics={})]
    f = tmp_path / "hyb-g1" / "programs.jsonl"
    f.parent.mkdir()
    f.write_text("\n".join(json.dumps(r) for r in rows))
    lib = harvest([str(tmp_path)])
    assert len(lib) == 1 and lib[0]["name"] == "hit" and lib[0]["introduced"] == 1 and lib[0]["uses"] == 2
    assert abs(lib[0]["mean_delta"] - 0.1) < 1e-9 and lib[0]["self_contained"]
    assert "def hit(u):" in prompt_section(lib)
    keys = {h["normalised"]: h["name"] for h in lib}
    assert tag(CHILD, keys) == ["hit"] and tag(PARENT, keys) == []
