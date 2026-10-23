"""Building-block registry: every block's name, typed inputs and output.

A block with ret == VOID is an effect (a step); the rest are pure and nest.
`fuel` is a placeholder until prices are measured against cambc.
"""
from dataclasses import dataclass

TYPES = (
    "Num", "Bool", "Tile", "TileSet", "Unit", "UnitList", "UnitPred",
    "TilePred", "Stat", "Item", "Team", "Champ", "ChampList", "Bytes", "Family",
)
VOID = "Void"


@dataclass(frozen=True)
class Block:
    name: str
    args: tuple
    ret: str
    infix: str | None = None  # operator symbol, for printing
    fuel: int | None = None

    @property
    def effect(self):
        return self.ret == VOID

    @property
    def key(self):
        return f"{self.name}({','.join(self.args)})"


REGISTRY: list[Block] = []


def _b(name, args, ret, infix=None):
    REGISTRY.append(Block(name, tuple(args.split()), ret, infix))


# Literals
_b("ally", "", "Team")
_b("enemy", "", "Team")
_b("stat_strength", "", "Stat")
_b("stat_focus", "", "Stat")
_b("stat_health", "", "Stat")

# Arithmetic and logic
for _name, _op in (("add", "+"), ("sub", "-"), ("mul", "*"), ("div", "/")):
    _b(_name, "Num Num", "Num", _op)
for _name, _op in (("lt", "<"), ("le", "<="), ("gt", ">"), ("ge", ">="), ("eq", "==")):
    _b(_name, "Num Num", "Bool", _op)
_b("ne", "Num Num", "Bool", "!=")
_b("true", "", "Bool")
_b("false", "", "Bool")
_b("and", "Bool Bool", "Bool", "and")
_b("or", "Bool Bool", "Bool", "or")
_b("not", "Bool", "Bool")
_b("floor", "Num", "Num")

# Draft
_b("is_draft", "", "Bool")
_b("unpicked_champions", "", "ChampList")
_b("random_champion", "ChampList", "Champ")
_b("pick", "Champ", VOID)
# Champions by draft index (Cassi & Issac are one pick)
CHAMPIONS = ("ryth", "vesper_vale", "vendetta", "cassi_issac", "stellar", "prism",
             "marcella", "willow", "ren", "varg", "tavi", "heart_of_ruin")
for _name in CHAMPIONS:
    _b(f"champ_{_name}", "", "Champ")
_b("available", "ChampList Champ", "Bool")
_b("i_am", "Champ", "Bool")
_b("write_draft", "Bytes", VOID)

# Self
for _name in ("alive", "channeling", "can_move", "can_attack"):
    _b(_name, "", "Bool")
_b("position", "", "Tile")
_b("ability_ready", "Num", "Bool")
for _name in ("health", "max_health", "gems", "gold", "round_number", "fuel_remaining"):
    _b(_name, "", "Num")

# Static map
for _name in ("altars", "walls", "holes", "bushes", "camp_spawn_tiles"):
    _b(_name, "", "TileSet")
_b("spawn_region", "Team", "TileSet")
# Spawn tiles of every camp of one type (static map facts)
CAMP_TYPES = ("wolf", "elk", "gem_cluster", "gold_cluster", "monolith", "golem")
for _name in CAMP_TYPES:
    _b(f"{_name}_tiles", "", "TileSet")

# Vision
_b("enemies_visible", "", "UnitList")
_b("allies_visible", "", "UnitList")
_b("camps_visible", "", "UnitList")
_b("locked_altars", "", "TileSet")
_b("respawning_visible_spawns", "", "TileSet")

# Memory
_b("read_shared", "Num", "Num")
_b("write_shared", "Num Num", VOID)

# Tile sets
_b("union", "TileSet TileSet", "TileSet")
_b("minus", "TileSet TileSet", "TileSet")
_b("contains", "TileSet Tile", "Bool")
_b("ring", "TileSet Num", "TileSet")
_b("closest", "TileSet", "Tile")
_b("filter", "TileSet TilePred", "TileSet")
_b("first", "TileSet", "Tile")
_b("exists", "Tile", "Bool")
_b("count", "TileSet", "Num")
_b("within", "Num Tile", "TilePred")
_b("distance", "Tile Tile", "Num")

