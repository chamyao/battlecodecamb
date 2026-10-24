"""Fuel safety check (bot session's bar: no 100k-cap turns, first turn < 200k) with interp/build/fuel_turns: per policy,
over maps x seeds x sides, the number of turns at or over 100k, over 80k, the max and mean per-turn fuel, and the
first turn's fuel. Opponent tune5-campreset, bot seeds, fuel enforced (so fuel_remaining() gates see real values; a capped turn is a suspension); the first 5 entries (each champion's
first turn, allowed up to 200k) are reported separately. usage: fuel_check.py MAP[,MAP] SEEDS POLICY..."""
import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *

maps, seeds = sys.argv[1].split(","), int(sys.argv[2])
OPP = compile_file("policies/tune5-campreset.policy")


def one(job):
    pol, mp, s, side = job
    out = subprocess.run([str(ROOT / "interp/build/fuel_turns"), pol, f"maps/{mp}.map26a", "--seed", str(s), "--side", side, "--bot-seeds", "--opp", OPP, "--enforce"],
                         capture_output=True, text=True, timeout=3600)
    v = [int(l.split()[1]) for l in out.stdout.split("\n") if len(l.split()) == 2 and l.split()[0].isdigit()]
    susp = sum(int(l.split("suspensions")[1]) for l in out.stderr.split("\n") if "suspensions" in l)
    return v, susp


for f in sys.argv[3:]:
    pol = compile_file(f)
    jobs = [(pol, m, s, side) for m in maps for s in range(1, seeds + 1) for side in "ab"]
    with ThreadPoolExecutor(4) as ex:
        runs = list(ex.map(one, jobs))
    susp = sum(x[1] for x in runs)
    runs = [x[0] for x in runs]
    allv = [x for v in runs for x in v[5:]]
    print(f"{f.split('/')[-1]:32s} games {len(runs)} turns {len(allv)} >=100k {sum(x >= 100000 for x in allv)} "
          f">80k {sum(x > 80000 for x in allv)} max {max(allv)} mean {sum(allv) / len(allv):.0f} "
          f"first-turns max {max(max(v[:5]) for v in runs if v)}", flush=True)
