"""Confirm a combination of near-miss constant changes on fresh seeds, with the full gauntlet.
usage: combo_confirm.py BASE TAG SEED1 SEED2 'old=>new' ['old=>new' ...]"""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

base_file, tag, s1, s2 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
base = open(base_file).read()
t = base
for e in sys.argv[5:]:
    old, new = e.split("=>")
    assert t.count(old) == 1, old
    t = t.replace(old, new)
open(f"runs/tune/{tag}.policy", "w").write(t)
r = confirm(t, compile_text(base), seeds=(s1, s2), base_text=base, log=lambda s: None)
open(f"runs/tune/{tag}.log", "a").write(json.dumps(r) + "\n")
