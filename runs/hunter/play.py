# usage: play.py A.policy B.policy [games] [seed]  -> A's view: win, kills, gems lost
import sys, json, subprocess, tempfile, os
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
from policygen.compile import to_prefix
from policygen.text import parse
from funsearch.evaluate import EVAL_BIN, MAPS
def comp(p):
    if p.startswith('builtin:'): return p
    fd, out = tempfile.mkstemp(suffix='.pol'); os.write(fd, to_prefix(parse(open(p).read())).encode()); os.close(fd); return out
a, b = comp(sys.argv[1]), comp(sys.argv[2])
g = int(sys.argv[3]) if len(sys.argv) > 3 else 80; seed = sys.argv[4] if len(sys.argv) > 4 else '1'
r = json.loads(subprocess.run([str(EVAL_BIN), '--a', a, '--b', b, '--games', str(g), '--threads', '8', '--seed', seed, *MAPS], capture_output=True, text=True).stdout.strip().splitlines()[-1])
print(f"{os.path.basename(sys.argv[1])} vs {os.path.basename(sys.argv[2])}: win {r['win_rate']:.3f} gems {r['a_gems']:.0f}-{r['b_gems']:.0f} kills {r['a_kills']:.1f}-{r['b_kills']:.1f} gems_lost {r['a_gems_lost']:.0f}-{r['b_gems_lost']:.0f} rounds {r['avg_rounds']:.0f} ({r['seconds']:.0f}s)")
