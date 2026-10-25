import sys; sys.path.insert(0,'/root/w')
from lib import *
s = int(sys.argv[1]); c = ed(s,'cast_value')
a = "        hits = count(dist(u.pos, o.tile) <= 1 for u in enemies()) + count(dist(u.pos, o.tile) <= 1 and is_awake(u) for u in camps())\n        return 84 if hits > 0 else 0\n"
assert a in c and 'aoe_center' not in json.load(open(f'/root/z19/queue/req-{s}.json'))['user'], 'n/a'
c2 = c.replace(a, "        t = aoe_center()\n        return 84 if valid(t) and dist(o.tile, t) == 0 else 0\n")
w(s, desc(c2, "area spells aimed once per pass") + '''@gene("new", "where to drop an area spell this pass: the enemy champion, else the awake camp, within reach", parents=["Z6a"])
def aoe_center() -> Tile:
    e = best(enemies(), lambda u: count(dist(v.pos, u.pos) <= 1 for v in enemies()) if dist(u.pos, me().pos) <= 4 else -1)
    if exists(e) and dist(e.pos, me().pos) <= 4:
        return e.pos
    c = best(camps(), lambda u: count(dist(v.pos, u.pos) <= 1 and is_awake(v) for v in camps()) if is_awake(u) and dist(u.pos, me().pos) <= 4 else -1)
    if exists(c) and is_awake(c) and dist(c.pos, me().pos) <= 4:
        return c.pos
    return tile(-5, -5)

''')
open(f'/root/w/d/{s}.best','w').write(f'/root/w/d/{s}.aoe_center.txt')
