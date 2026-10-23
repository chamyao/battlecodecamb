#!/bin/bash
# Play the deploy bot (bot/) against an opponent on one map and summarise per-turn fuel.
# Usage: bot/tools/run.sh MAP [OPPONENT] [OUTDIR] [extra cambc args...]
set -e
m=$1; opp=${2:-starter-cpp}; out=${3:-/tmp/runs/$m}
shift $(( $# < 3 ? $# : 3 ))
repo=$(cd "$(dirname "$0")/../.." && pwd)
ln -sfn "$repo/bot" ~/ws/bots/deploy
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
rm -rf "$out" && mkdir -p "$out"
(cd ~/ws && cambc run deploy "$opp" --release --map maps/$m.map26a -o "$out" "$@" > "$out/log.txt" 2>&1) || { tail -5 "$out/log.txt"; exit 1; }
grep -E "wins|crash|deploy " "$out/log.txt" | tail -3
python3 "$repo/oracle/tools/fuel_file.py" "$out"/*.repl26a team-a | tail -1
