"""fixpicks.py SEQ [extra.txt]: reply = the request's rule gene with every branch's pick restored to v39a's pick for the
same condition (the tuner perturbs pick ids: 16 -> 15, 13 -> 17, 1 -> 1.1356); guards are left as they are.
extra.txt (a reply file) is appended to the same code block."""
import json, re, sys
R = '/home/user/battlecodecamb/arenaA-11'
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
_, _, V = edit.segments(open(f'{R}/seeds/v39a.genome').read())
pat = re.compile(r'    if [\d.]+ > top and (.*?):\n        top = [\d.]+\n        pick = ([\d.]+)\n')
canon = {}
for cond, pick in pat.findall(V['c0']):
    canon.setdefault(cond, pick)
u = json.load(open(f'{R}/queue/req-{sys.argv[1]}.json'))['user']
blk = re.search(r'## EDITABLE gene rule .*?\n```python\n(.*?)```', u, re.S).group(1)
seen = {}
def fix(m):
    cond = m.group(1); k = seen.get(cond, 0); seen[cond] = k + 1
    picks = [p for c, p in pat.findall(V['c0']) if c == cond]
    p = picks[k] if k < len(picks) else m.group(2)
    return m.group(0)[:m.start(2) - m.start(0)] + p + '\n'
new = pat.sub(fix, blk)
new = re.sub(r'(if 10 > top:\n        top = 10\n        pick = )[\d.]+', r'\g<1>20', new)
changed = new != blk
extra = open(sys.argv[2]).read().replace('```python\n', '').replace('```', '').strip() if len(sys.argv) > 2 else ''
if not changed and not extra:
    sys.exit('no change')
open(f'{R}/queue/rep-{sys.argv[1]}.txt', 'w').write('```python\n' + (new if changed else '') + ('\n' + extra + '\n' if extra else '') + '```\n')
print('picks fixed' if changed else 'picks ok', sys.argv[1])
