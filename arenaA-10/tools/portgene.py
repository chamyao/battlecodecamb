"""portgene.py SEQ: print, for each editable gene of req SEQ, its v33-ported version (tools/port.py on the parent) if different."""
import json, re, sys, subprocess
sys.path.insert(0, '/root/a10w')
from genome.search import edit
q = json.load(open(f'/root/a10w/queue/req-{sys.argv[1]}.json')); u = q['user']
par = f"/root/a10w/runs/arenaA-10/arena/genomes/{q['parents'][0]}.genome"
r = subprocess.run(['python3', '/root/a10w/tools/port.py', par, '/tmp/pg.genome'], capture_output=True, text=True)
print('port:', r.stdout.strip()[:200], r.stderr.strip()[-200:])
_, _, g0 = edit.segments(open(par).read()); _, k1, g1 = edit.segments(open('/tmp/pg.genome').read())
for blk in re.findall(r'## EDITABLE gene \w+.*?\n```python\n(.*?)```', u, re.S):
    gid = re.search(r"@gene\(['\"]([^'\"]+)['\"]", blk).group(1)
    if gid in g1 and edit.body_canon(g0[gid]) != edit.body_canon(g1[gid]):
        print(f'--- PORTED {gid}:\n{g1[gid]}')
    else: print(f'--- {gid}: no port change')
