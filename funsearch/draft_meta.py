"""Draft screen against the ladder meta composition (FunSearch lead; docs/LADDER_LOSSES_V16.md on analysis/sprint1:
vc? drafts VV, HoR, Marcella, Vendetta, Ryth and won fights 130-21 against tune-5). Orders on tune-5: a copy of the
meta draft, and every head of 3 from {vendetta, vesper_vale, tavi, heart_of_ruin, marcella, ryth} with the two best
tails. Each order: 200 games vs opp-metadraft (tune-5 with the meta draft) and 200 vs tune-5, seed SEED; ranked by
the mean. Both teams may pick the same champion, so a "counter" can't deny picks; it can only out-fight them.
usage: draft_meta.py TAG SEED"""
import itertools, json, sys
sys.path.insert(0, '.')
from funsearch.race import *

tag, seed = sys.argv[1], int(sys.argv[2])
base = open("policies/tune-5.policy").read()
bpol = compile_text(base)
meta = compile_file("policies/opp-metadraft.policy")
pool = ["vendetta", "vesper_vale", "tavi", "heart_of_ruin", "marcella", "ryth"]
orders = {("vesper_vale", "heart_of_ruin", "marcella", "vendetta", "ryth")}
for head in itertools.permutations(pool, 3):
    rest = [c for c in ["ryth", "ren", "heart_of_ruin", "vendetta", "marcella"] if c not in head]
    orders.add(head + tuple(rest[:2]))
orders.add(("vendetta", "vesper_vale", "tavi", "ryth", "ren"))  # tune-5 itself (control)
log = open(f"runs/tune/draftmeta-{tag}.log", "a")
res = []
for o in sorted(orders):
    pol = compile_text(set_draft(base, chain_draft(list(o))))
    try:
        vm = h2h(pol, meta, 200, seed)["win_rate"]
        vb = h2h(pol, bpol, 200, seed + 1)["win_rate"]
    finally:
        Path(pol).unlink(missing_ok=True)
    res.append(((vm + vb) / 2, vm, vb, ",".join(o)))
    log.write(f"{','.join(o)}: vs_meta {vm:.3f} vs_t5 {vb:.3f}\n"); log.flush()
res.sort(reverse=True)
json.dump(res, open(f"runs/tune/draftmeta-{tag}.json", "w"), indent=1)
