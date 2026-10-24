"""Per-map win rate of tune-5 vs the strongest gauntlet opponents (400 games each = 10 per map, seed 9341), to find
map-fix targets. Game g is map (g / 2) % 40."""
import json, sys, collections
sys.path.insert(0, '.')
from funsearch.race import *
t5 = compile_file("policies/tune-5.policy")
names = [m.split("/")[-1].split(".")[0] for m in MAPS]
tab = collections.defaultdict(dict)
for opp in ("v7zg-cast", "opp-icecream", "opp-odyssey", "opp-metab", "tune-2"):
    r = h2h(t5, compile_file(f"policies/{opp}.policy"), 400, 9341)["results"]
    w = collections.Counter(); n = collections.Counter()
    for g, x in enumerate(r):
        m = names[(g // 2) % 40]; w[m] += x; n[m] += 1
    for m in names:
        tab[m][opp] = w[m] / n[m]
    print(opp, r and sum(r) / len(r), flush=True)
rows = sorted(tab.items(), key=lambda kv: sum(kv[1].values()))
for m, d in rows:
    print(f"{m:24s} " + " ".join(f"{d[o]:.1f}" for o in d) + f"  mean {sum(d.values()) / len(d):.2f}")
json.dump(tab, open("runs/tune/t5_maps.json", "w"))
