# early_stop.py CP_FILE: how well the state at round R predicts the winner (lines "<tag> <genome_eval --checkpoints 50 JSON>")
import json, sys, collections
rows = collections.defaultdict(list)
for line in open(sys.argv[1]):
    tag, js = line.split(" ", 1)
    rows[tag].append(json.loads(js))
def lead(c, kind):
    r, ta, tb, ca, cb = c[:5]
    return (ta - tb) if kind == "trib" else (ta + ca - tb - cb)
for tag, gs in rows.items():
    uniq = len({json.dumps(g["cp"]) for g in gs})
    n = len(gs); rounds = sum(g["rounds"] for g in gs)
    reasons = collections.Counter(g["reason"] for g in gs)
    aw = sum((g["winner"] == 0) == (g["a_side"] == "A") for g in gs)
    print(f"\n== {tag}: {n} games ({uniq} distinct), A win rate {aw/n:.3f}, mean rounds {rounds/n:.0f}, end reasons {dict(reasons)}")
    print("  round  running  leader-wins(trib)  leader-wins(trib+carried)")
    for R in (200, 400, 600, 800, 1000, 1200, 1500):
        live = [g for g in gs if g["rounds"] > R]
        if not live: continue
        res = []
        for kind in ("trib", "all"):
            ok = tot = 0
            for g in live:
                c = next(c for c in g["cp"] if c[0] == R)
                d = lead(c, kind)
                if d == 0: continue
                tot += 1; ok += (d > 0) == (g["winner"] == 0)
            res.append(f"{ok/tot:.3f} ({tot})")
        print(f"  {R:5d}  {len(live)/n:6.2f}   {res[0]:>17}  {res[1]:>17}")
    # stop rule: first checkpoint >= R0 with |lead(all)| >= m -> call it for the leader
    print("  rule: stop at first 50-round checkpoint >= R0 with |trib+carried lead| >= m")
    print("    R0    m   stopped  wrong(of all)  rounds saved  A-winrate est (true)")
    for R0 in (200, 400, 600):
        for m in (50, 100, 150, 200, 300):
            wrong = stopped = saved = awe = 0
            for g in gs:
                call = None
                for c in g["cp"]:
                    if c[0] >= R0 and c[0] < g["rounds"] and abs(lead(c, "all")) >= m:
                        call = (0 if lead(c, "all") > 0 else 1, c[0]); break
                w = g["winner"]
                if call:
                    stopped += 1; wrong += call[0] != w; saved += g["rounds"] - call[1]; w = call[0]
                awe += (w == 0) == (g["a_side"] == "A")
            print(f"  {R0:5d} {m:4d}   {stopped/n:6.2f}   {wrong/n:8.3f}      {saved/rounds:6.2f}      {awe/n:.3f} ({aw/n:.3f})")
