"""applyrep.py BASE REPLY OUT: apply a mutation reply to BASE (editable = gene ids the reply names that BASE has)."""
import sys, re
sys.path.insert(0, '/root/a10w')
from genome.search import operators, edit
from genome import build
b = open(sys.argv[1]).read(); r = open(sys.argv[2]).read()
_, _, g = edit.segments(b)
ids = {i for i in re.findall(r"@gene\(['\"]([^'\"]+)['\"]", r) if i in g}
c, st = operators.apply_mutation(b, r, ids, 'Q'); build.build(c); open(sys.argv[3], 'w').write(c)
print(sys.argv[2], st['genes_changed'], st['genes_added'])
