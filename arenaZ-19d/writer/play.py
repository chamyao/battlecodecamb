import sys, os, json
os.chdir(os.path.expanduser('~/z19')); sys.path.insert(0, '.')
from genome.search.score import Scorer
a = sys.argv[1]; b = sys.argv[2] if len(sys.argv) > 2 else 'genome/examples/starter.genome'
g = int(sys.argv[3]) if len(sys.argv) > 3 else 12; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
s = Scorer([b], threads=int(os.environ.get('T', '2')))
st = s.play(s._spec(a), s._spec(b), seed, g)
st.pop('results', None)
print(f"win {st['win_rate']:.3f} gems {st['a_gems']:.0f}-{st['b_gems']:.0f} rounds {st['avg_rounds']:.0f} susp {st['a_suspensions']:.0f} deaths {st['deaths']} kills {st['kills']} capt {st['captures']} gcap {st['gems_captured']} trib {st['tributes']}")
