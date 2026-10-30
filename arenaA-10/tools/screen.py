"""screen.py CAND [OPP...] [--tag T]: 80 bot-seeded games (40 maps x 2 sides) of CAND (a .genome file) vs each opponent
(v33, B318, A61188, farmer, a member name, or a path). Logs to ~/a10w/screens.jsonl."""
import sys, os, json, subprocess, time
sys.path.insert(0, os.path.expanduser('~/a10w')); os.chdir(os.path.expanduser('~/a10w'))
from genome import build
from funsearch.evaluate import MAPS
from genome.search.score import Scorer
A = os.path.expanduser('~/a10w'); G = A + '/runs/arenaA-10/arena/genomes'
args = [a for a in sys.argv[1:] if not a.startswith('--')]
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''
if tag in args: args.remove(tag)
cand, opps = args[0], args[1:] or ['v33']
NAMED = {'farmer': A + '/genome/examples/farmer.genome', 'v33': A + '/v33.genome', 'B318': None, 'A61188': A + '/a7/A61188.genome'}
def spec(x):
    if x in NAMED and NAMED[x]: x = NAMED[x]
    elif x == 'B318': x = A + '/b318.genome'
    elif not os.path.exists(x) and os.path.exists(f'{G}/{x}.genome'): x = f'{G}/{x}.genome'
    if x.endswith('.genome'): return 'genome:' + str(build.build(open(x).read()))
    return Scorer([], threads=1)._spec(x)
ca = spec(cand); maps = sorted(MAPS)
for o in opps:
    t = time.time()
    out = subprocess.run([A + '/genome/build/genome_eval', '--a', ca, '--b', spec(o), '--games', '80', '--threads', '1',
                          '--seed', '1', '--bot-seeds', *maps], capture_output=True, text=True)
    r = json.loads(out.stdout)
    w = r['a_wins']; res = r['results']
    lost = [os.path.basename(maps[i // 2]).split('.')[0] + 'AB'[i % 2] for i, x in enumerate(res) if not x]
    rec = {'time': time.strftime('%H:%M:%S'), 'candidate': cand, 'tag': tag, 'opponent': o, 'wins': w, 'games': 80,
           'gems': [r['a_gems'], r['b_gems']], 'deaths': r['deaths'], 'secs': round(time.time() - t)}
    open(A + '/screens.jsonl', 'a').write(json.dumps(rec) + '\n')
    print(o, f'{w}/80', 'gems', r['a_gems'], r['b_gems'], 'deaths', r['deaths'], 'lost:', ' '.join(lost))
