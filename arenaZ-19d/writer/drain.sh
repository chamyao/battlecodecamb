#!/bin/bash
# drain.sh LOG seq1 seq2 ...: write each seq's best as soon as its BEST line appears
LOG=$1; shift
for s in "$@"; do
  until [ -f ~/w/d/$s.best ] && grep -q "BEST" <(sed -n "/== $s/,/BEST/p" $LOG); do sleep 3; done
  ~/w/wbest.sh $s
done
