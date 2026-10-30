import sys, os, json, subprocess
sys.path.insert(0, '/root/a10w'); os.chdir('/root/a10w')
from genome import build
a, b = sys.argv[1], sys.argv[2]
sa = 'genome:' + str(build.build(open(a).read())); sb = 'genome:' + str(build.build(open(b).read()))
for m in sys.argv[3:]:
    r = json.loads(subprocess.run(['genome/build/genome_eval', '--a', sa, '--b', sb, '--games', '2', '--threads', '1', '--seed', '1', '--bot-seeds', f'maps/{m}.map26a'], capture_output=True, text=True).stdout)
    print(m, r['results'], 'gems', r['a_gems'], r['b_gems'], 'rounds', r['avg_rounds'], 'kills', r['kills'], 'deaths', r['deaths'], 'capt', r['captures'], 'gcapt', r['gems_captured'], 'trib', r['tributes'], 'lost2ch', r['gems_lost_to_champs'], 'susp', r['a_suspensions'])
