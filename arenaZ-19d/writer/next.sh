#!/bin/bash
cd ~/z19 && python3 -m genome.search.queuewait ~/z19/queue --max 8 --timeout 600 > /tmp/qw.json
cd ~/w && python3 - <<'PY'
import sys,json,re; sys.path.insert(0,'/root/w')
import auto
d=json.load(open('/tmp/qw.json'))
if isinstance(d, dict): print(d); sys.exit()
for q in d:
    s=q['seq']; r=json.load(open(f'/root/z19/queue/req-{s}.json'))
    cross='mutate one link' not in r['system']
    cs = auto.cross_candidates(s) if cross else auto.candidates(s)
    print(s, r['parents'], 'CROSS' if cross else auto.editable(s), [c[0] for c in cs])
print('top5', r['feedback']['top5'])
PY
