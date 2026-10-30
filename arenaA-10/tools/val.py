"""val.py SEQ REPLYFILE [--write] [--out child.genome]: validate a reply for queue req SEQ; optionally write rep-SEQ.txt."""
import json, re, sys, os
sys.path.insert(0, os.path.expanduser('~/a10w'))
from genome.search import operators, edit
from genome import build, lang
Q = os.path.expanduser('~/a10w/queue'); G = os.path.expanduser('~/a10w/runs/arenaA-10/arena/genomes')
seq, rf = sys.argv[1], sys.argv[2]
q = json.load(open(f'{Q}/req-{seq}.json')); reply = open(rf).read()
src = lambda n: open(f'{G}/{n}.genome').read()
if q['op'] == 'mutate':
    u = q['user']
    ids = set()
    for blk in re.findall(r'## EDITABLE gene \w+.*?\n```python\n(.*?)```', u, re.S):
        m = re.search(r"@gene\(['\"]([^'\"]+)['\"]", blk); ids.add(m.group(1))
    child, stats = operators.apply_mutation(src(q['parents'][0]), reply, ids, 'Z')
    print('editable', sorted(ids), 'stats', {k: v for k, v in stats.items() if k != 'pruned'}, 'pruned', stats.get('pruned'))
else:
    class C:
        def ask(self, *a, **k): return reply, 'm', 0.0, {}
    a, b = q['parents'][:2]
    ch = operators.llm_cross(src(a), 0, src(b), 0, C(), 'Z')
    if ch.error: print('ERROR', ch.error); sys.exit(1)
    child = ch.source; print('cross ok', {k: v for k, v in ch.log.items() if k not in ('llm',)})
build.build(child)
print('build ok')
if '--out' in sys.argv: open(sys.argv[sys.argv.index('--out') + 1], 'w').write(child)
if '--write' in sys.argv:
    p = f'{Q}/rep-{seq}.txt'
    assert not os.path.exists(p), 'already written'
    open(p, 'w').write(reply); print('written', p)