# Units
_b("filter", "UnitList UnitPred", "UnitList")
_b("first", "UnitList", "Unit")
_b("exists", "Unit", "Bool")
_b("count", "UnitList", "Num")
_b("unit_position", "Unit", "Tile")
_b("unit_health", "Unit", "Num")
_b("in_attack_range", "", "UnitPred")
_b("weakest", "UnitList", "Unit")
_b("richest", "UnitList", "Unit")
_b("nearest", "UnitList", "Unit")

# Randomness
_b("random_int", "Num", "Num")
_b("random_stat", "", "Stat")

# Items: shard(stat) is a Power shard; shard_of picks the emblem family.
_b("shard", "Stat", "Item")
FAMILIES = ("monster", "power", "durability", "treasure", "jungle", "home", "bruiser")
for _name in FAMILIES:
    _b(f"family_{_name}", "", "Family")
_b("shard_of", "Family Stat", "Item")
_b("buy_altar_lock", "", VOID)
_b("buy_teleport", "", VOID)
_b("has_altar_lock", "", "Bool")
_b("has_teleport", "", "Bool")
_b("place_altar_lock", "Tile", VOID)
_b("teleport_to", "Tile", VOID)

# Abilities and class
_b("i_am_ranged", "", "Bool")
for _name in ("dash", "damage", "aoe", "stun", "heal", "shield", "reset"):
    _b(f"slot_is_{_name}", "Num", "Bool")
_b("dash_towards", "Num Tile", VOID)

# Scores and map facts (also usable in the draft)
_b("unit_gems", "Unit", "Num")
_b("team_score", "Team", "Num")
_b("map_width", "", "Num")
_b("map_height", "", "Num")
_b("camp_count", "", "Num")

# Team communication over shared memory (fixed layout: bytes 0-5 hold each
# ally's claimed camp group, byte 6 the team's target; raw read/write_shared
# should only use byte 7).
_b("claim", "Tile", VOID)
_b("unclaim", "", VOID)
_b("claimed_by_allies", "", "TileSet")
_b("claim_count", "Tile", "Num")
_b("set_team_target", "Unit", VOID)
_b("team_target", "", "Unit")

# Safety and situation (from the ladder-loss analysis)
_b("in_danger", "", "Bool")
_b("move_away_from", "Tile", VOID)
_b("allies_within", "Num", "Num")
_b("unit_health_frac", "Unit", "Num")
_b("capturable_spawns", "", "TileSet")
_b("turns_idle", "", "Num")
_b("enemies_within", "Num", "Num")
_b("local_strength", "Num", "Num")
_b("rich_spawns", "Num", "TileSet")
_b("group_tiles", "TileSet", "TileSet")
_b("group_gems", "TileSet", "Num")
_b("group_threat", "Tile", "Num")
_b("group_hp", "Tile", "Num")

# Effects
_b("move_towards", "Tile", VOID)
_b("attack", "Unit", VOID)
_b("cast_at_unit", "Num Unit", VOID)
_b("cast_at_tile", "Num Tile", VOID)
_b("cast_self", "Num", VOID)
_b("place_ward", "Tile", VOID)
_b("tribute", "Tile", VOID)
_b("recall", "", VOID)
_b("buy", "Item Num", VOID)
_b("set_priority", "Num", VOID)

BY_NAME: dict[str, list[Block]] = {}
for _blk in REGISTRY:
    BY_NAME.setdefault(_blk.name, []).append(_blk)
BY_KEY = {b.key: b for b in REGISTRY}
INFIX = {b.infix: b for b in REGISTRY if b.infix}


def resolve(name, arg_types):
    """The overload of `name` taking exactly `arg_types`."""
    for blk in BY_NAME.get(name, ()):
        if blk.args == tuple(arg_types):
            return blk
    raise TypeError(f"no block {name}({', '.join(arg_types)})")
