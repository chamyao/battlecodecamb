#!/bin/bash
# Run the fuel probe bot (oracle/bots/fuelprobe) on a map; @@ lines go to /tmp/fp/MAP.txt.
# Usage: oracle/run_fuelprobe.sh MAP [ROUNDS]; then python3 oracle/tools/fuel_fit.py MAP...
set -e
m=$1; r=${2:-60}
repo=$(cd "$(dirname "$0")/.." && pwd)
ln -sfn "$repo/oracle/bots/fuelprobe" ~/ws/bots/fuelprobe
cd ~/ws
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
export CXXFLAGS="-I$repo/sim/include" # the probe compiles sim/src/bitboard.cpp into the bot
rm -rf /tmp/fp/$m.d && mkdir -p /tmp/fp/$m.d
cambc run fuelprobe starter-cpp --release --map maps/$m.map26a --rounds $r --fuel 1000000000 --log-limit 2000000000 -o /tmp/fp/$m.d/out.repl26a > /tmp/fp/$m.log 2>&1
cd /tmp/fp/$m.d && unzip -q -o out.repl26a/*.repl26a && tr -d '\000' < team-a.stdout | grep "^@@" > /tmp/fp/$m.txt
wc -l < /tmp/fp/$m.txt
