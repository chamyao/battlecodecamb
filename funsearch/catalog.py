"""What the language model is told: the game, the grammar, and every block."""
from policygen.blocks import REGISTRY, VOID

GAME = """\
Cambridge Battlecode 2026a. Two teams of 3-5 champions on a grid map (30x30 to 100x100).
Camps (wolves, elks, golems, gem/gold clusters, monoliths) sit on the map; damaging one wakes
its group, which then attacks the nearest champion. Killing every monster in a group and then
standing on one of its tiles for 5 rounds captures its gold and gems. Carried gems become score
only when tributed beside an altar (a channel of ceil(gems/10) turns; stun cancels it). A dead
champion drops its carried gems to its killer and sits out 60 rounds. First team to tribute
1000 gems wins; otherwise after 2000 rounds the team with more tributed gems wins.
Gold buys shards on your spawn (30 gold each; 5 of one stat combine into an emblem). Each turn a
champion may walk one tile, basic attack once (melee range 1, ranged 3; ranged champions cannot
do both in one turn), and cast one of two abilities (8-turn cooldowns). Recall (5 turns,
cancelled by damage) teleports home; standing on spawn heals. Vision is 8 tiles, blocked by
walls and bushes, and is not shared between allies; 8 bytes of shared memory are.
Every block a bot runs costs fuel; each bot gets 100,000 fuel per turn, and a bot that runs
out is suspended mid-turn and loses tempo. So cheaper policies are better, all else equal.
"""

GRAMMAR = """\
A policy is a Python-shaped program that runs from the top every turn, for every bot (the
draft bot and each champion). Steps:
  <effect block call>              e.g. move_towards(closest(camp_spawn_tiles()))
  if <Bool>: ... [else: ...]       (else-blocks must be non-empty)
  let name = <expr>                value for this turn
  keep name = <expr>               computed once (first time reached), kept across turns
  end_turn()                       stop for this turn
Expressions nest blocks, variables and numeric/string constants. Operators + - * / < <= > >=
== != and or not, unary minus, and True/False are allowed on Num/Bool. Every value is typed; a block's arguments must have
exactly the listed types. No loops, no functions, no other Python. Names must be defined
(let/keep) before use; a let inside an if-branch is only visible in that branch.
A name cannot be redefined in the same scope (use a new name, e.g. camp2); the two branches of
one if may each define the same name. elif is fine.
Not supported (each one makes the policy invalid): %, //, **, None (test with exists(...)),
is / in, chained comparisons like 1 < x < 3 (use and), keyword arguments, attribute access
like .x, indexing, lists/tuples, def/for/while/return.
Comments start with #.
"""

DOCS = {
    "ally": "your team", "enemy": "the other team",
    "stat_strength": "", "stat_focus": "", "stat_health": "",
    "floor": "round down",
    "is_draft": "true for the draft bot (picks champions before the game)",
    "unpicked_champions": "champions your team has not picked yet",
    "random_champion": "uniformly random member (draft)",
    "pick": "draft pick", "write_draft": "write bytes to draft memory (draft bot only)",
    "alive": "this champion is alive", "channeling": "recalling, tributing or teleporting",
    "can_move": "move still available this turn", "can_attack": "attack still available this turn",
    "position": "this champion's tile", "health": "", "max_health": "",
    "gems": "carried gems", "gold": "carried gold", "round_number": "", "fuel_remaining": "fuel left this turn",
    "altars": "all altar tiles", "walls": "", "holes": "", "bushes": "",
    "camp_spawn_tiles": "every camp's spawn tile",
    "spawn_region": "a team's spawn tiles",
    "enemies_visible": "living enemy champions you can see", "allies_visible": "living allies you can see (not you)",
    "camps_visible": "living camps you can see (costs one query per camp on the map)",
    "locked_altars": "altar tiles with a visible altar lock",
    "respawning_visible_spawns": "spawn tiles of visible camp groups that are waiting to respawn",
    "read_shared": "read shared-memory byte i (0-7)", "write_shared": "write byte value (0-255) at offset i (0-7)",
    "union": "", "minus": "a without b", "contains": "tile in set",
    "ring": "all tiles within Chebyshev distance r of the set (scans the map)",
    "closest": "nearest reachable tile of the set by walking distance (none if unreachable)",
    "filter": "keep members satisfying the predicate", "first": "first member, or none",
    "exists": "not none", "count": "",
    "within": "predicate: tile within Chebyshev distance r of a tile",
    "distance": "Chebyshev distance (1e9 if either is none)",
    "unit_position": "", "unit_health": "",
    "in_attack_range": "predicate: unit within this champion's basic attack range",
    "random_int": "uniform in [0, n)", "random_stat": "",
    "shard": "a Power shard of the stat (30 gold)",
    "move_towards": "step one tile along the shortest walkable path to the tile",
    "attack": "basic attack", "cast_at_unit": "cast ability slot (0/1) at a unit",
    "cast_at_tile": "cast ability slot (0/1) at a tile", "cast_self": "cast ability slot (0/1) on yourself",
    "place_ward": "place your ward (within 2 tiles)", "tribute": "start tributing at an adjacent altar",
    "recall": "start the 5-turn recall home", "buy": "buy n of an item (on spawn or while dead)",
    "set_priority": "turn order among your champions next round (higher first)",
}


def block_catalog():
    lines = []
    for b in REGISTRY:
        if b.infix or b.name == "not":
            continue
        sig = f"{b.name}({', '.join(b.args)})"
        ret = "effect" if b.ret == VOID else b.ret
        doc = DOCS.get(b.name, "")
        lines.append(f"  {sig} -> {ret}" + (f"   # {doc}" if doc else ""))
    return "\n".join(lines)
