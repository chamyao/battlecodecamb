"""Full constant grid (const_spec knobs + fight_spec knobs and switches) around a centre genome, with knobs moved by
promoted edits given their new current values. python3 genome/tuneb/full_spec.py OUT.json CENTRE.genome MOVED_JSON"""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import const_spec as cs, fight_spec as fs

text = open(sys.argv[2]).read()
moved = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
allk = {k[0]: k for k in cs.KNOBS + cs.RH + cs.B32}
by = {k[0]: k for k in cs.knobs(text)}
for n, (cur, vals) in moved.items():
    if n in allk:
        by[n] = (n, allk[n][1], cur, vals)
out, seen = [dict(tag='centre', edits=[])], set()
for n, tpl, cur, vals in sorted(by.values(), key=lambda k: (k[0] not in cs.ECON, k[0])):
    old = tpl.format(cs.fmt(cur))
    if text.count(old) != 1:
        continue
    for v in vals:
        out.append(dict(tag='%s=%s' % (n, cs.fmt(v)), edits=[[old, tpl.format(cs.fmt(v))]]))
    seen.add(n)
for v in fs.variants(text, {k: x for k, x in moved.items() if k not in allk}):
    if v['tag'].split('=')[0] not in seen:
        out.append(v)
json.dump(out, open(sys.argv[1], 'w'), indent=0)
print(len(out), 'variants;', len(seen), 'const knobs')
