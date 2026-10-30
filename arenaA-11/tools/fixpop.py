"""fixpop.py: restore v39a's rule pick ids (by condition) in every live arena genome's c0, in place."""
import json, re, sys
R = '/home/user/battlecodecamb/arenaA-11'
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
from genome import lang
_, _, V = edit.segments(open(f'{R}/seeds/v39a.genome').read())
pat = re.compile(r'    if [\d.]+ > top and (.*?):\n        top = [\d.]+\n        pick = ([\d.]+)\n')
canon = pat.findall(V['c0'])
s = json.load(open(f'{R}/arena/state.json'))
for m in s['members'].values():
    if m['kind'] != 'genome' or not m['alive']: continue
    p = f"{R}/arena/{m['path']}"; txt = open(p).read(); _, _, g = edit.segments(txt)
    if 'c0' not in g: continue
    seen = {}
    def fix(mm):
        c = mm.group(1); k = seen.get(c, 0); seen[c] = k + 1
        ps = [q for cc, q in canon if cc == c]
        return mm.group(0)[:mm.start(2) - mm.start(0)] + (ps[k] if k < len(ps) else mm.group(2)) + '\n'
    new = pat.sub(fix, g['c0'])
    new = re.sub(r'(if 10 > top:\n        top = 10\n        pick = )[\d.]+', r'\g<1>20', new)
    if new != g['c0']:
        t2 = txt.replace(g['c0'], new); lang.parse(t2); open(p, 'w').write(t2); print('fixed', m['name'])
