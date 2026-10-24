"""Draft pass 2 around the tune-1 order (usage: BASE TAG SEED): tails after vendetta,vv,tavi; other frontliners first with the best tails."""
import itertools, json, sys
sys.path.insert(0, '.')
from funsearch.race import *
base_file, tag, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
base = open(base_file).read()
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
log = open(f"runs/tune/screen-{tag}.log", "a")
res = screen(cands, bpol, games=200, seed=seed, log=lambda s: (log.write(s + "\n"), log.flush()))
json.dump(res, open(f"runs/tune/screen-{tag}.json", "w"))
