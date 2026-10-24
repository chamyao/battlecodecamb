"""Confirm the top of the tune-5 constant grid (screen seed 9311) and the best pair: 2 x 400 fresh games vs tune-5
(seeds 9331/9332) plus the cambc80 check; the full gauntlet only for a > 52% survivor."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

base = open("policies/tune-5.policy").read()
bpol = compile_text(base)
J = ("let jungle_n = floor( rest_after_treasure / 2 )", "let jungle_n = floor( rest_after_treasure / 3 )")
R = ("round_number() > 1500", "round_number() > 1000")
Z = ("let jungle_n = floor( rest_after_treasure / 2 )", "let jungle_n = 0")
cands = {"jungle/3": [J], "baground1000": [R], "jungle0": [Z], "jungle/3+baground1000": [J, R]}
log = open("runs/tune/confirm-t5grid.log", "a")
for name, edits in cands.items():
    t = base
    for o, n in edits:
        assert t.count(o) == 1
        t = t.replace(o, n)
    pol = compile_text(t)
    hh = [h2h(pol, bpol, 400, s)["win_rate"] for s in (9331, 9332)]
    r = {"h2h": hh, "h2h_mean": sum(hh) / 2, "cambc80": h2h(pol, bpol, 80, 1, bot_seeds=True)["win_rate"]}
    if r["h2h_mean"] > 0.52:
        full = confirm(t, bpol, seeds=(9331, 9332), base_text=base, log=lambda s: None)
        r["gauntlet"] = full["gauntlet"]
    log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
