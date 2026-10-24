"""Lead (1) from the coordinator: tune-3's scoreless-after-300 monolith fallback misfires on 01starvation.
Variants of its condition, scored like bank_fix.py (all-map vs tune-3, cambc-exact 80, per-map starvation/hooks
vs Icecream, v7zg-cast and the metab-v3 stand-in), plus the three maps where the fallback rescues slow starts."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.map_diag import play

OLD = "if team_score(ally()) == 0 and round_number() > 300:\n"
KEEP_ANCHOR = "keep camp_spawns = camp_spawn_tiles()\n"
KEEP = "keep non_mono_gem_spawns = count( minus( rich_spawns(1), group_tiles( monolith_tiles() ) ) )\n"
CONDS = {
    "r800": "round_number() > 800",
    "allies2": "round_number() > 300 and allies_within(4) >= 2",
    "r600-allies1": "round_number() > 600 and allies_within(4) >= 1",
    "nomono-or-r900": "(round_number() > 300 and non_mono_gem_spawns == 0) or round_number() > 900",
}


def mono(base, cond):
    assert base.count(OLD) == 1
    t = base.replace(OLD, f"if team_score(ally()) == 0 and {cond}:\n")
    if "non_mono_gem_spawns" in cond:
        t = t.replace(KEEP_ANCHOR, KEEP_ANCHOR + KEEP, 1)
    return t


if __name__ == "__main__":
    base = open("policies/tune-3.policy").read()
    bpol = compile_text(base)
    opps = {n: compile_file(f"policies/{n}.policy") for n in ("opp-icecream", "v7zg-cast", "opp-metab")}
    log = open("runs/tune/monofix.log", "a")
    for name, cond in CONDS.items():
        pol = compile_text(mono(base, cond))
        r = {"all400": h2h(pol, bpol, 400, 9015)["win_rate"], "cambc80": h2h(pol, bpol, 80, 1, bot_seeds=True)["win_rate"]}
        for m in ("01starvation", "01hooks", "00stampede", "00pilgrimage", "01shortcut"):
            for on, op in opps.items():
                if m not in ("01starvation", "01hooks") and on != "v7zg-cast":
                    continue
                s = play(pol, op, f"maps/{m}.map26a", 40, 21)
                r[f"{m}/{on}"] = [s["wins"], s["gems"]]
        log.write(f"{name}: {json.dumps(r)}\n"); log.flush()
