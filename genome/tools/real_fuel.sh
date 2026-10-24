#!/bin/bash
# real.sh GENOME MAP: plain (unprofiled) genome bot vs starter-cpp in cambc; per-turn real fuel summary
cd /home/user/battlecodecamb
genome/bot/sync.sh "$1" ~/ws/bots/greal-$(basename $1 .genome)-$2 >/dev/null
out=/tmp/claude-0/real-$(basename $1 .genome)-$2; rm -rf $out
(cd ~/ws && timeout 1200 cambc run greal-$(basename $1 .genome)-$2 starter-cpp --release --map maps/$2.map26a -o $out > $out.log 2>&1) || tail -3 $out.log
echo "$(basename $1) $2: $(grep -E "greal" $out.log | head -1 | awk '{print "gems",$3}') $(python3 oracle/tools/fuel_file.py $out/*.repl26a team-a | tail -1)"
