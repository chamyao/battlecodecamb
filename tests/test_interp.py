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
