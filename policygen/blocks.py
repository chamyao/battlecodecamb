"""Building-block registry: every block's name, typed inputs and output.

A block with ret == VOID is an effect (a step); the rest are pure and nest.
`fuel` is a placeholder until prices are measured against cambc.
"""
from dataclasses import dataclass

TYPES = (
    "Num", "Bool", "Tile", "TileSet", "Unit", "UnitList", "UnitPred",
    "TilePred", "Stat", "Item", "Team", "Champ", "ChampList", "Bytes",
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
_b("and", "Bool Bool", "Bool", "and")
_b("or", "Bool Bool", "Bool", "or")
_b("not", "Bool", "Bool")
_b("floor", "Num", "Num")

# Draft
_b("is_draft", "", "Bool")
_b("unpicked_champions", "", "ChampList")
_b("random_champion", "ChampList", "Champ")
_b("pick", "Champ", VOID)
_b("write_draft", "Bytes", VOID)

# Self
for _name in ("alive", "channeling", "can_move", "can_attack"):
    _b(_name, "", "Bool")
_b("position", "", "Tile")
for _name in ("health", "max_health", "gems", "gold", "round_number", "fuel_remaining"):
    _b(_name, "", "Num")

# Static map
for _name in ("altars", "walls", "holes", "bushes", "camp_spawn_tiles"):
    _b(_name, "", "TileSet")
_b("spawn_region", "Team", "TileSet")

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

# Randomness
_b("random_int", "Num", "Num")
_b("random_stat", "", "Stat")

# Items
_b("shard", "Stat", "Item")

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
