#!/bin/bash
# acc.sh SEQ:K ... : rep-SEQ = rep-K (K=e: empty reply, K=x: llm cross auto graft)
cd /home/user/battlecodecamb/arenaA-11/queue
for p in "$@"; do s=${p%%:*}; k=${p##*:}
  if [ "$k" = e ]; then printf '```python\n```\n' > rep-$s.txt
  elif [ "$k" = x ]; then python3 ../tools/xover.py $s auto > /dev/null
  else cp rep-$k.txt rep-$s.txt; fi
done
