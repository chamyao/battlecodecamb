"""Risk-based bank rule on tune-5 (FunSearch lead, from docs/LADDER_LOSSES_V16.md on analysis/sprint1: on the ladder
tune-5's carriers die with big bags, median 35.5 in losses vs 25 in wins, 3,364 gems lost to kills in 19 losses).
Keep bag >= 25 and add: (E) an enemy champion near, (W) local strength unfavourable, (F) far from an altar and
unfavourable, screened separately. Each: all-map 400 vs tune-5 (seed 9381), cambc80, and 400 vs v7zg-cast,
Icecream and opp-metadraft (tune-5 with the meta draft) against tune-5's own score there.
usage: bank_t5.py [VARIANT ...]"""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *

OLD = "let bag_ready = gems() >= 25 or round_number() > 1500 or health() < 0.3 * max_health()\n"
ALT = "distance( position(), closest(altar_ring) )"
V = {}
for g in (1, 10):
    for r in (5, 8):
        V[f"E{g}-r{r}"] = f"(gems() >= {g} and enemies_within({r}) > 0)"
for g in (5, 10):
    for s in (0.5, 1):
        V[f"W{g}-s{s}"] = f"(gems() >= {g} and local_strength(8) < {s})"
for d in (8, 15):
    V[f"F10-d{d}"] = f"(gems() >= 10 and {ALT} > {d} and local_strength(8) < 1)"
V["E10-r8+W10"] = "(gems() >= 10 and (enemies_within(8) > 0 or local_strength(8) < 1))"


def bank(base, extra):
    assert base.count(OLD) == 1
    return base.replace(OLD, "# bank early when an enemy champion makes carrying risky (tune line, ladder v16 losses)\n" + OLD.rstrip("\n") + f" or {extra}\n")


if __name__ == "__main__":
    base = open("policies/tune-5.policy").read()
    bpol = compile_text(base)
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("v7zg-cast", "opp-icecream", "opp-metadraft")}
    only = set(sys.argv[1:])
    log = open("runs/tune/bank_t5.log", "a")
    ref = {on: h2h(bpol, op, 400, 9382)["win_rate"] for on, op in opps.items()}
    log.write(f"tune-5 ref: {json.dumps(ref)}\n"); log.flush()
    for name, extra in V.items():
        if only and name not in only:
            continue
        pol = compile_text(bank(base, extra))
        r = {"all400": h2h(pol, bpol, 400, 9381)["win_rate"], "cambc80": h2h(pol, bpol, 80, 1, bot_seeds=True)["win_rate"]}
        for on, op in opps.items():
            x = h2h(pol, op, 400, 9382)
            r[on] = round(x["win_rate"] - ref[on], 4)
            if on == "opp-metadraft":
                r["susp"] = x["a_suspensions"]
        line = f"{name}: {json.dumps(r)}"
        print(line, flush=True); log.write(line + "\n"); log.flush()
