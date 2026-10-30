"""xover.py SEQ [ids...]: for an llm_cross request, list genes differing between parents A and B; with ids, write
rep-SEQ.txt = parent A with B's versions of those genes (B-only genes come along when named)."""
import json, re, sys
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
from genome import lang
R = '/home/user/battlecodecamb/arenaA-11'
q = json.load(open(f'{R}/queue/req-{sys.argv[1]}.json'))
A, B = (open(f'{R}/arena/genomes/{p}.genome').read() for p in q['parents'])
_, _, ga = edit.segments(A); _, _, gb = edit.segments(B)
if len(sys.argv) == 2:
    for k in sorted(set(ga) | set(gb)):
        if k not in ga: print('B only', k, gb[k].splitlines()[0][:150])
        elif k not in gb: print('A only', k, ga[k].splitlines()[0][:150])
        elif edit.body_canon(ga[k]) != edit.body_canon(gb[k]):
            print('diff', k, re.search(r'def (\w+)', ga[k]).group(1), '| B:', gb[k].splitlines()[0][len(k)+10:160])
    sys.exit()
ids = sys.argv[2:]
if ids == ['auto']:
    pref = ['r7', 'r4', 'r11', 'm14', 's10', 's11', 'r9', 'r17', 'm13', 'r5', 'r12', 's15', 'm11', 'a2']
    ids = [k for k in pref if k in ga and k in gb and edit.body_canon(ga[k]) != edit.body_canon(gb[k])][:3]
    print('auto', ids)
txt = A
for k in ids:
    if k in ga:
        txt = txt.replace(ga[k], gb[k])
    else:
        txt = txt.rstrip('\n') + '\n\n' + gb[k] + '\n'
lang.parse(txt)
open(f'{R}/queue/rep-{sys.argv[1]}.txt', 'w').write('```python\n' + txt + '\n```\n')
print('wrote', len(txt))
