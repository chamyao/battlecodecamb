#!/bin/bash
# gate4.sh BOT OPP OUTDIR: cambc 4.0.0 (engine 2.0.0), every map in ~/ws4/maps x both sides, 4 at a time
bot=$1; opp=$2; out=$3; rm -rf $out; mkdir -p $out
C=/tmp/claude-0/cambc4/bin/cambc
run() { m=$1; side=$2; d=$out/$m-$side
  if [ $side = A ]; then $C run $bot $opp --release --map maps/$m.map26a -o $d > $d.log 2>&1
  else $C run $opp $bot --release --map maps/$m.map26a -o $d > $d.log 2>&1; fi; }
export -f run; export bot opp out C
cd ~/ws4 && $C build $bot --release >/dev/null 2>&1 && $C build $opp --release >/dev/null 2>&1 && ls maps/*.map26a | xargs -n1 basename | sed 's/.map26a//' | while read m; do echo "$m A"; echo "$m B"; done | xargs -P 4 -n 2 bash -c 'run "$0" "$1"'
