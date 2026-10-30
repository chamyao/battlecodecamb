#!/bin/bash
# gate4.sh CAND REF : real cambc 4.0.0, all 70 maps x both sides, bots under ws4/bots. Prints CAND wins/140.
S=/tmp/claude-0/-home-user-battlecodecamb/ffe54acc-bdb7-57df-a68a-1cdbcfbc6770/scratchpad; W4=$S/cambc4/ws4; C=$S/cambc4/venv/bin/cambc
cand=$1; ref=$2; O=$S/cambc4/runs/$cand-vs-$ref; mkdir -p $O; rm -f $O/*.repl26a $O/manifest.txt
for m in $W4/maps/*.map26a; do n=$(basename $m .map26a)
  echo "$W4/bots/$cand $W4/bots/$ref $m $O/A-$n.repl26a" >> $O/manifest.txt
  echo "$W4/bots/$ref $W4/bots/$cand $m $O/B-$n.repl26a" >> $O/manifest.txt; done
(cd $W4 && $C run-batch --release --jobs 4 --timeout 1800 $O/manifest.txt > $O/batch.log 2>&1)
w=$(grep -c "WIN ($cand)" $O/batch.log); n=$(grep -c 'WIN\|DRAW' $O/batch.log); e=$(grep -i -c 'crash\|error\|panic\|fault' $O/batch.log)
old=$(grep "WIN ($cand)" $O/batch.log | grep -c -E ' 0[01][a-z]'); echo "$cand vs $ref: $w/$n (old-map wins $old/80), errors $e"
