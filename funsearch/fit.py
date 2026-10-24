"""Fitting fitness (style line): how closely a candidate opponent reproduces the real top teams' statistics against
each of our versions. Not a win-rate score: the run evolves an opponent whose SIM stats against every version match
the REAL stats, so all versions stay in the fit and no single bot is overfitted.

Target file (JSON), stats from the TOP TEAM's (candidate's) view against each version:
  {"versions": {"<name>": {"policy": "policies/<our version>.policy",
                           "stats": {"win": 1.0, "kills": 12.9, "opp_kills": 0.3, ...}}, ...},
   "scales":  {"<stat>": <normaliser>, ...},     optional, overrides DEFAULT_SCALES
   "weights": {"<stat>": <weight>, ...}}         optional, default 1 for every stat present in the target
Stats available from the sim (funsearch/fights.py summary): win, gems, opp_gems, kills, opp_kills, champ_dmg,
opp_champ_dmg, first_kill_round, fight_score, engagements, opp_out_death_share. Stats in the target that the sim
does not produce are ignored (listed as "unmatched").

distance = sqrt(mean over versions and stats of weight * ((sim - real) / scale)^2); fitness = 1 / (1 + distance).
usage: python3 -m funsearch.fit candidate.policy target.json [games per version] [seed]
"""
import json
import math
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from policygen.compile import to_prefix
from policygen.text import parse

from . import fights
from .evaluate import ROOT

# one "unit of misfit" per stat: roughly the spread between teams on the ladder
DEFAULT_SCALES = {"win": 0.1, "gems": 100.0, "opp_gems": 100.0, "kills": 2.0, "opp_kills": 1.0, "champ_dmg": 3000.0,
                  "opp_champ_dmg": 2000.0, "first_kill_round": 50.0, "fight_score": 0.1, "engagements": 3.0,
                  "opp_out_death_share": 0.1}


def load_target(path):
    t = json.loads(Path(path).read_text())
    for name, v in t["versions"].items():
        if not (ROOT / v["policy"]).exists():
            raise FileNotFoundError(f"target version {name}: {v['policy']} not found")
    return t


def _compile(path_or_text, is_text=False):
    text = path_or_text if is_text else Path(path_or_text).read_text()
    fd, out = tempfile.mkstemp(suffix=".pol", prefix="fit-")
    with os.fdopen(fd, "w") as f:
        f.write(to_prefix(parse(text)))
    return out


def distance(sim_by_version, target):
    scales = {**DEFAULT_SCALES, **target.get("scales", {})}
    weights = target.get("weights", {})
    terms, unmatched = [], set()
    for name, v in target["versions"].items():
        sim = sim_by_version[name]
        for stat, real in v["stats"].items():
            if stat not in sim or stat not in scales:
                unmatched.add(stat)
                continue
            w = weights.get(stat, 1.0)
            terms.append(w * ((sim[stat] - real) / scales[stat]) ** 2)
    return (math.sqrt(sum(terms) / len(terms)) if terms else float("inf")), sorted(unmatched)


def fit(candidate_text, target, games=40, seed=1, threads=5):
    """Play the candidate against every target version (in parallel, one single-threaded process each).
    Returns (fitness, distance, {version: sim summary}, unmatched stats)."""
    cand = _compile(candidate_text, is_text=True)
    opps = {name: _compile(ROOT / v["policy"]) for name, v in target["versions"].items()}
    try:
        with ThreadPoolExecutor(max_workers=max(1, threads)) as ex:
            futs = {name: ex.submit(fights.play, cand, pol, games, seed) for name, pol in opps.items()}
            sim = {name: f.result()["summary"] for name, f in futs.items()}
    finally:
        for p in [cand, *opps.values()]:
            Path(p).unlink(missing_ok=True)
    d, unmatched = distance(sim, target)
    return 1.0 / (1.0 + d), d, sim, unmatched


if __name__ == "__main__":
    cand, tgt = sys.argv[1], sys.argv[2]
    games = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    target = load_target(tgt)
    fitness, d, sim, unmatched = fit(Path(cand).read_text(), target, games, seed)
    print(f"{Path(cand).name}: fitness {fitness:.3f}, distance {d:.2f} ({games} games per version)")
    for name, v in target["versions"].items():
        cells = "  ".join(f"{s} {sim[name].get(s, float('nan')):.2f}/{r}" for s, r in v["stats"].items())
        print(f"  vs {name}: {cells}   (sim/real)")
    if unmatched:
        print("  unmatched target stats (no sim counterpart):", ", ".join(unmatched))
