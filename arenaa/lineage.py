"""Lineage curve and gene ablation from lineage-A's lineage.jsonl (13-opponent panel, 80 games each).

    python3 arenaa/lineage.py lineage.jsonl births.jsonl A659 A711
"""
import collections
import json
import sys

R = [json.loads(l) for l in open(sys.argv[1])]
B = {json.loads(l)["name"]: json.loads(l) for l in open(sys.argv[2])}
w = collections.defaultdict(dict)
meta = {}
for r in R:
    w[r["genome"]][r["opponent"]] = r["wins"]
    meta[r["genome"]] = r
opps = sorted(w["seed"])


def tot(g):
    return sum(w[g][o] for o in opps) if len(w[g]) == len(opps) else None


s = tot("seed")
print(f"{len(opps)} opponents, {80 * len(opps)} games; seed {s}")
for tip in sys.argv[3:]:
    line, x = [], tip
    while x in B and B[x]["parents"]:
        line.append(x)
        x = B[x]["parents"][0]
    prev, steps = s, []
    print(f"\n{tip}: main line, total minus seed, step")
    for g in reversed(line):
        t = tot(g)
        if t is None:
            continue
        steps.append(t - prev)
        print(f"  {g:6s} {B[g]['op']:7s} {t - s:+4d} {t - prev:+4d}")
        prev = t
    print(f"  steps: {sum(d > 0 for d in steps)} up, {sum(d < 0 for d in steps)} down, {sum(d == 0 for d in steps)} zero")
    b = tot(tip)
    abl = sorted((tot(g) - b, meta[g]["reverted"]) for g in w
                 if meta[g].get("base") == tip and meta[g]["kind"] == "ablation" and tot(g) is not None)
    print(f"  ablation (revert one gene to the seed's; change vs {tip}): {abl}")
