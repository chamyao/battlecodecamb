import sys, os, json
os.chdir(os.path.expanduser('~/z19')); sys.path.insert(0, '.')
from genome.search.score import Scorer
G = 'runs/arenaZ-19d/arena/genomes/'
a = sys.argv[1]; opps = sys.argv[2].split(','); g = int(sys.argv[3]) if len(sys.argv) > 3 else 60
s = Scorer(['genome/examples/starter.genome'], threads=int(os.environ.get('T', '2')))
A = s._spec(a); tot = 0; out = []
for o in opps:
    p = o if '/' in o else G + o + '.genome'
    st = s.play(A, s._spec(p), 777, g)
    tot += st['win_rate']; out.append(f"{o}:{st['win_rate']:.2f}")
print(f"panel {tot/len(opps):.3f}  " + " ".join(out))
