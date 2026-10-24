"""Checks against the C++ interpreter (skipped until interp/build is built)."""
import json
import subprocess
from pathlib import Path

import pytest

from policygen.blocks import REGISTRY
from policygen.compile import to_prefix
from policygen.text import parse

ROOT = Path(__file__).parent.parent
EVAL = ROOT / "interp" / "build" / "interp_eval"
pytestmark = pytest.mark.skipif(not EVAL.exists(), reason="interp not built")


def test_blocks_match_registry():
    cpp = set(subprocess.check_output([str(EVAL), "--list-blocks"], text=True).split())
    assert cpp == {b.key for b in REGISTRY}


def test_starter_beats_idle(tmp_path):
    pol = tmp_path / "starter.pol"
    pol.write_text(to_prefix(parse((ROOT / "policies" / "starter.policy").read_text())))
    out = subprocess.check_output(
        [str(EVAL), "--a", str(pol), "--b", "builtin:idle", "--games", "4", "--threads", "2",
         str(ROOT / "maps" / "00elkring.map26a")], text=True)
    assert json.loads(out)["win_rate"] == 1.0


def test_bot_embedded_policy_is_current(tmp_path):
    """bot/src/policy_data.h must match a fresh encoding of the policy it names: adding a block
    renumbers the op codes, and a stale header would make the bot run the wrong ops."""
    header = (ROOT / "bot" / "src" / "policy_data.h").read_text()
    src = header.split("from ", 1)[1].split(";", 1)[0]
    pol = tmp_path / "p.pol"
    pol.write_text(to_prefix(parse((ROOT / src).read_text())))
    out = tmp_path / "p.h"
    subprocess.check_call(["python3", str(ROOT / "bot" / "encode_policy.py"), str(pol), str(out), src],
                          stdout=subprocess.DEVNULL)
    body = lambda t: [l for l in t.splitlines() if not l.startswith("// Generated")]
    assert body(out.read_text()) == body(header), f"bot/src/policy_data.h is stale: run bot/sync.sh {src}"
