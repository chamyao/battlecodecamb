import sys,re; sys.path.insert(0,'/root/w')
from lib import *
s = int(sys.argv[1]); v = sys.argv[2]; p = ed(s,'progress')
p2 = re.sub(r"if me\(\)\.health_frac < [\d.]+ and threat_at\(me\(\)\.pos\) > 0:", f"if me().health_frac < {v} and threat_at(me().pos) > 0:", p)
assert p2 != p
w(s, desc(p2, "escape threshold tweak"))
open(f'/root/w/d/{s}.best','w').write(f'/root/w/d/{s}.prog_escape{v}.txt')
