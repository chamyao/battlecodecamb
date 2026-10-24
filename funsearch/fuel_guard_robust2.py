"""Re-check the tune-3 dash guard away from the typical fuel_remaining() at the dash check (~53-56k in the sim).

For each F: 01big-world as A vs tune-2 (600 per-game-seeded games), the cambc-exact 80 vs tune-2, 400 all-map games vs tune-2."""
import json, sys
sys.path.insert(0, '.')
from funsearch.fuel_guard import guard, big_world
from funsearch.race import *

base = open("policies/tune-2.policy").read()
bpol = compile_text(base)
log = open("runs/tune/fuel-guard4.log", "a")
for name, text in [(f"goal-{f}", guard(base, f, "goal")) for f in (60000, 70000)]:
    pol = compile_text(text)
    bw = big_world(pol, bpol, games=600, seed=61)
    chk = h2h(pol, bpol, 80, 1, bot_seeds=True)
    allm = h2h(pol, bpol, 400, 9011)
    r = {"bw600_wr": bw["win_rate"], "bw600_susp": bw["a_suspensions"], "cambc80": chk["win_rate"],
         "cambc80_susp": chk["a_suspensions"], "all400": allm["win_rate"], "all400_susp": allm["a_suspensions"]}
    log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
