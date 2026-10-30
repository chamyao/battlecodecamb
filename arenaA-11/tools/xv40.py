"""xv40.py SEQ: llm-cross reply = parent A with v40's contest genes (v2, c0, A94141a) grafted in."""
import json, sys
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
from genome import lang
R = '/home/user/battlecodecamb/arenaA-11'
q = json.load(open(f'{R}/queue/req-{sys.argv[1]}.json'))
A = open(f"{R}/arena/genomes/{q['parents'][0]}.genome").read()
_, _, ga = edit.segments(A); _, _, gv = edit.segments(open(f'{R}/v40.genome').read())
txt = A
for k in ('v2', 'c0', 'A94141a'):
    txt = txt.replace(ga[k], gv[k]) if k in ga else txt.rstrip('\n') + '\n\n' + gv[k] + '\n'
lang.parse(txt)
open(f'{R}/queue/rep-{sys.argv[1]}.txt', 'w').write('```python\n' + txt + '\n```\n')
print('v40 graft', sys.argv[1], q['parents'][0])
