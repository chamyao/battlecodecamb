#!/bin/bash
# next batch: wait, then compact view of every pending request
cd /home/user/battlecodecamb/arenaA-11
bash tools/next.sh ${1:-8} ${2:-60} > /tmp/next.txt
grep "done" /tmp/next.txt
python3 tools/v.py $(python3 -c "import json;r=json.load(open('/tmp/qw.json'));print(' '.join(str(q['seq']) for q in r) if isinstance(r,list) else '')")
tail -1 arena/log.txt | cut -c1-250
