#!/bin/bash
# game_fuel.sh GENOME MAP: one game, genome as team A vs starter, in cambc (real fuel, plain bot) and in the
# simulator; mean fuel per champion turn and turns at the 100k cap, real / sim. Output in /tmp/claude-0/gf/.
set -euo pipefail
cd "$(dirname "$0")/../.."
g=$1; map=$2; name=$(basename "$g" .genome)-$map; out=/tmp/claude-0/gf/$name; mkdir -p "$out"
if [ -z "${SIM_ONLY:-}" ]; then
	genome/bot/sync.sh "$g" ~/ws/bots/gf-$name >/dev/null
	rm -rf "$out/replay"
	(cd ~/ws && timeout 1800 cambc run gf-$name starter-cpp --release --map maps/$map.map26a -o "$out/replay" > "$out/cambc.log" 2>&1) || tail -3 "$out/cambc.log"
fi
so=$(python3 -m genome.build "$g")
GENOME_TURN_FUEL=$out/sim_turns.txt genome/build/genome_eval --a genome:$so --b builtin:starter --games 1 --threads 1 maps/$map.map26a > "$out/sim.json"
python3 - "$out" "$name" <<'PY'
import sys, glob
sys.path.insert(0, 'oracle/tools'); import fuel_file
out, name = sys.argv[1], sys.argv[2]
_, used = fuel_file.turns(glob.glob(f'{out}/replay/*.repl26a')[0], 'team-a')
real = used[5:]
sim = [int(v) for v in open(f'{out}/sim_turns.txt').readline().split()]
f = lambda v: f"{sum(v)/len(v)/1000:.1f}k cap {sum(x >= 100000 for x in v)}"
print(f"{name}: real {f(real)} / sim {f(sim)}  ratio {sum(sim)/len(sim)/(sum(real)/len(real)):.2f}  turns {len(real)}/{len(sim)}")
PY
