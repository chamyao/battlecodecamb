"""Score a policy by playing it in the simulator (interp/build/interp_eval)."""
import json
import random
import subprocess
import tempfile
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


def evaluate(text, opponents=("builtin:starter",), games=32, threads=4, seed=0, maps=None, timeout=600):
    """Parse, compile and play `text`; games alternate sides, maps sampled by seed."""
    try:
        steps = parse(text)
        prefix = to_prefix(steps)
    except Exception as e:  # syntax or type error in the policy
        return EvalResult(error=f"{type(e).__name__}: {e}")
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
                 "--seed", str(seed), *chosen],
                capture_output=True, text=True, timeout=timeout)
            stats = json.loads(out.stdout)
            if "error" in stats:
                return EvalResult(error=stats["error"])
            stats.pop("results", None)
            result.per_opponent[opp] = stats
            result.score += score_of(stats) / len(opponents)
        return result
    except subprocess.TimeoutExpired:
        return EvalResult(error="evaluation timed out")
    finally:
        Path(pol).unlink(missing_ok=True)
