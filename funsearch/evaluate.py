"""Score a policy by playing it in the simulator (interp/build/interp_eval)."""
import json
import os
import random
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from policygen.compile import to_prefix
from policygen.text import parse

ROOT = Path(__file__).resolve().parent.parent
EVAL_BIN = ROOT / "interp" / "build" / "interp_eval"
MAPS = sorted(str(p) for p in (ROOT / "maps").glob("*.map26a"))


@dataclass
class EvalResult:
    score: float = float("-inf")
    error: str | None = None
    per_opponent: dict = field(default_factory=dict)

    @property
    def ok(self):
        return self.error is None


def score_of(stats):
    """Win rate, plus a small bonus for the tributed-gem margin (breaks ties)."""
    margin = (stats["a_gems"] - stats["b_gems"]) / 1000.0
    return stats["win_rate"] + 0.25 * max(-1.0, min(1.0, margin))


_OPP_CACHE = {}
_OPP_LOCK = threading.Lock()


def _compiled_opponent(spec):
    """A .policy opponent is compiled once to a .pol file; other specs pass through."""
    if not spec.endswith(".policy"):
        return spec
    with _OPP_LOCK:
        if spec not in _OPP_CACHE:
            fd, out = tempfile.mkstemp(suffix=".pol", prefix="opp-")
            with os.fdopen(fd, "w") as f:
                f.write(to_prefix(parse(Path(spec).read_text())))
            _OPP_CACHE[spec] = out
        return _OPP_CACHE[spec]


def evaluate(text, opponents=("builtin:starter",), games=32, threads=4, seed=0, maps=None, timeout=600,
             fuel_mult=1.0):
    """Parse, compile and play `text`; games alternate sides, maps sampled by seed.

    fuel_mult scales every bot's per-turn fuel budget (exploration only: anything
    named best or submitted must be scored at 1.0, the real game)."""
    try:
        steps = parse(text)
        prefix = to_prefix(steps)
    except Exception as e:  # syntax or type error in the policy
        return EvalResult(error=f"{type(e).__name__}: {e}")
    opponents = [_compiled_opponent(o) for o in opponents]
    rng = random.Random(seed)
    pool = maps or MAPS
    chosen = [rng.choice(pool) for _ in range(max(1, games // 2))]
    with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
        f.write(prefix)
        pol = f.name
    try:
        result = EvalResult(score=0.0)
        for opp in opponents:
            out = subprocess.run(
                [str(EVAL_BIN), "--a", pol, "--b", opp, "--games", str(games), "--threads", str(threads),
                 "--seed", str(seed), "--fuel-mult", str(fuel_mult), *chosen],
                capture_output=True, text=True, timeout=timeout)
            stats = json.loads(out.stdout)
            if "error" in stats:
                return EvalResult(error=stats["error"])
            stats.pop("results", None)
            result.per_opponent[Path(opp).stem if opp.endswith(".pol") else opp] = stats
            result.score += score_of(stats) / len(opponents)
        return result
    except subprocess.TimeoutExpired:
        return EvalResult(error="evaluation timed out")
    finally:
        Path(pol).unlink(missing_ok=True)
