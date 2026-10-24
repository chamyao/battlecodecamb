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
                 threads=2, maps=None, timeout=900, fuel_mult=1.0, bot_seeds=False, fitness="score"):
        self.screen_games, self.confirm_games = screen_games, confirm_games
        self.screen_seed, self.confirm_seed = screen_seed, confirm_seed
        self.threads, self.maps, self.timeout = threads, maps or MAPS, timeout
        self.bot_seeds = bot_seeds  # policies seeded per instance as deployed (then every game is fixed by map and side)
        self.fuel_mult = fuel_mult  # scales every bot's per-turn fuel (both sides); 1.0 = the real game
        self.fitness = fitness  # "score": win rate + gem-margin bonus; "wins": win rate only
        self.lock = threading.Lock()
        self.cache = {}
        self.tmp = Path(tempfile.mkdtemp(prefix="gsearch-"))
        self.set_opponents(opponents)

    def set_opponents(self, opponents):
        """Opponent specs, each optionally weighted as `spec@w` (default 1). The score is the weighted mean."""
        specs, weights = [], []
        for o in opponents:
            spec, _, w = o.rpartition("@") if "@" in o and o.rsplit("@", 1)[1].replace(".", "").isdigit() else (o, "", "1")
            specs.append(spec)
            weights.append(float(w))
        with self.lock:
            self.opponents = [self._spec(o) for o in specs]
            self.opp_names = [Path(o).stem if not o.startswith("builtin:") else o for o in specs]
            self.weights = weights
            self.pool_key = hashlib.sha256(json.dumps([self.opponents, weights]).encode()).hexdigest()[:12]

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
        if self.bot_seeds and games >= 2 * len(self.maps):  # every game is fixed by map and side: all of them, once
            return sorted(self.maps)
        rng = random.Random(seed)
        return [rng.choice(self.maps) for _ in range(max(1, games // 2))]

    def evaluate(self, text, kind, seed, games):
        key = (hashlib.sha256(text.encode()).hexdigest(), kind, seed, games, self.pool_key, self.fuel_mult)
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
            for opp, name, w in zip(self.opponents, self.opp_names, self.weights):
                stats = self.play(a, opp, seed, games)
                if "error" in stats:
                    return Result(error=stats["error"])
                outcomes.append((stats.pop("results", None), stats["a_gems"], stats["b_gems"]))
                res.per_opponent[name] = stats
                fit = stats["win_rate"] if self.fitness == "wins" else score_of(stats)
                res.score += w * fit / sum(self.weights)
        except subprocess.TimeoutExpired:
            return Result(error="evaluation timed out")
        res.fingerprint = hashlib.sha256(json.dumps(outcomes).encode()).hexdigest()[:16]
        with self.lock:
            self.cache[key] = res
        return res

    def play(self, a, b, seed, games, threads=None, maps=None):
        """One genome_eval call between two side specs; returns its JSON stats (or {"error": ...}).
        Game g plays map (g / 2) % len(maps), A on side g % 2: with maps given and games = 2 * len(maps),
        every map once from each side."""
        out = subprocess.run([str(EVAL), "--a", a, "--b", b, "--games", str(games), "--threads",
                              str(threads or self.threads), "--seed", str(seed), "--fuel-mult", str(self.fuel_mult),
                              *(["--bot-seeds"] if self.bot_seeds else []), *(maps or self._games(seed, games))],
                             capture_output=True, text=True, timeout=self.timeout)
        if out.returncode != 0:
            return {"error": f"genome_eval exit {out.returncode}: {out.stderr[-300:]}"}
        return json.loads(out.stdout)

    def screen(self, text, kind):
        return self.evaluate(text, kind, self.screen_seed, self.screen_games)

    def confirm(self, text, kind):
        return self.evaluate(text, kind, self.confirm_seed, self.confirm_games)


def brief(res):
    """One line of results for prompts: win rate and gem margin per opponent."""
    return "; ".join(f"vs {n}: win {s['win_rate']:.2f}, gems {s['a_gems']:.0f}-{s['b_gems']:.0f}"
                     for n, s in res.per_opponent.items())
