import random

from funsearch.llm import AXES, NEW_BLOCKS, explore_user, sample_variant


def test_vocab_share():
    rng = random.Random(0)
    vs = [sample_variant(rng, 2) for _ in range(2000)]
    assert 0.15 < sum(v["vocab"] for v in vs) / len(vs) < 0.25
    assert not any(sample_variant(rng, 2, vocab_share=0.0)["vocab"] for _ in range(100))


def test_vocab_prompt_lists_new_blocks():
    rng = random.Random(0)
    v = dict(axis="combat", change="edit", framing="champion", catalog="lean", evidence="none", parents="single")
    plain = explore_user([("end_turn()\n", 0.5, {})], dict(v, vocab=False), rng)
    vocab = explore_user([("end_turn()\n", 0.5, {})], dict(v, vocab=True), rng)
    assert "Newest blocks" not in plain and "Newest blocks" in vocab
    assert "- unit_tributing:" in vocab and "- slot_stun:" in vocab


def test_axis_briefs_state_levers():
    assert all("Levers:" in t for t in AXES.values())
    assert set(NEW_BLOCKS) >= {"unit_tributing", "unit_is", "unit_shield", "slot_stun", "slot_range", "slot_radius"}


def test_refresh_exec_blocks_uses_marker_and_cache(tmp_path):
    import json
    from funsearch import evaluate
    calls = []
    orig = evaluate.executed_blocks
    evaluate.executed_blocks = lambda text: calls.append(text) or {"move_to"}
    try:
        rows = [dict(id=0, text="a", score=0.5, error=None, metrics=dict(exec_blocks=["x"], exec_opp="starter")),
                dict(id=1, text="b", score=0.5, error=None, metrics=dict(exec_blocks=["idle_only"])),
                dict(id=2, text="c", score=None, error="bad", metrics={}),
                dict(id=3, text="d", score=0.4, error=None, metrics={})]
        cache = tmp_path / "exec_blocks_v2.json"
        cache.write_text(json.dumps({"3": ["cached"]}))
        got = evaluate.refresh_exec_blocks(rows, cache, threads=2)
        assert got == {0: ["x"], 1: ["move_to"], 3: ["cached"]} and calls == ["b"]
        assert json.loads(cache.read_text())["1"] == ["move_to"]
    finally:
        evaluate.executed_blocks = orig
