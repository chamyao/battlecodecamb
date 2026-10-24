"""Scoring for both representations through one path: genome_eval (interp_eval + genome: sides, same JSON).

- A genome is compiled by genome/build.py and played as genome:<so>; a .policy is compiled to a .pol.
- Paired seeds: every program is played on the same games (seed -> maps and game seeds), so a child and
  its parent differ only by the program. Screen and confirm use separate seeds.
- Two-stage confirmation as in funsearch/run.py: screen on few games; confirm promising children on many
  fresh games (and the parent on the same fresh games).
- Behavioural twins: a child whose per-game results and gem totals equal its parent's on the screen games
  plays the same games; it is flagged (the edit changed nothing that matters there).
"""
import hashlib
import json
import random
import subprocess
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from funsearch.evaluate import MAPS, ROOT, score_of

from .. import build as gbuild
from .. import lang

EVAL = ROOT / "genome" / "build" / "genome_eval"


@dataclass
class Result:
    score: float = float("-inf")
    error: str | None = None
    per_opponent: dict = field(default_factory=dict)
    fingerprint: str = ""   # hash of per-game outcomes: equal => same games played out the same

    @property
    def ok(self):
        return self.error is None


class Scorer:
    def __init__(self, opponents, screen_games=40, confirm_games=120, screen_seed=0, confirm_seed=1,
                 threads=2, maps=None, timeout=900, fuel_mult=1.0):
        self.screen_games, self.confirm_games = screen_games, confirm_games
        self.screen_seed, self.confirm_seed = screen_seed, confirm_seed
        self.threads, self.maps, self.timeout = threads, maps or MAPS, timeout
        self.fuel_mult = fuel_mult  # scales every bot's per-turn fuel (both sides); 1.0 = the real game
        self.lock = threading.Lock()
        self.cache = {}
        self.tmp = Path(tempfile.mkdtemp(prefix="gsearch-"))
        self.opponents = [self._spec(o) for o in opponents]
        self.opp_names = [Path(o).stem if not o.startswith("builtin:") else o for o in opponents]

    # ---- program -> genome_eval side spec
    def _spec(self, text_or_path, kind=None):
        """A path (.genome/.policy/.pol/builtin:) or program text (kind 'genome' or 'policy')."""
        if kind is None:
            if text_or_path.startswith("builtin:") or text_or_path.endswith(".pol"):
                return text_or_path
            kind = "genome" if text_or_path.endswith(".genome") else "policy"
            text = Path(text_or_path).read_text()
        else:
            text = text_or_path
        if kind == "genome":
            return f"genome:{gbuild.build(text)}"
        from policygen.compile import to_prefix
        from policygen.text import parse
        out = self.tmp / (hashlib.sha256(text.encode()).hexdigest()[:16] + ".pol")
        if not out.exists():
            out.write_text(to_prefix(parse(text)))
        return str(out)

    def _games(self, seed, games):
        rng = random.Random(seed)
        return [rng.choice(self.maps) for _ in range(max(1, games // 2))]

    def evaluate(self, text, kind, seed, games):
        key = (hashlib.sha256(text.encode()).hexdigest(), kind, seed, games)
        with self.lock:
            if key in self.cache:
                return self.cache[key]
        try:
            a = self._spec(text, kind)
        except (lang.GenomeError, RuntimeError, Exception) as e:  # type errors, compile failures
            return Result(error=f"{type(e).__name__}: {str(e)[:500]}")
        res = Result(score=0.0)
        outcomes = []
        try:
            for opp, name in zip(self.opponents, self.opp_names):
                out = subprocess.run([str(EVAL), "--a", a, "--b", opp, "--games", str(games), "--threads",
                                      str(self.threads), "--seed", str(seed), "--fuel-mult", str(self.fuel_mult),
                                      *self._games(seed, games)],
                                     capture_output=True, text=True, timeout=self.timeout)
                if out.returncode != 0:
                    return Result(error=f"genome_eval exit {out.returncode}: {out.stderr[-300:]}")
                stats = json.loads(out.stdout)
                if "error" in stats:
                    return Result(error=stats["error"])
                outcomes.append((stats.pop("results", None), stats["a_gems"], stats["b_gems"]))
                res.per_opponent[name] = stats
                res.score += score_of(stats) / len(self.opponents)
        except subprocess.TimeoutExpired:
            return Result(error="evaluation timed out")
        res.fingerprint = hashlib.sha256(json.dumps(outcomes).encode()).hexdigest()[:16]
        with self.lock:
            self.cache[key] = res
        return res

    def screen(self, text, kind):
        return self.evaluate(text, kind, self.screen_seed, self.screen_games)

    def confirm(self, text, kind):
        return self.evaluate(text, kind, self.confirm_seed, self.confirm_games)


def brief(res):
    """One line of results for prompts: win rate and gem margin per opponent."""
    return "; ".join(f"vs {n}: win {s['win_rate']:.2f}, gems {s['a_gems']:.0f}-{s['b_gems']:.0f}"
                     for n, s in res.per_opponent.items())
