import sys, os
os.chdir(os.path.expanduser('~/z19')); sys.path.insert(0, '.')
from genome.search.score import Scorer
s = Scorer(['genome/examples/starter.genome'], threads=int(os.environ.get('T', '2')))
B = s._spec('/root/w/exp/idle.genome'); g = int(os.environ.get('G', '60'))
for a in sys.argv[1:]:
    st = s.play(s._spec(a), B, 99, g)
    print(f"{os.path.basename(a):18s} gems {st['a_gems']:.0f} rounds {st['avg_rounds']:.0f} deaths {st['deaths'][0]:.1f} capt {st['captures'][0]:.1f} gcap {st['gems_captured'][0]:.0f} trib {st['tributes'][0]:.1f} susp {st['a_suspensions']:.0f}")
