"""What the language model is told: the game, the grammar, and every block."""
import re
from pathlib import Path

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
out is suspended mid-turn (the rest of that turn is lost). Typical policies use ~15k per turn,
so fuel rarely binds: gains come from better play. Each block's typical price is listed below;
keep an eye on it only when adding expensive board-scanning blocks (thousands of fuel each).
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
exactly the listed types. No loops, no functions except macros (below), no other Python. Names must be defined
(let/keep) before use; a let inside an if-branch is only visible in that branch.
A name cannot be redefined in the same scope (use a new name, e.g. camp2); the two branches of
one if may each define the same name. elif is fine.
Not supported (each one makes the policy invalid): %, //, **, None (test with exists(...)),
is / in, chained comparisons like 1 < x < 3 (use and), keyword arguments, attribute access
like .x, indexing, lists/tuples, for/while, def inside a block, return outside a macro.
Comments start with #.
"""

GAME += """\
Observations from today's top-12 ladder games (current rules), for inspiration, not rules:
- Long games (median ~1,100 rounds); more gems captured predicts the winner 92%, more gold 86%,
  more kills 79%, fewer deaths 76%. Wards, altar locks and teleports show no effect.
- Monoliths: the team capturing more wins ~80% where they exist. Top teams never go alone
  (success 0% solo, 29% with 2, 49% with 3, 69% with 4 attackers), start after ~round 1,000,
  commit ~30 rounds, recall individually at low health and return, abandon below 2 attackers.
  (In our tests a plain "3 allies go to the monolith after round 1,000" rule lost badly, so it
  probably needs more damage/sustain first.)
- Drafts: Vesper Vale, Heart of Ruin, Marcella, Vendetta, Ryth. Heart of Ruin plays normally
  (recall ~40-45% health, shield on cooldown in fights, dash toward goals or onto camps).
- Builds: Treasure shards early, then Bruiser (Power Strength for Vesper Vale).
Observations from our own v3 ladder losses (13-22 over 35 games):
- Our scoring stalls: median tributed total at round 1000 is 115 in our losses vs their 899.
  Their bags are 15-18 gems (ours 7) and they earn 2.1x our gold.
- Enemies lock altars. Tributing at a locked altar turns into attacks on the lock (5 hits clear
  it), so never filter locked altars out entirely: v3 did, and its gem carriers idled for
  thousands of rounds.
- Altars within reach of a monolith kill gem carriers: prefer altars outside
  ring(monolith_tiles(), 5).
- Many deaths come from fights taken while outnumbered, usually starting above 50% health:
  avoid fights when allies_within(4) is less than the number of visible enemies, and retreat
  from champions at about 60% health.
