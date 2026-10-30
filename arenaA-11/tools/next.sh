#!/bin/bash
# wait for pending queue requests, list them, and print the editable genes of each mutate request
cd /home/user/battlecodecamb
Q=arenaA-11/queue
timeout 650 python3 -m genome.search.queuewait $Q --max ${1:-8} --timeout 600 > /tmp/qw.json
python3 -c "
import json,re;r=json.load(open('/tmp/qw.json'))
if isinstance(r,dict): print(r)
for q in r if isinstance(r,list) else []:
  u=q['user']; print(q['seq'], q['op'], q['parents'], re.findall(r'## Link\(s\) to mutate: (.*)', u)[:1] if q['op']=='mutate' else '', u.split('\n')[0][:80])
"
