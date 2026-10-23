#!/bin/bash
# Profile the deploy bot's policy blocks in real fuel (no fuel cap) on one map.
# Usage: bot/tools/profile.sh MAP [POLICY]; prints the top blocks by total exclusive fuel.
set -e
repo=$(cd "$(dirname "$0")/../.." && pwd)
m=$1; pol=${2:-$repo/policies/v2.policy}
bash "$repo/bot/sync.sh" "$pol" > /dev/null
python3 "$repo/bot/tools/profile_patch.py" "$repo/bot/src/vendor_interp_policy.cpp"
out=/tmp/prof/$m
"$repo/bot/tools/run.sh" "$m" starter-cpp "$out" --fuel 1000000000 --log-limit 2000000000 || true
bash "$repo/bot/sync.sh" "$pol" > /dev/null # restore the plain build
(cd "$out" && unzip -q -o *.repl26a && tr -d '\000' < team-a.stdout | grep "^@@" > prof.txt)
python3 - "$out/prof.txt" <<'PY'
import sys, collections
last = {}
T = []
for line in open(sys.argv[1]):
    f = line.split()
    if f[0] == "@@T" and len(f) == 4: T.append(int(f[3]))
    if f[0] == "@@P" and len(f) == 7:
        c, t = int(f[1]), int(f[2])
        last.setdefault(c, {})
        if t >= last[c].get("_t", 0):
            if t > last[c].get("_t", 0): last[c] = {"_t": t}
            last[c][f[3]] = (int(f[4]), int(f[5]), int(f[6]))
agg = collections.defaultdict(lambda: [0, 0, 0])
for c, d in last.items():
    for k, v in d.items():
        if k == "_t": continue
        n, tot, mx = v
        a = agg[k]; a[0] += n; a[1] += tot; a[2] = max(a[2], mx)
T.sort()
if T: print(f"policy pass per turn: n={len(T)} mean={sum(T)/len(T):.0f} p50={T[len(T)//2]} p99={T[int(len(T)*.99)]} max={T[-1]}")
for k, (n, tot, mx) in sorted(agg.items(), key=lambda kv: -kv[1][1])[:30]:
    print(f"{k:34s} n={n:7d} avg={tot/n:8.0f} max={mx:7d} total={tot}")
PY
