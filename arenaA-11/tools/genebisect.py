"""bisect.py GENOME MAP: swap v40's version of each gene that differs into GENOME, one gene at a time; for each variant,
print gems/deaths/rounds vs builtin:idle on MAP (both sides, 4 games)."""
import sys, json, subprocess
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
from genome import build, lang
R = '/home/user/battlecodecamb'
G = open(sys.argv[1]).read(); M = sys.argv[2]
_, _, g = edit.segments(G); _, _, v = edit.segments(open(f'{R}/arenaA-11/v40.genome').read())
def run(txt):
    s = build.build(txt)
    out = subprocess.run([f'{R}/genome/build/genome_eval', '--a', f'genome:{s}', '--b', 'builtin:idle', '--games', '4',
                          '--threads', '4', '--bot-seeds', '--details', M], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        if l.startswith('{') and '"a_side"' in l:
            d = json.loads(l); i = 0 if d['a_side'] == 'A' else 1
            r.append((d['a_side'], d['rounds'], d['gems'][i], d['deaths'][i]))
    return r
print('base', run(G))
for k in sorted(g):
    if k in v and edit.body_canon(g[k]) != edit.body_canon(v[k]):
        t = G.replace(g[k], v[k])
        try:
            lang.parse(t); print(k, run(t))
        except Exception as e:
            print(k, 'ERR', str(e)[:80])
