"""swapscan.py BASE DONOR MAP...: for each gene id in both with different bodies, swap DONOR's version into BASE; play MAPs both sides."""
import sys, os, json, subprocess, re
sys.path.insert(0, '/root/a10w'); os.chdir('/root/a10w')
from genome import build, lang
from genome.search import edit
B = open(sys.argv[1]).read(); D = open(sys.argv[2]).read(); maps = sys.argv[3:]
_, _, gb = edit.segments(B); _, _, gd = edit.segments(D)
opp = 'genome:' + str(build.build(open('v33.genome').read()))
def play(src):
    sa = 'genome:' + str(build.build(src))
    r = json.loads(subprocess.run(['genome/build/genome_eval', '--a', sa, '--b', opp, '--games', str(2 * len(maps)), '--threads', '1', '--seed', '1', '--bot-seeds', *[f'maps/{m}.map26a' for m in maps]], capture_output=True, text=True).stdout)
    return r['a_wins'], round(r['a_gems']), r['deaths'][0], r['results']
print('base', play(B))
for gid in gb:
    if gid in gd and edit.body_canon(gb[gid]) != edit.body_canon(gd[gid]):
        s = B.replace(gb[gid].rstrip(), gd[gid].rstrip())
        try:
            lang.parse(s); print(gid, play(s), flush=True)
        except Exception as e:
            print(gid, 'ERR', str(e)[:80])
