"""v.py SEQ...: compact view of queue requests: link and editable genes; genes identical to v39a's are collapsed."""
import json, re, sys
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
R = '/home/user/battlecodecamb/arenaA-11'
_, _, V = edit.segments(open(f'{R}/seeds/v39a.genome').read())
for s in sys.argv[1:]:
    q = json.load(open(f'{R}/queue/req-{s}.json')); u = q['user']
    print(f"##### {q['seq']} {q['op']} {q['parents']} | {u.splitlines()[0][:70]}")
    if '## Link' not in u:
        print(u[-3000:]); continue
    print('\n'.join(re.findall(r'## Link\(s\) to mutate: .*', u)))
    for blk in re.findall(r'## EDITABLE gene \w+.*?\n```python\n(.*?)```', u, re.S):
        gid = re.search(r"@gene\(['\"]([^'\"]+)['\"]", blk).group(1)
        name = re.search(r'def (\w+)', blk).group(1)
        if gid in V and edit.body_canon(V[gid]) == edit.body_canon(blk) and len(blk) > 600:
            print(f'--- {name} [{gid}] = v39a ({len(blk)} chars)')
        else:
            print(blk.strip())
