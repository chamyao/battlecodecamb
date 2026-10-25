import sys; sys.path.insert(0,'/root/w')
from lib import *
s = int(sys.argv[1]); sc = ed(s,'score'); a = "    if o.kind == TRIBUTE:\n        return 70\n"
assert a in sc
w(s, desc(sc.replace(a, "    if o.kind == TRIBUTE:\n        return 86 if gems() >= 10 else 70\n"), "bank a full bag before fighting"))
open(f'/root/w/d/{s}.best','w').write(f'/root/w/d/{s}.tribute_first.txt')
