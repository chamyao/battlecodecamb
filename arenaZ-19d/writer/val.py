import sys, json, re, os
sys.path.insert(0, os.path.expanduser('~/z19'))
os.chdir(os.path.expanduser('~/z19'))
from genome.search import operators
from genome import build
Q = os.path.expanduser('~/z19/queue'); A = 'runs/arenaZ-19d/arena/genomes'
seq = sys.argv[1]; draft = open(sys.argv[2]).read()
write = '--write' in sys.argv
req = json.load(open(f'{Q}/req-{seq}.json'))
if 'mutate one link' in req['system']:
    ids = set(re.findall(r"## EDITABLE gene \S+ .*?\n```python\n@gene\(['\"]([^'\"]+)['\"]", req['user'], re.S))
    par = open(f"{A}/{req['parents'][0]}.genome").read()
    child, stats = operators.apply_mutation(par, draft, ids, 'zz')
    print('editable', ids, stats)
else:
    blocks = re.findall(r"```python\n(.*?)```", req['user'], re.S)
    class C:
        def ask(self, sysm, user): return draft, 'x', 0, {}
    c = operators.llm_cross(blocks[0], 0, blocks[1], 0, C(), 'zz')
    if c.source is None: raise SystemExit('CROSS ERROR ' + str(c.error))
    child = c.source
build.build(child)
print('BUILD OK')
open(os.path.expanduser(f'~/w/child-{seq}.genome'),'w').write(child)
if write:
    p = f'{Q}/rep-{seq}.txt'
    assert not os.path.exists(p)
    open(p + '.tmp','w').write(draft); os.rename(p + '.tmp', p); print('WROTE', p)
