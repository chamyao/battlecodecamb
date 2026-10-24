"""Rebase the map fixes on tune-5 (live ladder v16): the two starvation fixes (monolith fallback after round 800 +
threat banking T240, i.e. tune-6's edits on tune-3) and the altar-count bag (01hooks), alone and together.
Each candidate gets the full confirm vs tune-5 (2 x 400 fresh seeds 9027/9028, gauntlet, cambc80) plus the maps
lost on both sides in cambc80, and per-map results vs the stand-ins; tune-5 itself is logged per map as the baseline.
Map-fix bar: >= 49% over 2 x 400, >= 40/80 cambc80, no map lost on both sides, clear gain on the target maps."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.mono_fix import mono
from funsearch.threat_bank import threat_bank
from funsearch.altar_bag import altar_bag, lost_both_sides

base = open("policies/tune-5.policy").read()
bpol = compile_text(base)
starv = threat_bank(mono(base, "round_number() > 800"), 240)
cands = {"tune-5": base, "t5-starv": starv, "t5-alt1": altar_bag(base, 2), "t5-alt2": altar_bag(base, 3),
         "t5-starv+alt1": altar_bag(starv, 2), "t5-starv+alt2": altar_bag(starv, 3)}
only = set(sys.argv[1:])
opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
log = open("runs/tune/t5mapfix.log", "a")
for name, t in cands.items():
    if only and name not in only:
        continue
    open(f"runs/tune/cand-{name}.policy", "w").write(t)
    pol = compile_text(t)
    r = {}
    if name != "tune-5":
        r = confirm(t, bpol, seeds=(9027, 9028), base_text=base, log=lambda s: None)
        r["lost_both"] = lost_both_sides(h2h(pol, bpol, 80, 1, bot_seeds=True)["results"])
    for m in ("01starvation", "01hooks", "00stampede", "00pilgrimage", "01shortcut"):
        for on, op in opps.items():
            s = play(pol, op, f"maps/{m}.map26a", 60, 35)
            r[f"{m}/{on}"] = [s["wins"], s["gems"]]
    log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
