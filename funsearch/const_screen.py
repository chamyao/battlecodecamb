"""One-at-a-time constant grid on a base policy (exact snippet replacement), screened vs the base."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
base_file, tag, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
base = open(base_file).read()
bpol = compile_text(base)
from funsearch.const_screen_grid import G
cands = {}
for k, (old, news) in G.items():
    assert base.count(old) == 1, (k, base.count(old))
    for n in news:
        cands[f"{k}={n.strip()}"] = base.replace(old, n)
print(len(cands), "candidates", flush=True)
log = open(f"runs/tune/screen-{tag}.log", "a")
def L(s):
    log.write(s + "\n"); log.flush()
res = screen(cands, bpol, games=200, seed=seed, log=L)
json.dump(res, open(f"runs/tune/screen-{tag}.json", "w"))
