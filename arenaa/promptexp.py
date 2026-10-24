"""Prompt experiment 1: A0 vs A1, child-minus-parent wins vs the 6 anchors (480 games), paired on cells.

    python3 arenaa/promptexp.py scores.jsonl children.jsonl
"""
import collections
import json
import math
import sys

ANCH = ["style-gconv1", "tune-v20-L1", "rall2-ca4-lean-g", "v7", "opp-tune5-metadraft", "tune-v20-L1c"]
R = [json.loads(l) for l in open(sys.argv[1])]
C = [json.loads(l) for l in open(sys.argv[2])]
w = collections.defaultdict(dict)
meta = {}
for r in R:
    if r["opponent"] in ANCH:
        w[r["genome"]][r["opponent"]] = r["wins"]
        meta[r["genome"]] = r
done = lambda g: len(w[g]) == 6
par = {g.split("parent:", 1)[1]: sum(d.values()) for g, d in w.items() if meta[g]["kind"] == "parent" and done(g)}
null = sorted(sum(w[g].values()) - par[meta[g]["parent"]] for g in w
              if meta[g]["kind"] == "null" and done(g) and meta[g]["parent"] in par)
p95 = null[min(len(null) - 1, int(0.95 * len(null)))] if null else None
print(f"null n={len(null)} p95={p95}: {null}")
diff = {}
for g in w:
    m = meta[g]
    if m["kind"] == "child" and done(g) and m["parent"] in par:
        diff[(m["cell"], m["arm"])] = (sum(w[g].values()) - par[m["parent"]], m.get("type"))
fail = {(c["cell"], c["arm"]) for c in C if c.get("error")}
cells = sorted({c["cell"] for c in C})
for arm in ("A0", "A1"):
    x = sorted(d for (c, a), (d, _) in diff.items() if a == arm)
    nf = sum(1 for (c, a) in fail if a == arm)
    if x:
        print(f"{arm}: scored {len(x)}, failed {nf}; mean {sum(x)/len(x):+.1f} median {x[len(x)//2]:+d} "
              f"p90 {x[int(.9*len(x))]:+d} max {x[-1]:+d}; > p95: {sum(d > p95 for d in x)}; broken (< -50): {sum(d < -50 for d in x)}")
by = collections.defaultdict(list)
for (c, a), (d, t) in diff.items():
    if a == "A1":
        by[t].append(d)
for t, x in sorted(by.items()):
    x.sort()
    print(f"  A1 {t}: n {len(x)} mean {sum(x)/len(x):+.1f} max {x[-1]:+d} > p95 {sum(d > p95 for d in x)} broken {sum(d < -50 for d in x)}")
# paired McNemar on cells where both arms are decided (scored or failed)
better = lambda c, a: (c, a) in diff and diff[(c, a)][0] > p95
dec = [c for c in cells if all(((c, a) in diff) or ((c, a) in fail) for a in ("A0", "A1"))]
b01 = sum(1 for c in dec if better(c, "A1") and not better(c, "A0"))
b10 = sum(1 for c in dec if better(c, "A0") and not better(c, "A1"))
n = b01 + b10
p = sum(math.comb(n, k) for k in range(b01, n + 1)) / 2 ** n if n else 1.0
print(f"paired cells decided {len(dec)}: A1-only better {b01}, A0-only better {b10}, one-sided exact p = {p:.3f}")
