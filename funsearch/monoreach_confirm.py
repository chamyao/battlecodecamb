"""Map-fix confirm of the monolith-reach goal filter (monoreach.py): reach5 alone and stacked on the starvation fixes
(r800 + T240, as t5-starv in t5_mapfix.py), vs tune-5: 2 x 400 fresh (seeds 9361/9362), gauntlet, cambc80, maps lost
on both sides, and per-map on 00lost-world / 01starvation vs the stand-ins."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.mono_fix import mono
from funsearch.threat_bank import threat_bank
from funsearch.altar_bag import lost_both_sides
from funsearch.monoreach import reach

base = open("policies/tune-5.policy").read()
bpol = compile_text(base)
cands = {"t5-reach5": reach(base), "t5-starv+reach5": reach(threat_bank(mono(base, "round_number() > 800"), 240))}
only = set(sys.argv[1:])
opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
log = open("runs/tune/monoreach_confirm.log", "a")
for name, t in cands.items():
    if only and name not in only:
        continue
    open(f"runs/tune/cand-{name}.policy", "w").write(t)
    pol = compile_text(t)
    r = confirm(t, bpol, seeds=(9361, 9362), base_text=base, log=lambda s: None)
    r["lost_both"] = lost_both_sides(h2h(pol, bpol, 80, 1, bot_seeds=True)["results"])
    for m in ("00lost-world", "01starvation"):
        for on, op in opps.items():
            a = play(pol, op, f"maps/{m}.map26a", 30, 71)
            r[f"{m}/{on}"] = [a["wins"], a["gems"]]
    line = f"{name}: {json.dumps(r)}"
    print(line, flush=True); log.write(line + "\n"); log.flush()
