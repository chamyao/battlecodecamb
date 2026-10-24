"""Item / gold-spend screen (FunSearch lead: the ladder gap includes gold spending; top teams hold 7.8 items vs our 5).
tune-5's shop: half Treasure-strength, then Jungle-health, Power-strength, Power-health; it never buys Focus (abilities
scale with Focus), Durability (-10% damage taken, champions included) or Home (recall 5 -> 3 turn ends).
Variants on r-campreset (tune5-reset + camp reset), each 400 games vs it (seed 9451) + fight metrics vs v7zg-cast
(80 games, seed 9452). usage: shop_screen.py [VARIANT ...]"""
import json, sys
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fight_metrics import metrics

STR = "    buy( shard(stat_strength()), strength_shards )\n"
HP = "    buy( shard(stat_health()), rest_after_jungle - strength_shards )\n"
JUN = "    buy( shard_of(family_jungle(), stat_health()), jungle_n )\n"
TRE = "    buy( shard_of(family_treasure(), stat_strength()), treasure_n )\n"
V = {
    "base": [],
    "focus": [(STR, "    buy( shard(stat_focus()), strength_shards )\n")],
    "half-focus": [(STR, "    buy( shard(stat_strength()), strength_shards - floor( strength_shards / 2 ) )\n"
                         "    buy( shard(stat_focus()), floor( strength_shards / 2 ) )\n")],
    "dur-hp": [(HP, "    buy( shard_of(family_durability(), stat_health()), rest_after_jungle - strength_shards )\n")],
    "dur-str": [(STR, "    buy( shard_of(family_durability(), stat_strength()), strength_shards )\n")],
    "home-hp": [(JUN, "    buy( shard_of(family_home(), stat_health()), jungle_n )\n")],
    "treasure-focus": [(TRE, "    buy( shard_of(family_treasure(), stat_focus()), treasure_n )\n")],
    "monster-str": [(STR, "    buy( shard_of(family_monster(), stat_strength()), strength_shards )\n")],
    "dur-both": [(HP, "    buy( shard_of(family_durability(), stat_health()), rest_after_jungle - strength_shards )\n"),
                 (STR, "    buy( shard_of(family_durability(), stat_strength()), strength_shards )\n")],
    "dur-hp+focus": [(HP, "    buy( shard_of(family_durability(), stat_health()), rest_after_jungle - strength_shards )\n"),
                     (STR, "    buy( shard(stat_focus()), strength_shards )\n")],
}


def variant(t, edits):
    for o, n in edits:
        assert t.count(o) == 1, o
        t = t.replace(o, n)
    return t


def run(name):
    base = open("runs/tune/league/r-campreset.policy").read()
    pol = compile_text(variant(base, V[name]))
    r = {"fight_v7zg": metrics(pol, compile_file("policies/v7zg-cast.policy"), games=80, seed=9452)}
    if name != "base":
        r["vs_base"] = h2h(pol, compile_text(base), 400, 9451, threads=1)["win_rate"]
    return name, r


if __name__ == "__main__":
    names = sys.argv[1:] or list(V)
    log = open("runs/tune/shop_screen.log", "a")
    with ProcessPoolExecutor(2) as ex:
        for name, r in ex.map(run, names):
            line = f"{name}: {json.dumps(r)}"
            print(line, flush=True); log.write(line + "\n"); log.flush()
