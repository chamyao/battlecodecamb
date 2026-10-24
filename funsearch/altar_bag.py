"""Coordinator's hooks lead: against an altar-holding opponent bag 25 never gets tributed on single-altar maps.
Bag threshold by altar count (static, kept): bag_n = 25 - 15 * floor(k / (count(altars()) + 1)) gives bag 10 when
count(altars()) <= k - 1 (k = 2: one altar; k = 3: one or two), else 25.
Scored on all-map 400 + cambc80 vs tune-3 (with maps lost on both sides) and per-map vs the stand-ins."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play
from funsearch.mono_fix import mono
from funsearch.threat_bank import threat_bank

KEEP_ANCHOR = "keep camp_spawns = camp_spawn_tiles()\n"
OLD = "let bag_ready = gems() >= 25 or"


def altar_bag(base, k):
    keep = (f"# bag 10 on maps with at most {k - 1} altar(s), else 25 (tune line: an altar-holding opponent never lets a\n"
            f"# 3-turn tribute finish on 01hooks)\nkeep bag_n = 25 - 15 * floor( {k} / (count(altars()) + 1) )\n")
    assert base.count(OLD) == 1
    return base.replace(KEEP_ANCHOR, KEEP_ANCHOR + keep, 1).replace(OLD, "let bag_ready = gems() >= bag_n or")


def lost_both_sides(results):
    """cambc80 results list: game g is on map (g // 2) % 40, sides alternate. Maps where both games were lost."""
    return [MAPS[i].split("/")[-1] for i in range(len(results) // 2) if results[2 * i] == 0 and results[2 * i + 1] == 0]


if __name__ == "__main__":
    base = open("policies/tune-3.policy").read()
    bpol = compile_text(base)
    starv = threat_bank(mono(base, "round_number() > 800"), 240)
    cands = {"alt1": altar_bag(base, 2), "alt2": altar_bag(base, 3), "starv+alt1": altar_bag(starv, 2), "starv+alt2": altar_bag(starv, 3)}
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
    log = open("runs/tune/altarbag.log", "a")
    for name, t in cands.items():
        open(f"runs/tune/cand-{name}.policy", "w").write(t)
        pol = compile_text(t)
        chk = h2h(pol, bpol, 80, 1, bot_seeds=True)
        r = {"all400": h2h(pol, bpol, 400, 9023)["win_rate"], "cambc80": chk["win_rate"], "lost_both": lost_both_sides(chk["results"])}
        for m in ("01starvation", "01hooks"):
            for on, op in opps.items():
                s = play(pol, op, f"maps/{m}.map26a", 40, 21)
                r[f"{m}/{on}"] = [s["wins"], s["gems"]]
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
