#!/bin/bash
# prof_pair.sh GENOME MAP [OUT]: the genome built with GENOME_PROF, team A vs starter, in cambc (real fuel)
# and in the simulator (sim prices) on one map; profile lines (@@GENE / @@FIELD / @@P) to OUT/{real,sim}.txt.
# SIM_ONLY=1 re-runs only the simulator side. Needs genome/build-prof (cmake -S genome -B genome/build-prof -DCMAKE_CXX_FLAGS=-DGENOME_PROF).
set -euo pipefail
cd "$(dirname "$0")/../.."
g=$1; map=$2; name=$(basename "$g" .genome)-$map
out=${3:-/tmp/claude-0/prof/$name}; mkdir -p "$out"
[ -n "${SIM_ONLY:-}" ] || { GENOME_DEFS="GENOME_PROF ${PROF_DEFS:-}" genome/bot/sync.sh "$g" ~/ws/bots/gp-$name >/dev/null
rm -rf "$out/replay"
(cd ~/ws && timeout 1800 cambc run gp-$name starter-cpp --release --map maps/$map.map26a -o "$out/replay" --log-limit 50000000 > "$out/cambc.log" 2>&1) || tail -3 "$out/cambc.log"
unzip -p "$out"/replay/*.repl26a team-a.stdout | tr -d '\000' | grep -a '^@@' > "$out/real.txt" || true
python3 oracle/tools/fuel_file.py "$out"/replay/*.repl26a team-a | tail -1 > "$out/real_turns_summary.txt"; }  # SIM_ONLY=1: keep the real run
so=$(GENOME_DEFS="GENOME_PROF ${PROF_DEFS:-}" python3 -m genome.build "$g")
GENOME_TURN_FUEL=$out/sim_turns.txt genome/build-prof/genome_eval --a genome:$so --b builtin:starter --games 1 --threads 1 maps/$map.map26a 2>/dev/null | grep -a '^@@' > "$out/sim.txt" || true
echo "$name: real $(wc -l < "$out/real.txt") sim $(wc -l < "$out/sim.txt") lines; $(cat "$out/real_turns_summary.txt")"
