#!/bin/bash
# solo4.sh BOT OUTDIR: BOT vs the genome idle bot on every map, both sides; prints map side rounds gems
bot=$1; out=$2; rm -rf $out; mkdir -p $out
C=/tmp/claude-0/cambc4/bin/cambc
run() { m=$1; s=$2; d=$out/$m-$s
  if [ $s = A ]; then $C run $bot gidle --release --map maps/$m.map26a -o $d > $d.log 2>&1
  else $C run gidle $bot --release --map maps/$m.map26a -o $d > $d.log 2>&1; fi; }
export -f run; export bot out C
cd ~/ws4 && $C build $bot --release >/dev/null 2>&1 && $C build gidle --release >/dev/null 2>&1
ls maps/*.map26a | xargs -n1 basename | sed 's/.map26a//' | while read m; do echo "$m A"; echo "$m B"; done | xargs -P 4 -n 2 bash -c 'run "$0" "$1"'
for f in $out/*.log; do r=$(grep -oE "in round [0-9]+" $f | head -1 | grep -oE "[0-9]+"); echo "$(basename $f .log) ${r:-2000}"; done > $out/rounds.txt
