"""Gems tributed per game (the score) and win rate per opponent, for the v20 ward-rule question (FunSearch lead: v20's
ladder gems fell 260 -> 189 vs the top teams). Policies v19, v20, tune-v19-L1c, tune-v20-L1c vs hunter3, hunter2b and
the four stand-ins (400 games each, seed 9561), plus 00quadrants alone (40 per-game-seeded games each)."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

POLS = {"v19": "policies/tune-v19.policy", "v20": "policies/tune-v20.policy",
        "v19-L1c": "policies/candidates/tune-v19-L1c.policy", "v20-L1c": "policies/candidates/tune-v20-L1c.policy"}
OPPS = ["opp-hunter3", "opp-hunter2b", "opp-icecream", "opp-odyssey", "opp-metab", "opp-metadraft"]
comp = {k: compile_file(v) for k, v in POLS.items()}
opps = {o: compile_file(f"policies/{o}.policy") for o in OPPS}
import subprocess
for k, p in comp.items():
    row = []
    for o, q in opps.items():
        r = h2h(p, q, 400, 9561, threads=2)
        row.append(f"{o[4:]} w{r['win_rate']:.3f} g{r['a_gems']:.0f}")
        out = subprocess.run([str(EVAL_BIN), "--a", p, "--b", q, "--games", "40", "--threads", "2", "--seed", "9562",
                              "maps/00quadrants.map26a"], capture_output=True, text=True).stdout.strip().splitlines()[-1]
        qd = json.loads(out)
        row.append(f"quad w{qd['win_rate']:.2f} g{qd['a_gems']:.0f}")
    print(k, " | ".join(row), flush=True)
