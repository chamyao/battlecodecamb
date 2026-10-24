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
fuel_remaining() gates are a real lever now (until recently the live bot could not read its fuel):
reading it costs almost nothing, so guard optional expensive steps (extra board scans, dashes,
far camp scoring) with e.g. `if fuel_remaining() > 40000:` to skip them on heavy turns; pick
thresholds well away from the typical mid-turn reading. This is compute as part of the policy.
dash_towards is the exception to watch: on 100x100 maps a turn with dashes can approach the
100,000 limit, so guard repeated dash attempts (check slot_is_dash and ability_ready first).
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
At most 16 let/keep statements per value type (Num, Bool, Tile, TileSet, Unit, ...) in the whole
program, counting every statement, including both branches of an if: the policy is invalid
beyond that. Macros are expanded at every call, so each call of a macro containing lets uses
that many slots again. Inline a value used once instead of naming it, and reuse names across branches.
A name cannot be redefined in the same scope (use a new name, e.g. camp2); the two branches of
one if may each define the same name. elif is fine.
Not supported (each one makes the policy invalid): %, //, **, None (test with exists(...)),
is / in, chained comparisons like 1 < x < 3 (use and), keyword arguments, attribute access
like .x, indexing, lists/tuples, for/while, def inside a block, return outside a macro.
Comments start with #.
"""

# the game without the ladder observations and directions below (exploration's "lean" prompt)
GAME_BASE = GAME

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
- Some deaths come from fights taken while outnumbered (compare allies_within(4) with the
  number of visible enemies), but most of our deaths to champions come in even or favourable
  fights (1v1 deaths: 121 ours vs 41 theirs). So improve fight quality (target choice,
  ability use and timing, focus fire, items) rather than avoiding fights; make any
  engagement or retreat threshold a named constant so it can be tuned.
- Simple threshold rules on local_strength lost in our tests (retreat when below a ratio:
  32-53% vs a 51% mirror; chase when above: 20-28%). The gains are in how to fight (ability
  timing, target choice, staying with allies), not whether to engage. local_strength(r) is 100
  when no enemy is within r: pair it with enemies_within(r) > 0.
Observations from our v6 ladder losses (we are ~23-12 since v5d):
- Our main loss is to melee stun/dive teams, who kill us 21-34 times per game: our ranged
  champions trade in place when a melee enemy is adjacent. Ideas: kite (i_am_ranged(): step
  move_away_from the adjacent melee enemy, then attack from range) and stay near allies.
- Gem camps in contested middles: on one map we made 157 captures and 0 gems because we only
  farmed edge gold clusters. Gems, not gold, win games; go for gem camps (gem_cluster_tiles(),
  wolves, elks), with allies when they are contested.
Observations from our v7 ladder losses: we now lose on SCORING RATE, not fights or freezes.
- Our captures yield ~15 gems each vs 21-60 for the teams beating us, and 27% of ours are
  gold-only (0 gems). Our median tribute bag is 14 vs their 30-39.
- The winners take monoliths as a team: one team took both monoliths on a big map, worth its
  whole 456-gem margin. Try committing 3+ champions together (claim_count) to a monolith.
- Simple fixes were neutral or worse in tests: always preferring the richest groups lost
  (33-38/80); preferring elk/gem clusters, or a bag of 25, were neutral. The gain probably needs
  a value-vs-distance trade-off when choosing camps, team monolith takes, and bigger bags
  without more deaths. Treat these as directions, not rules.
- Camp-choice blocks: group_gems(set) is what a group pays, group_threat(g) and group_hp(g) what
  it costs, rich_spawns(n) the spawns of groups worth >= n gems, group_tiles(monolith_tiles()) the
  monolith group. Bind static sets with keep. MEASURED (2000 games vs the live bot): skipping the
  nearest group when group_threat(g) * group_hp(g) / (strength() * (1 + allies_within(4))) exceeds
  health() LOSES 25 points (52% -> 28%); x3 health still loses 11, x6 loses 5, x12 is neutral.
  That ratio is far larger than health on almost every group, so do not use it as a skip test.
  A direction worth trying instead (early screen +4, unconfirmed): choose a rich group (closest of
  goals intersected with rich_spawns(15)) over the nearest camp when it is only a few tiles farther.
- Constant tuning around the current best finds nothing better (its thresholds are locally
  optimal). Camp choice is the second lever: today the goal is simply the closest camp spawn.
Observations from 50 games vs the ladder's top 10 (live bot, v16): 0-50. COMBAT IS NOW THE TOP PRIORITY.
- Per game: our deaths 17.8 vs their 1.6, our kills 0.3 vs their 12.9, damage to champions 7.2k vs
  21.1k. Max HP is equal at round 100, yet their first kill comes at a median of round 175: they win
  fights at even strength, mostly with 1-2 champions, not packs. The item gap comes from the kills.
- In the 5 rounds before each of our deaths to a champion the victim attacked an enemy champion only
  59% of the time, cast an ability on one only 16% (casts went to self or dash 32%), had started a
  recall (damage cancels it) 23%, attacked a camp 18%. 52% of our dead carried no gems.
- How they fight (1,317 engagements, docs/TOP_TEAMS_RULES.md; medians): engage healthy (HP 0.9-1.0 at
  the first hit), usually 2v1; target the closest visible enemy (usually also the weakest); open with
  the ability on the first-hit turn; chase only 0-2 tiles; they leave around 0.8 HP and die 1.6 times a
  game. Openers: Heart of Ruin stunning dash from 3; Vendetta dash from 3; Marcella damage from 4; Ryth
  AoE stun from 4; Prism AoE from 5 then damage-stun; Tavi stun from 4; Cassi stun from 5. Vesper Vale,
  Vendetta, Tavi and Ryth have an attack RESET: self-cast it (cast_self) right AFTER a basic attack,
  then attack again. Casting a reset at the enemy fails. Fixing just that in the live bot gained
  +9.7 points (59.7% over 1600 games), kills 7.3 vs 5.1.
- Ability blocks: slot_stun(slot) = stun turns on hit (HoR's dash and Ryth's AoE included),
  slot_range(slot) / slot_radius(slot) = cast range and area radius, slot_is_reset / slot_is_dash /
  slot_is_shield / slot_is_heal for the type, i_am(champ_heart_of_ruin()) etc. for who you are.
  Opener: if ability_ready(1) and slot_stun(1) > 0 and distance(position(), unit_position(enemy))
  <= slot_range(1) + slot_radius(1): dash_towards(1, ...) for a dash, else cast_at_unit(1, enemy).
- The simulator matches the real engine in fights (119/120 games turn for turn), so fight results
  here are real. MEASURED: an ability opener plus basic > reset > basic inside attack reach, focused
  on the team target, gained ~+7 points. Engaging from 8 tiles at HP >= 0.8 LOST (24% vs the live bot),
  disengaging at 0.75 HP lost more (13%), and a naive chase of the weakest within 6 lost (33%). So the
  macro rules alone are not the gap. The MICRO is: landing the first hit (turn order via
  set_priority, approaching from out of vision), 2v1 focus where both hit the same target on the same
  turn, kiting at max range for ranged champions (i_am_ranged, move_away_from after the attack),
  ability timing (stun before burst, reset after a basic), and spending gold on stats we don't buy.
  Explore these.
- Also: never start a recall while in_danger() (move away first); tribute at once when an enemy is
  near while carrying.
"""

