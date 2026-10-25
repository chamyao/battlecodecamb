import sys; sys.path.insert(0,'/root/w')
from lib import *
s = int(sys.argv[1]); t = ed(s,'threat_at')
t2 = t.replace("dist(u.pos, t) <= u.attack_range + 1 for u in enemies()", "dist(u.pos, t) <= u.attack_range for u in enemies()")
assert t2 != t
w(s, desc(t2, "enemies only when actually in reach"))
open(f'/root/w/d/{s}.best','w').write(f'/root/w/d/{s}.threat_narrow.txt')
