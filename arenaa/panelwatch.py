"""Panel milestones (panelwatch panel.jsonl): each milestone's genomes' total wins over the panel.

    python3 arenaa/panelwatch.py panel.jsonl
"""
import collections
import json
import sys

R = [json.loads(l) for l in open(sys.argv[1])]
opps = sorted({r["opponent"] for r in R if r["kind"] == "panel"})
w = collections.defaultdict(dict)
births = {}
for r in R:
    if r["kind"] == "snapshot":
        births[r["milestone"]] = r["births"]
    elif r["kind"] == "panel":
        w[(r["milestone"], r["genome"])][r["opponent"]] = r["wins"]
print(f"{len(opps)} opponents x 80 games = {80 * len(opps)}")
for (m, g), d in sorted(w.items()):
    full = len(d) == len(opps)
    print(f"  milestone {m:2d} (birth {births.get(m)}) {g:6s} {sum(d.values()):4d}{'' if full else f' (partial, {len(d)} opponents)'}")
