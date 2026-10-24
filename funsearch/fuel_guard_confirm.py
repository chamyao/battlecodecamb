import json, sys
sys.path.insert(0, '.')
from funsearch.fuel_guard import *
base = open("policies/tune-2.policy").read(); bpol = compile_text(base)
for name, text in [("tune-2", base), ("goal-50000", guard(base, 50000, "goal")), ("goal-55000", guard(base, 55000, "goal")), ("goal-60000", guard(base, 60000, "goal"))]:
    bw = big_world(compile_text(text), bpol, games=600, seed=41)
    open("runs/tune/fuel-guard3.log", "a").write(f"{name}: bigworld600 wr {bw['win_rate']} susp {bw['a_suspensions']}\n")
