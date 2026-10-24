"""Confirm the starvation fixes on fresh seeds: monolith fallback after round 800, optionally plus threat banking
(T = 240). Full gauntlet vs tune-3 plus per-map (starvation, hooks, stampede, pilgrimage, shortcut) for the
candidate and for tune-3 itself."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.mono_fix import mono
from funsearch.threat_bank import threat_bank

base = open("policies/tune-3.policy").read()
bpol = compile_text(base)
r800 = mono(base, "round_number() > 800")
cands = {"tune-3": base, "r800": r800, "r800+T240": threat_bank(r800, 240)}
opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
log = open("runs/tune/starvconfirm.log", "a")
for name, t in cands.items():
    open(f"runs/tune/cand-{name}.policy", "w").write(t)
    pol = compile_text(t)
    r = {}
    if name != "tune-3":
        r = confirm(t, bpol, seeds=(9021, 9022), base_text=base, log=lambda s: None)
    for m in ("01starvation", "01hooks", "00stampede", "00pilgrimage", "01shortcut"):
        for on, op in opps.items():
            s = play(pol, op, f"maps/{m}.map26a", 60, 33)
            r[f"{m}/{on}"] = [s["wins"], s["gems"]]
    log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
