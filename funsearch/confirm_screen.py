"""Confirm the top of a screen: 2 x 400 fresh games vs the base; the gauntlet only for +5 survivors.

usage: confirm_screen.py BASE.policy SCREEN.json TAG KIND [TOP]
KIND is draft (names are comma-separated orders) or const (names are snippet edits, re-made via const_screen.G)."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

base_file, screen_file, tag, kind = sys.argv[1:5]
top = int(sys.argv[5]) if len(sys.argv) > 5 else 8
base = open(base_file).read()
bpol = compile_text(base)
log = open(f"runs/tune/confirm-{tag}.log", "a")
def L(s):
    log.write(s + "\n"); log.flush()

def text_of(name):
    if kind == "draft":
        return set_draft(base, chain_draft(name.split(",")))
    key, new = name.split("=", 1)
    from funsearch.const_screen_grid import G
    old, _ = G[key]
    return base.replace(old, next(n for n in G[key][1] if n.strip() == new))

ranked = [n for w, n in json.load(open(screen_file)) if not n.startswith("control")][:top]
out = {}
for name in ranked:
    t = text_of(name)
    pol = compile_text(t)
    hh = [h2h(pol, bpol, 400, s) for s in (9001, 9002)]
    r = {"h2h": [x["win_rate"] for x in hh], "susp": [x["a_suspensions"] for x in hh]}
    r["h2h_mean"] = sum(r["h2h"]) / 2
    L(f"{name}: {json.dumps(r)}")
    if r["h2h_mean"] >= 0.55:
        full = confirm(t, bpol, base_text=base, log=lambda s: None)
        r.update(gauntlet=full["gauntlet"], cambc_check=full["cambc_check"])
        L(f"{name} FULL: {json.dumps(r)}")
    out[name] = r
    Path(pol).unlink(missing_ok=True)
json.dump(out, open(f"runs/tune/confirm-{tag}.json", "w"), indent=1)
