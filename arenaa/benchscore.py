"""Bench children vs the anchors: child-minus-parent wins on the same 480 games, by prompt, vs the null.

    python3 arenaa/benchscore.py benchscore.jsonl
"""
import collections
import json
import sys

R = [json.loads(l) for l in open(sys.argv[1])]
G = collections.defaultdict(dict)
meta = {}
for r in R:
    if r["opponent"] == "parent":
        continue  # the 80 vs-parent games, not an anchor
    G[r["genome"]][r["opponent"]] = r["wins"]
    meta[r["genome"]] = r
par = {g.split("parent:", 1)[1]: d for g, d in G.items() if meta[g]["kind"] == "parent" and len(d) == 6}
rows = collections.defaultdict(list)
for g, d in G.items():
    m = meta[g]
    if m["kind"] not in ("child", "null") or len(d) < 6 or m["parent"] not in par:
        continue
    if m["kind"] == "child" and m.get("bench") == "promptbench-2" and m.get("prompt") in ("default", "temperament"):
        continue  # overwritten by the retest children (file-name bug)
    rows["null" if m["kind"] == "null" else m["prompt"]].append(
        (sum(d.values()) - sum(par[m["parent"]].values()), m.get("vs_parent_wins") or m.get("bench_wins")))
null = sorted(x for x, _ in rows.pop("null", []))
p95 = null[int(0.95 * len(null))] if null else None
print(f"null n={len(null)} p95={p95} values={null}")
for k, v in sorted(rows.items()):
    x = sorted(a for a, _ in v)
    mu = sum(x) / len(x)
    above = sum(a > p95 for a in x) if p95 is not None else None
    print(f"{k:12s} n={len(x):3d} mean {mu:+6.1f} median {x[len(x)//2]:+4d} p90 {x[int(.9*len(x))]:+4d} max {x[-1]:+4d} "
          f"above null p95: {above}  broken(<-100): {sum(a < -100 for a in x)}")
pairs = [(a, b) for v in rows.values() for a, b in v if b is not None]
if len(pairs) > 5:
    n = len(pairs); ma = sum(a for a, _ in pairs) / n; mb = sum(b for _, b in pairs) / n
    cov = sum((a - ma) * (b - mb) for a, b in pairs); va = sum((a - ma) ** 2 for a, _ in pairs); vb = sum((b - mb) ** 2 for _, b in pairs)
    print(f"corr(vs-parent wins, anchor diff) over {n} children: {cov / (va * vb) ** .5:.2f}")
