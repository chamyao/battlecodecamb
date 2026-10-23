"""Draft screen on a base policy: transferred v5d leaders + frontline variants (coordinator's lead)."""
import itertools, json, sys
sys.path.insert(0, '.')
from funsearch.race import *
base_file, tag, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
base = open(base_file).read()
bpol = compile_text(base)
orders = set()
cur = ["vesper_vale", "tavi", "marcella", "stellar", "ren"]
front = ["heart_of_ruin", "ryth", "varg", "cassi_issac", "vendetta"]
# one or two of marcella/stellar/ren replaced by a frontliner, in place
for i in (2, 3, 4):
    for f in front:
        o = list(cur); o[i] = f; orders.add(tuple(o))
for i, j in itertools.combinations((2, 3, 4), 2):
    for f, g in itertools.permutations(front, 2):
        o = list(cur); o[i] = f; o[j] = g; orders.add(tuple(o))
# frontline-first: a frontliner, then VV, tavi, then two of the rest
for f in front:
    for rest in itertools.permutations([c for c in ["marcella", "stellar", "ren", "prism", "varg", "ryth"] if c != f], 2):
        orders.add((f, "vesper_vale", "tavi") + rest)
# leaders from the v5d screen (old fuel table)
for line in sorted(json.load(open("runs/tune/screen-v5d-draft.json")), reverse=True)[:30]:
    if not line[1].startswith("control"):
        orders.add(tuple(line[1].split(",")))
orders.discard(tuple(cur))
cands = {",".join(o): set_draft(base, chain_draft(list(o))) for o in sorted(orders)}
print(len(cands), "candidates", flush=True)
log = open(f"runs/tune/screen-{tag}.log", "a")
def L(s):
    log.write(s + "\n"); log.flush()
res = screen(cands, bpol, games=200, seed=seed, log=L)
json.dump(res, open(f"runs/tune/screen-{tag}.json", "w"))