GRAMMAR += """\
Macros (the one exception to "no functions"): top-level `def name(a, b):` definitions are
expanded inline where called. A macro whose whole body is `return <expr>` is used as a
value; any other macro is used as a step. Arguments are re-evaluated at each use (bind them
with let first to pay their fuel once). No recursion. Build reusable helpers this way. A step macro cannot call another step macro (inline it).
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
    "position": "this champion's tile", "health": "", "max_health": "", "strength": "your Strength: basic attack damage per hit (items included)", "focus": "your Focus: ability damage scaling (items included)",
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
    "locked_altars": "altar tiles with a visible enemy altar lock (our own locks never block our tributes)",
    "respawning_visible_spawns": "spawn tiles of visible camp groups that are waiting to respawn",
    "write_shared": "write byte value (0-255) at offset i (use 7; 0-6 are used by claims and team target). Byte 7 is shared: bits 0-1 are the lock flags (placed, bought), so keep them: let v = read_shared(7), write_shared(7, 4 * x + (v - 4 * floor(v / 4))) for your own value x (0-63)",
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
    "slot_is_shield": "self shield", "slot_is_reset": "attack reset (self-cast it AFTER a basic attack, then attack again)",
    "slot_range": "cast range in tiles of ability slot (0/1); a dash's travel distance", "slot_radius": "area radius of the slot's effect (0 = single target)",
    "slot_stun": "turns the slot stuns on hit, 0 if none: cc abilities and stunning damage/dash (Heart of Ruin's dash, Ryth's AoE). Open fights with it",
    "unit_is": "true if the unit is that champion (e.g. unit_is(enemy, champ_heart_of_ruin()))", "unit_shield": "shield points currently on a visible champion (absorbs damage before health); 0 if none",
    "unit_tributing": "true if a visible champion is channelling a tribute (gem submission) right now; placing an altar lock on that altar cancels every tribute in progress there, allies' included",
    "unit_max_health": "a visible champion's max health, items included (0 if not a visible champion)", "unit_strength": "a visible champion's Strength (basic attack damage, items included)", "unit_focus": "a visible champion's Focus (ability damage scaling, items included)",
    "enemies_near": "number of living visible enemy champions within r tiles of a tile (e.g. of a fight target, a camp goal, or the altar you are carrying gems to)", "allies_near": "number of living allied champions (you included) within r tiles of a tile",
    "strength_at": "local_strength measured around a tile instead of around you: (health x damage) of our champions within r of the tile over the same for visible enemies; >1 favours us, 100 if no enemy is there",
    "threat_eta": "fewest turns until any visible enemy champion could hit you (its distance minus its attack range, over its speed; walls ignored); 1000 if none visible",
    "altar_eta": "turns for you to reach a tile next to the nearest altar you can tribute at (not enemy-locked), walls ignored", "retreat_eta": "turns for you to reach your spawn region, walls ignored",
    "enemy_between": "true if a visible enemy champion is within 3 tiles of the straight line from you to the tile", "group_contested": "number of visible enemy champions closer to the tile than you are",
    "team_gems": "gems carried by all your living champions together",
    "unseen_enemies_near": "unseen_enemies_near(r, age): enemy champions not visible now that you saw within the last `age` rounds within r tiles of you (sightings are remembered each time you call this, so call it every turn)",
    "dash_towards": "cast the dash in slot (0/1) up to 2 tiles along the walking path to the tile",
    "weakest": "lowest-health member, or none", "richest": "member carrying the most gems, or none",
    "nearest": "closest member by Chebyshev distance, or none",
    "claim": "tell allies you are taking the camp group whose spawn tile this is (replaces your previous claim)",
    "unclaim": "drop your camp claim",
    "claim_count": "how many other allies currently claim the camp group whose spawn tile this is (use to commit together)",
    "claimed_by_allies": "spawn tiles of camp groups other allies have claimed",
    "set_team_target": "name an enemy champion as the team's focus target",
    "team_target": "the team's focus target, or none",
    "read_shared": "read shared-memory byte i (only byte 7 is free; 0-6 are used by claims and team target). In byte 7, bits 0-1 are the lock flags (v - 4 * floor(v / 4)) and floor(v / 4) is free for your own value",
    "in_danger": "an awake camp or a visible enemy champion can hit you where you stand (uses THEIR ranges: wolf 3, elk/golem 4, monolith 5; enemy attack range + 1)",
    "move_away_from": "step one tile to increase distance from the tile",
    "allies_within": "number of living allies you can see within Chebyshev distance r",
    "unit_health_frac": "unit's health / max health (0 if not visible)",
    "capturable_spawns": "spawn tiles of visible camp groups that are fully cleared with reward available (stand here to capture)",
    "enemies_within": "number of living enemy champions you can see within Chebyshev distance r",
    "local_strength": "(health x damage) of you + visible allies within r over the same for visible enemy champions within r; >1 means the local fight favours you, 100 if no enemy in r. Use as an engagement/retreat test with a tunable threshold",
    "rich_spawns": "spawn tiles of every camp whose group gives at least n gems when captured (static; gold-only groups give 0 gems, elk/gem-cluster groups 15-60+). Bind it with keep",
    "group_tiles": "spawn tiles of every camp in a group that has a camp on one of the given tiles (static; hitting any camp of a group wakes the whole group, e.g. group_tiles(monolith_tiles()) wakes monoliths). Bind it with keep",
    "group_gems": "total gems of the camp groups that have a camp on one of the given tiles (static; e.g. group_gems(monolith_tiles()) is what the monoliths give). Bind it with keep",
    "group_threat": "summed strength (damage per turn when awake) of the living camps in the group spawning on that tile, 0 off a spawn tile; a camp out of vision counts as alive. Elk 60, wolf 20, golem 120, monolith 200, clusters 0.",
    "group_hp": "summed health of the same camps as group_threat (unseen counts at full health): clearing takes about group_hp(g) / (strength() * (1 + allies_within(4))) turns, taking group_threat(g) damage each turn",
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


# blocks without a calibrated fuel cost yet (interp/src/block_costs_gen.inc): a policy using them is
# rejected, so they stay out of the prompt until the coordinator adds the cost entries
UNCOSTED = set()


def block_catalog():
    fuel = _typical_fuel()
    lines = []
    for b in REGISTRY:
        if b.infix or b.name == "not" or b.name in UNCOSTED:
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
