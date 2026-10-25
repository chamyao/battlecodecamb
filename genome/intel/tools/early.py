import sys, json, glob, os, collections
sys.path.insert(0, '.')
from genome.intel import sim_metrics as sm
# early (r<250) deaths to champions and captures for side A genome vs opponent, all 40 maps, bot seeds
os.environ['GAME_EVENTS'] = '1'
import subprocess
a, b = sys.argv[1], sys.argv[2]
maps = sorted(glob.glob('maps/*.map26a'))
cmd = [sm.EVAL, '--a', sm.side(a), '--b', sm.side(b), '--games', str(2 * len(maps)), '--threads', '1', '--details', '--bot-seeds'] + maps
out = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, GAME_EVENTS='1')).stdout
ev = []; R = collections.defaultdict(list)
for l in out.splitlines():
    if l.startswith('@@EV'): ev.append(l.split()); continue
    if '"game"' in l:
        g = json.loads(l); us = 0 if g['a_side'] == 'A' else 1
        P = lambda e: dict(kv.split('=', 1) for kv in e[1:] if '=' in kv)
        E = [(e[2], P(e)) for e in ev]
        dc = sum(1 for k, p in E if k == 'death' and p['team'] == str(us) and int(p['r']) < 250 and 'camp' not in p.get('by', ''))
        kc = sum(1 for k, p in E if k == 'death' and p['team'] != str(us) and int(p['r']) < 250 and 'camp' not in p.get('by', ''))
        cu = sum(1 for k, p in E if k == 'capture' and p['team'] == str(us) and int(p['r']) < 250)
        ct = sum(1 for k, p in E if k == 'capture' and p['team'] != str(us) and int(p['r']) < 250)
        win = g['winner'] == us
        R['W' if win else 'L'].append((dc, kc, cu, ct))
        ev = []
for k, L in R.items():
    n = len(L)
    print(os.path.basename(a), 'vs', os.path.basename(b), k, n, 'r<250 per game: our deaths to champions %.2f, kills %.2f, captures us/them %.1f/%.1f' % tuple(sum(x[i] for x in L) / n for i in range(4)))
