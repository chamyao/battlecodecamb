"""Draft pass 2 around tune-1: tails after vendetta,vv,tavi; other frontliners first with the best tails."""
import itertools, json, sys
sys.path.insert(0, '.')
from funsearch.race import *
base = open('policies/tune-1.policy').read()
bpol = compile_text(base)
allc = ["ryth", "vesper_vale", "vendetta", "cassi_issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi", "heart_of_ruin"]
orders = set()
for tail in itertools.permutations([c for c in allc if c not in ("vendetta", "vesper_vale", "tavi")], 2):
    orders.add(("vendetta", "vesper_vale", "tavi") + tail)
for head in itertools.permutations(["vendetta", "vesper_vale", "tavi"]):
    orders.add(head + ("ryth", "ren"))
for f in ["varg", "ryth", "heart_of_ruin", "cassi_issac"]:
    for tail in [("ryth", "ren"), ("varg", "ren"), ("vendetta", "ren"), ("ryth", "vendetta")]:
        if f not in tail:
            orders.add((f, "vesper_vale", "tavi") + tail)
for o in [("vendetta", "ryth", "vesper_vale", "tavi", "ren"), ("vendetta", "varg", "vesper_vale", "tavi", "ren")]:
    orders.add(o)
orders.discard(("vendetta", "vesper_vale", "tavi", "ryth", "ren"))
cands = {",".join(o): set_draft(base, chain_draft(list(o))) for o in sorted(orders)}
print(len(cands), "candidates", flush=True)
log = open("runs/tune/screen-t1-draft2.log", "a")
res = screen(cands, bpol, games=200, seed=12, log=lambda s: (log.write(s + "\n"), log.flush()))
json.dump(res, open("runs/tune/screen-t1-draft2.json", "w"))
