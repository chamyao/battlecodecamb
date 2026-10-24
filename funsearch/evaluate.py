"""Score a policy by playing it in the simulator (interp/build/interp_eval)."""
import json
import os
import random
import re
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


# map sampling (funsearch.run --screen-maps): "random" draws maps with replacement (the original screens: a fixed
# seed gives every child the same ~28 of 40 maps for 48 slots); "cover" walks seeded shuffles of the whole pool, so
# an opponent with >= 80 games plays every map on both sides and smaller ones get distinct maps
MAP_MODE = "random"


def _choose_maps(rng, pool, slots):
    if MAP_MODE != "cover":
        return [rng.choice(pool) for _ in range(slots)]
    out = []
    while len(out) < slots:
        perm = list(pool)
        rng.shuffle(perm)
        out += perm
    return out[:slots]


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
    # "spec@w" weights an opponent: w times the games and w times the share of the score
    weights = [float(o.rsplit("@", 1)[1]) if "@" in o else 1.0 for o in opponents]
    opponents = [o.rsplit("@", 1)[0] if "@" in o else o for o in opponents]
    names = [Path(o).stem if o.endswith(".policy") else o for o in opponents]
    try:
        opponents = [_compiled_opponent(o) for o in opponents]
    except Exception as e:  # opponent policy no longer parses: a setup error, not the candidate's
        raise RuntimeError(f"opponent failed to compile: {e}") from e
    rng = random.Random(seed)
    pool = maps or MAPS
    counts = [max(2, round(games * w / 2) * 2) for w in weights]  # even, so sides stay balanced
    chosen = _choose_maps(rng, pool, max(counts) // 2)
    with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
        f.write(prefix)
        pol = f.name
    try:
        result = EvalResult(score=0.0)
        for name, opp, w, n in zip(names, opponents, weights, counts):
            out = subprocess.run(
                [str(EVAL_BIN), "--a", pol, "--b", opp, "--games", str(n), "--threads", str(threads),
                 "--seed", str(seed), "--fuel-mult", str(fuel_mult), *chosen[: n // 2]],
                capture_output=True, text=True, timeout=timeout)
            stats = json.loads(out.stdout)
            if "error" in stats:
                return EvalResult(error=stats["error"])
            stats.pop("results", None)
            result.per_opponent[name] = stats
            result.score += score_of(stats) * w / sum(weights)
        return result
    except subprocess.TimeoutExpired:
        return EvalResult(error="evaluation timed out")
    finally:
        Path(pol).unlink(missing_ok=True)


FUEL_BIN = EVAL_BIN.with_name("fuel_turns")
FUEL_MAPS = ("01big-world", "00ambush")  # the maps where heavy turns hit the 100k cap first


def fuel_check(text, opp_text, maps=FUEL_MAPS, threshold=90_000, timeout=300):
    """Real-budget fuel check (fuel_turns --enforce --bot-seeds, both sides of each map vs opp_text): returns
    {suspensions, heavy_turns} per game (heavy = turns at or above `threshold` fuel, first turns included, as for
    the live bot), or None on error."""
    try:
        pols = []
        for t in (text, opp_text):
            with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
                f.write(to_prefix(parse(t)))
                pols.append(f.name)
    except Exception:
        return None
    susp = heavy = games = 0
    try:
        for m in maps:
            for side in ("a", "b"):
                out = subprocess.run([str(FUEL_BIN), pols[0], str(ROOT / "maps" / f"{m}.map26a"), "--enforce",
                                      "--bot-seeds", "--side", side, "--opp", pols[1]],
                                     capture_output=True, text=True, timeout=timeout)
                ms = re.search(r"suspensions (\d+)", out.stderr)
                if not ms:
                    return None
                susp += int(ms.group(1))
                heavy += sum(1 for l in out.stdout.splitlines() if l.split() and int(l.split()[1]) >= threshold)
                games += 1
        return dict(suspensions=round(susp / games, 2), heavy_turns=round(heavy / games, 1))
    except Exception:
        return None
    finally:
        for f in pols:
            Path(f).unlink(missing_ok=True)


EXEC_OPP = "starter"  # opponent of executed_blocks; logged as metrics.exec_opp


def refresh_exec_blocks(rows, cache_path, threads=8):
    """Executed blocks vs builtin:starter for every valid row, {id: sorted names}: from metrics when measured
    vs starter (metrics.exec_opp), else from the cache file, else computed now (in parallel) and cached. Rows
    are programs.jsonl dicts. Rows measured vs builtin:idle (before exec_opp) are recomputed."""
    from concurrent.futures import ThreadPoolExecutor
    cache_path = Path(cache_path)
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    out, todo = {}, []
    for r in rows:
        if r.get("error") is not None or r.get("score") is None or r["score"] == float("-inf"):
            continue
        m = r.get("metrics") or {}
        if m.get("exec_opp") == EXEC_OPP and "exec_blocks" in m:
            out[r["id"]] = m["exec_blocks"]
        elif str(r["id"]) in cache:
            out[r["id"]] = cache[str(r["id"])]
        else:
            todo.append(r)
    if todo:
        with ThreadPoolExecutor(threads) as ex:
            for r, b in zip(todo, ex.map(lambda r: executed_blocks(r["text"]), todo)):
                cache[str(r["id"])] = out[r["id"]] = sorted(b) if b is not None else []
        cache_path.write_text(json.dumps(cache))
    return out


def executed_blocks(text, games=4, seed=0, timeout=120):
    """Blocks a policy actually executes (interp_eval --block-hits) in a few games against builtin:starter,
    which runs no blocks, so every hit is the policy's (builtin:idle never comes into view, so blocks that need a
    visible enemy never ran against it). Returns a set of block names, or None on error."""
    try:
        prefix = to_prefix(parse(text))
    except Exception:
        return None
    rng = random.Random(seed)
    chosen = [rng.choice(MAPS) for _ in range(games // 2)]
    with tempfile.NamedTemporaryFile("w", suffix=".pol", delete=False) as f:
        f.write(prefix)
        pol = f.name
    try:
        out = subprocess.run([str(EVAL_BIN), "--a", pol, "--b", "builtin:starter", "--games", str(games), "--threads", "1",
                              "--seed", str(seed), "--block-hits", *chosen], capture_output=True, text=True, timeout=timeout)
        hits = json.loads(out.stdout.strip().splitlines()[-1]).get("block_hits", {})
        return {k.split("(", 1)[0] for k, v in hits.items() if v > 0}
    except Exception:
        return None
    finally:
        Path(pol).unlink(missing_ok=True)