"""

GRAMMAR += """\
Macros (the one exception to "no functions"): top-level `def name(a, b):` definitions are
expanded inline where called. A macro whose whole body is `return <expr>` is used as a
value; any other macro is used as a step. Arguments are re-evaluated at each use (bind them
with let first to pay their fuel once). No recursion. Build reusable helpers this way.
If you need a capability that no block or macro can express, write a comment line
`# PROPOSE: <block signature> -> <type>: <what it does and why>` above your policy; it will
be reviewed for adding to the language. Write the policy with the existing blocks anyway.
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
    "wolf_tiles": "spawn tiles of all wolves (20 str, 4 gems, 40 gold)",
    "elk_tiles": "spawn tiles of all elks (60 str, 15 gems, 90 gold)",
    "golem_tiles": "spawn tiles of all golems (120 str, 36 gems, 160 gold)",
    "monolith_tiles": "spawn tiles of all monoliths (20k hp, 200 str, 200 gems, 300 gold; top teams win 80% of games when they capture more of these)",
    "gem_cluster_tiles": "spawn tiles of gem clusters (no damage, 7 gems)",
    "gold_cluster_tiles": "spawn tiles of gold clusters (no damage, 20 gold)",
    "spawn_region": "a team's spawn tiles",
    "enemies_visible": "living enemy champions you can see", "allies_visible": "living allies you can see (not you)",
    "camps_visible": "living camps you can see (costs one query per camp on the map)",
    "locked_altars": "altar tiles with a visible altar lock",
    "respawning_visible_spawns": "spawn tiles of visible camp groups that are waiting to respawn",
    "write_shared": "write byte value (0-255) at offset i (use 7; 0-6 are used by claims and team target)",
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
    "shard_of": "a shard of the given emblem family and stat (30 gold; 5 identical make the emblem)",
    "buy_altar_lock": "buy an altar lock (10 gold, on spawn)", "buy_teleport": "buy a teleport crystal (10 gold, on spawn)",
    "place_altar_lock": "lock an altar within 2 tiles (blocks enemy tributes until broken by 5 attacks)",
    "teleport_to": "teleport crystal: 3-turn channel, then jump up to 3 tiles ignoring terrain",
    "i_am_ranged": "basic attack range 3 (else melee range 1); e.g. Cassi is ranged, Issac melee",
    "slot_is_dash": "ability slot (0/1) is a dash", "slot_is_damage": "single-target damage",
    "slot_is_aoe": "area damage", "slot_is_stun": "stun", "slot_is_heal": "ally heal",
    "slot_is_shield": "self shield", "slot_is_reset": "attack reset",
    "dash_towards": "cast the dash in slot (0/1) up to 2 tiles along the walking path to the tile",
    "weakest": "lowest-health member, or none", "richest": "member carrying the most gems, or none",
    "nearest": "closest member by Chebyshev distance, or none",
    "claim": "tell allies you are taking the camp group whose spawn tile this is (replaces your previous claim)",
    "unclaim": "drop your camp claim",
    "claim_count": "how many other allies currently claim the camp group whose spawn tile this is (use to commit together)",
    "claimed_by_allies": "spawn tiles of camp groups other allies have claimed",
    "set_team_target": "name an enemy champion as the team's focus target",
    "team_target": "the team's focus target, or none",
    "read_shared": "read shared-memory byte i (only byte 7 is free; 0-6 are used by claims and team target)",
    "in_danger": "an awake camp or a visible enemy champion can hit you where you stand (uses THEIR ranges: wolf 3, elk/golem 4, monolith 5; enemy attack range + 1)",
    "move_away_from": "step one tile to increase distance from the tile",
    "allies_within": "number of living allies you can see within Chebyshev distance r",
    "unit_health_frac": "unit's health / max health (0 if not visible)",
    "capturable_spawns": "spawn tiles of visible camp groups that are fully cleared with reward available (stand here to capture)",
    "turns_idle": "consecutive turns (counted each time you check) your position has not changed",
    "unit_gems": "gems a visible champion carries (0 for camps)", "team_score": "gems a team has tributed",
    "map_width": "", "map_height": "", "camp_count": "camps on the map",
}


def _typical_fuel():
    """Mean measured fuel per block call, from the calibration table's comments."""
    path = Path(__file__).resolve().parent.parent / "interp" / "src" / "block_costs_gen.inc"
    try:
        text = path.read_text()
    except FileNotFoundError:
        return {}
    prices = {}
    for key, const, rest in re.findall(r'^\{ "([^"]+)", \w+, \{ (-?\d+),.*\}(.*)$', text, re.M):
        mean = re.search(r"mean=(\d+)", rest)
        prices[key] = int(mean.group(1)) if mean else round(int(const) / 1000)  # provisional: constant term
    return prices


def block_catalog():
    fuel = _typical_fuel()
    lines = []
    for b in REGISTRY:
        if b.infix or b.name == "not":
            continue
        sig = f"{b.name}({', '.join(b.args)})"
        ret = "effect" if b.ret == VOID else b.ret
        doc = DOCS.get(b.name, "")
        price = fuel.get(f"{b.name}({','.join(b.args)})")
        if price is not None:
            cost = f"~{price} fuel" if price > 0 else "fuel not yet measured"
            doc = cost + (f"; {doc}" if doc else "")
        lines.append(f"  {sig} -> {ret}" + (f"   # {doc}" if doc else ""))
    return "\n".join(lines)
