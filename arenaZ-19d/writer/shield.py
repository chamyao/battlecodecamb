import sys; sys.path.insert(0,'/root/w')
from lib import *
s = int(sys.argv[1]); c = ed(s,'cast_value')
a = "return 83 if threat > 0 and me().health_frac < 0.9 else 0"
assert a in c, 'no shield pattern'
w(s, desc(c.replace(a, "return 83 if threat > 0 else 0"), "shield whenever threatened"))
open(f'/root/w/d/{s}.best','w').write(f'/root/w/d/{s}.shield_always.txt')
