import json, glob, os
ch = {}
for l in open('/root/z19/runs/arenaZ-19d/arena/children.jsonl'):
    d = json.loads(l); ch[d['seq']] = d
for f in sorted(glob.glob('/root/z19/queue/req-*.json'), key=lambda f: int(f.split('-')[-1][:-5])):
    r = json.load(open(f)); c = ch.get(r['child_seq'])
    if c: print(r['seq'], r['op'], r['parents'], '->', c.get('name'), c.get('error') or '', c.get('twin_of') or '')
