# FunSearch prompt (as sent; model claude-haiku-5-5, max_tokens 16000)

The system prompt is cached; the user message changes per call (two parent versions from one island, worst first).

## System prompt

```
You improve bot policies for a programming competition, written in a small typed language.

# The game
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
dash_towards is the exception to watch: on 100x100 maps a turn with dashes can approach the
100,000 limit, so guard repeated dash attempts (check slot_is_dash and ability_ready first).
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

# The policy language
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
Macros (the one exception to "no functions"): top-level `def name(a, b):` definitions are
expanded inline where called. A macro whose whole body is `return <expr>` is used as a
value; any other macro is used as a step. Arguments are re-evaluated at each use (bind them
with let first to pay their fuel once). No recursion. Build reusable helpers this way.
If you need a capability that no block or macro can express, write a comment line
`# PROPOSE: <block signature> -> <type>: <what it does and why>` above your policy; it will
be reviewed for adding to the language. Write the policy with the existing blocks anyway.

# Blocks (signature -> return type)
  ally() -> Team   # ~45 fuel; your team
  enemy() -> Team   # ~47 fuel; the other team
  stat_strength() -> Stat   # ~40 fuel
  stat_focus() -> Stat   # ~40 fuel
  stat_health() -> Stat   # ~40 fuel
  true() -> Bool   # ~40 fuel
  false() -> Bool   # ~40 fuel
  floor(Num) -> Num   # ~213 fuel; round down
  is_draft() -> Bool   # ~49 fuel; true for the draft bot (picks champions before the game)
  unpicked_champions() -> ChampList   # ~10123 fuel; champions your team has not picked yet
  random_champion(ChampList) -> Champ   # ~238 fuel; uniformly random member (draft)
  pick(Champ) -> effect   # ~314 fuel; draft pick
  champ_ryth() -> Champ   # ~43 fuel
  champ_vesper_vale() -> Champ   # ~43 fuel
  champ_vendetta() -> Champ   # ~43 fuel
  champ_cassi_issac() -> Champ   # ~43 fuel
  champ_stellar() -> Champ   # ~43 fuel
  champ_prism() -> Champ   # ~43 fuel
  champ_marcella() -> Champ   # ~43 fuel
  champ_willow() -> Champ   # ~43 fuel
  champ_ren() -> Champ   # ~43 fuel
  champ_varg() -> Champ   # ~43 fuel
  champ_tavi() -> Champ   # ~43 fuel
  champ_heart_of_ruin() -> Champ   # ~43 fuel
  available(ChampList, Champ) -> Bool   # ~485 fuel
  i_am(Champ) -> Bool   # ~453 fuel
  write_draft(Bytes) -> effect   # ~286 fuel; write bytes to draft memory (draft bot only)
  alive() -> Bool   # ~275 fuel; this champion is alive
  channeling() -> Bool   # ~275 fuel; recalling, tributing or teleporting
  can_move() -> Bool   # ~277 fuel; move still available this turn
  can_attack() -> Bool   # ~277 fuel; attack still available this turn
  position() -> Tile   # ~264 fuel; this champion's tile
  ability_ready(Num) -> Bool   # ~550 fuel
  health() -> Num   # ~279 fuel
  max_health() -> Num   # ~279 fuel
  gems() -> Num   # ~252 fuel; carried gems
  gold() -> Num   # ~251 fuel; carried gold
  round_number() -> Num   # ~144 fuel
  fuel_remaining() -> Num   # ~77 fuel; fuel left this turn
  altars() -> TileSet   # ~197 fuel; all altar tiles
  walls() -> TileSet   # ~199 fuel
  holes() -> TileSet   # ~199 fuel
  bushes() -> TileSet   # ~199 fuel
  camp_spawn_tiles() -> TileSet   # ~2996 fuel; every camp's spawn tile
  spawn_region(Team) -> TileSet   # ~375 fuel; a team's spawn tiles
  wolf_tiles() -> TileSet   # ~1501 fuel; spawn tiles of all wolves (20 str, 4 gems, 40 gold)
  elk_tiles() -> TileSet   # ~1230 fuel; spawn tiles of all elks (60 str, 15 gems, 90 gold)
  gem_cluster_tiles() -> TileSet   # ~1602 fuel; spawn tiles of gem clusters (no damage, 7 gems)
  gold_cluster_tiles() -> TileSet   # ~1855 fuel; spawn tiles of gold clusters (no damage, 20 gold)
  monolith_tiles() -> TileSet   # ~1014 fuel; spawn tiles of all monoliths (20k hp, 200 str, 200 gems, 300 gold; top teams win 80% of games when they capture more of these)
  golem_tiles() -> TileSet   # ~986 fuel; spawn tiles of all golems (120 str, 36 gems, 160 gold)
  enemies_visible() -> UnitList   # ~975 fuel; living enemy champions you can see
  allies_visible() -> UnitList   # ~1793 fuel; living allies you can see (not you)
  camps_visible() -> UnitList   # ~408 fuel; living camps you can see (costs one query per camp on the map)
  locked_altars() -> TileSet   # ~340 fuel; altar tiles with a visible altar lock
  respawning_visible_spawns() -> TileSet   # ~3033 fuel; spawn tiles of visible camp groups that are waiting to respawn
  read_shared(Num) -> Num   # ~233 fuel; read shared-memory byte i (only byte 7 is free; 0-6 are used by claims and team target)
  write_shared(Num, Num) -> effect   # ~466 fuel; write byte value (0-255) at offset i (use 7; 0-6 are used by claims and team target)
  union(TileSet, TileSet) -> TileSet   # ~768 fuel
  minus(TileSet, TileSet) -> TileSet   # ~764 fuel; a without b
  contains(TileSet, Tile) -> Bool   # ~466 fuel; tile in set
  ring(TileSet, Num) -> TileSet   # ~682 fuel; all tiles within Chebyshev distance r of the set (scans the map)
  closest(TileSet) -> Tile   # ~2306 fuel; nearest reachable tile of the set by walking distance (none if unreachable)
  filter(TileSet, TilePred) -> TileSet   # ~963 fuel; keep members satisfying the predicate
  first(TileSet) -> Tile   # ~412 fuel; first member, or none
  exists(Tile) -> Bool   # ~177 fuel; not none
  count(TileSet) -> Num   # ~291 fuel
  within(Num, Tile) -> TilePred   # ~290 fuel; predicate: tile within Chebyshev distance r of a tile
  distance(Tile, Tile) -> Num   # ~434 fuel; Chebyshev distance (1e9 if either is none)
  filter(UnitList, UnitPred) -> UnitList   # ~1038 fuel; keep members satisfying the predicate
  first(UnitList) -> Unit   # ~286 fuel; first member, or none
  exists(Unit) -> Bool   # ~174 fuel; not none
  count(UnitList) -> Num   # ~200 fuel
  unit_position(Unit) -> Tile   # ~269 fuel
  unit_health(Unit) -> Num   # ~228 fuel
  in_attack_range() -> UnitPred   # ~40 fuel; predicate: unit within this champion's basic attack range
  weakest(UnitList) -> Unit   # ~444 fuel; lowest-health member, or none
  richest(UnitList) -> Unit   # ~427 fuel; member carrying the most gems, or none
  nearest(UnitList) -> Unit   # ~1009 fuel; closest member by Chebyshev distance, or none
  random_int(Num) -> Num   # ~161 fuel; uniform in [0, n)
  random_stat() -> Stat   # ~65 fuel
  shard(Stat) -> Item   # ~192 fuel; a Power shard of the stat (30 gold)
  family_monster() -> Family   # ~43 fuel
  family_power() -> Family   # ~43 fuel
  family_durability() -> Family   # ~43 fuel
  family_treasure() -> Family   # ~43 fuel
  family_jungle() -> Family   # ~43 fuel
  family_home() -> Family   # ~43 fuel
  family_bruiser() -> Family   # ~43 fuel
  shard_of(Family, Stat) -> Item   # ~423 fuel; a shard of the given emblem family and stat (30 gold; 5 identical make the emblem)
  buy_altar_lock() -> effect   # ~141 fuel; buy an altar lock (10 gold, on spawn)
  buy_teleport() -> effect   # ~141 fuel; buy a teleport crystal (10 gold, on spawn)
  has_altar_lock() -> Bool   # ~259 fuel
  has_teleport() -> Bool   # ~259 fuel
  place_altar_lock(Tile) -> effect   # ~336 fuel; lock an altar within 2 tiles (blocks enemy tributes until broken by 5 attacks)
  teleport_to(Tile) -> effect   # ~295 fuel; teleport crystal: 3-turn channel, then jump up to 3 tiles ignoring terrain
  i_am_ranged() -> Bool   # ~266 fuel; basic attack range 3 (else melee range 1); e.g. Cassi is ranged, Issac melee
  slot_is_dash(Num) -> Bool   # ~348 fuel; ability slot (0/1) is a dash
  slot_is_damage(Num) -> Bool   # ~348 fuel; single-target damage
  slot_is_aoe(Num) -> Bool   # ~348 fuel; area damage
  slot_is_stun(Num) -> Bool   # ~348 fuel; stun
  slot_is_heal(Num) -> Bool   # ~348 fuel; ally heal
  slot_is_shield(Num) -> Bool   # ~348 fuel; self shield
  slot_is_reset(Num) -> Bool   # ~348 fuel; attack reset
  dash_towards(Num, Tile) -> effect   # ~3244 fuel; cast the dash in slot (0/1) up to 2 tiles along the walking path to the tile
  unit_gems(Unit) -> Num   # ~185 fuel; gems a visible champion carries (0 for camps)
  team_score(Team) -> Num   # ~320 fuel; gems a team has tributed
  map_width() -> Num   # ~51 fuel
  map_height() -> Num   # ~51 fuel
  camp_count() -> Num   # ~59 fuel; camps on the map
  claim(Tile) -> effect   # ~359 fuel; tell allies you are taking the camp group whose spawn tile this is (replaces your previous claim)
  unclaim() -> effect   # ~171 fuel; drop your camp claim
  claimed_by_allies() -> TileSet   # ~855 fuel; spawn tiles of camp groups other allies have claimed
  claim_count(Tile) -> Num   # ~453 fuel; how many other allies currently claim the camp group whose spawn tile this is (use to commit together)
  set_team_target(Unit) -> effect   # ~288 fuel; name an enemy champion as the team's focus target
  team_target() -> Unit   # ~148 fuel; the team's focus target, or none
  in_danger() -> Bool   # ~5941 fuel; an awake camp or a visible enemy champion can hit you where you stand (uses THEIR ranges: wolf 3, elk/golem 4, monolith 5; enemy attack range + 1)
  move_away_from(Tile) -> effect   # ~2351 fuel; step one tile to increase distance from the tile
  allies_within(Num) -> Num   # ~2771 fuel; number of living allies you can see within Chebyshev distance r
  unit_health_frac(Unit) -> Num   # ~180 fuel; unit's health / max health (0 if not visible)
  capturable_spawns() -> TileSet   # ~3130 fuel; spawn tiles of visible camp groups that are fully cleared with reward available (stand here to capture)
  turns_idle() -> Num   # ~317 fuel; consecutive turns (counted each time you check) your position has not changed
  enemies_within(Num) -> Num   # ~1160 fuel; number of living enemy champions you can see within Chebyshev distance r
  local_strength(Num) -> Num   # ~2565 fuel; (health x damage) of you + visible allies within r over the same for visible enemy champions within r; >1 means the local fight favours you, 100 if no enemy in r. Use as an engagement/retreat test with a tunable threshold
  move_towards(Tile) -> effect   # ~2766 fuel; step one tile along the shortest walkable path to the tile
  attack(Unit) -> effect   # ~265 fuel; basic attack
  cast_at_unit(Num, Unit) -> effect   # ~490 fuel; cast ability slot (0/1) at a unit
  cast_at_tile(Num, Tile) -> effect   # ~393 fuel; cast ability slot (0/1) at a tile
  cast_self(Num) -> effect   # ~530 fuel; cast ability slot (0/1) on yourself
  place_ward(Tile) -> effect   # ~319 fuel; place your ward (within 2 tiles)
  tribute(Tile) -> effect   # ~275 fuel; start tributing at an adjacent altar
  recall() -> effect   # ~132 fuel; start the 5-turn recall home
  buy(Item, Num) -> effect   # ~282 fuel; buy n of an item (on spawn or while dead)
  set_priority(Num) -> effect   # ~217 fuel; turn order among your champions next round (higher first)

# What our ladder losses taught us (ideas to try, not rules)
Diagnosed from real ranked games against stronger teams (we lost 2-13):
- Our champions died to camps ~3x as often as the opponents' did: they kept fighting (recall at
  20% health is less than one monolith hit, and recall is cancelled by damage). Retreating
  toward spawn while in_danger() and recalling only once clear won ~+15 points in our tests.
- Opponents captured 2x as many camps, earned 1.8x the gold and carried bags of 22-58 gems per
  tribute (ours: 5-9, many trips). Bigger bags may pay once champions stop dying; tribute early
  when hurt or when an enemy is near.
- Pick camps you can clear: gold clusters and single wolves early, multi-elk groups with allies
  or later; never solo monoliths or golems (top teams take monoliths with 3-4 champions).
- Fight champions only with at least equal numbers nearby and above ~50% health; if carrying
  gems, disengage toward an altar.
- Spend gold on more item families: Treasure first (more gold), then Jungle (30% less camp
  damage) or Bruiser. Our champions bought only Power shards; opponents bought 6-10 kinds.
- The draft matters a lot: a fixed pick order (vesper_vale, tavi, marcella, stellar, ren) beat
  the same policy with random picks 59%. Write the draft as a deliberate chain of
  `elif available(pool, champ_x()): pick(champ_x())` checks, never random_champion.
- Idle champions: ours stood still off spawn for long stretches (e.g. holding a half-cleared
  camp). turns_idle() can detect that and switch goals.

# Your task
You are shown earlier policy versions, worst first, with their scores (win rate against the
reference bots, plus a small bonus for gem margin; higher is better), its win rate and gems against
each reference bot (weak matchups show where to improve) and, if any, how many turns per game its
champions ran out of fuel (each one is a lost turn). Write one new version that
should score higher. Make a focused, meaningful change: a better rule, a missing behaviour, a
better threshold, or a cheaper way to do the same thing. Keep everything that already works.
Reply with the complete new policy in a single ```policy code block, then nothing else.
```

## User message

```
## Version 0 (score 0.693)
Win rate (your gems - their gems per game): vs builtin:starter 95% (962-182), vs v7-zerogem 46% (748-751), vs v7 52% (748-723), vs v5d-fs2 63% (793-681), vs v5d 78% (841-567), vs v4 76% (833-564), vs locker 98% (767-58), vs fs-2 69% (823-622)
```policy
# v8: v0 (v7-zerogem) plus ability fixes. Shield and heal slots are cast on ourselves during
# champion fights, not at enemies, and are never wasted on camps. Everything else is unchanged.
# v7-zerogem: v7 + fixes for the three maps where a v7 mirror tributes nothing (docs/ZERO_GEM_MAPS.md):
# no fighting enemies on their own spawn, fight a camp that is the only way to an altar, and go
# for monoliths when nothing is tributed by round 300. Proposal from the sim-calibration session.
# v7: v5d-fs2 + idle fix (docs/FARM_DIAGNOSIS.md on deploy/v0): when standing on a dead camp of an
# uncleared group, walk to the nearest living camp instead of idling.
# v5d-fs2 [hybrid line]: v5d plus fs-2's league finds (Treasure/Jungle shards; tribute at >= 10 gems, when hurt, or after round 1500).
# v5d: v5 with a fixed draft order (the composition that won 75% of a v4 mirror).
# v5: v4 attacking the weakest enemy in range (focus fire) instead of the first.
# v4: v3 + altar fixes from docs/LADDER_LOSSES_V3.md: never freeze when every altar is locked
# (tributing a locked altar attacks the lock), and prefer altars out of monolith reach.
# v3: fs-1 + three fixes from the ladder-loss analysis (docs/LADDER_LOSSES.md on analysis/sprint1):
# retreat toward spawn below 30% health while in_danger() and recall only once clear; hold on a
# camp tile only when its group is capturable; skip monoliths and golems.
# Based on fs-1: FunSearch pilot #146 (5 Haiku edits from v1): split strength/health shards, heal on spawn,
# retreat at 50% health when carrying gems, hold on a cleared camp spawn to capture, one camps_visible() per turn.

# ---- draft ----
if is_draft():
    let pool = unpicked_champions()
    if available(pool, champ_vesper_vale()):
        pick(champ_vesper_vale())
    elif available(pool, champ_tavi()):
        pick(champ_tavi())
    elif available(pool, champ_marcella()):
        pick(champ_marcella())
    elif available(pool, champ_stellar()):
        pick(champ_stellar())
    elif available(pool, champ_ren()):
        pick(champ_ren())
    else:
        pick( random_champion(pool) )
    end_turn()

# ---- every turn ----
keep camp_spawns = camp_spawn_tiles()
keep altar_ring = ring( altars(), 1 )
keep safe_altar_ring = ring( minus( altars(), ring(monolith_tiles(), 5) ), 1 )

if not alive() or channeling() or (not can_move() and not can_attack()):
    end_turn()

let at_spawn = contains( spawn_region(ally()), position() )
if at_spawn:
    let shards_bought = floor( gold() / 30 )
    let treasure_n = floor( shards_bought / 2 )
    let rest_after_treasure = shards_bought - treasure_n
    let jungle_n = floor( rest_after_treasure / 3 )
    let rest_after_jungle = rest_after_treasure - jungle_n
    let strength_shards = floor( rest_after_jungle / 2 )
    buy( shard_of(family_treasure(), stat_strength()), treasure_n )
    buy( shard_of(family_jungle(), stat_health()), jungle_n )
    buy( shard(stat_strength()), strength_shards )
    buy( shard(stat_health()), rest_after_jungle - strength_shards )
    # heal on spawn before heading back out, unless an enemy is already in reach
    if health() < max_health() and not exists(first(filter(enemies_visible(), in_attack_range()))):
        end_turn()

# retreat at 20% health normally, but at 50% when carrying gems
if not at_spawn and health() < 0.3 * max_health():
    if in_danger():
        move_towards( closest( spawn_region(ally()) ) )
        end_turn()
    recall()
    end_turn()
if not at_spawn and gems() > 0 and health() < 0.5 * max_health() and not in_danger():
    recall()
    end_turn()

let enemy = weakest( filter( enemies_visible(), in_attack_range() ) )
# an enemy on its own spawn is healed every turn: fighting it there never ends (00reverse-spiral)
if exists(enemy) and not contains( spawn_region(enemy()), unit_position(enemy) ):
    # shields and heals go on ourselves; damage and other abilities go on the enemy
    if ability_ready(0):
        if slot_is_shield(0) or slot_is_heal(0):
            cast_self(0)
        else:
            cast_at_unit(0, enemy)
    if ability_ready(1):
        if slot_is_shield(1) or slot_is_heal(1):
            cast_self(1)
        else:
            cast_at_unit(1, enemy)
    attack(enemy)
    end_turn()

# tribute only with a worthwhile bag (or when hurt / late game)
let bag_ready = gems() >= 10 or round_number() > 1500 or health() < 0.5 * max_health()
if gems() > 0 and bag_ready:
    # an altar next to us works even when locked: tributing there attacks the lock (5 hits clear it)
    let altar = first( filter( altars(), within(1, position()) ) )
    if exists(altar):
        tribute(altar)
        end_turn()
    # walk to an open altar out of monolith reach (5); else any altar out of reach; else any altar
    let target = closest( minus( safe_altar_ring, ring(locked_altars(), 1) ) )
    if exists(target):
        move_towards(target)
        end_turn()
    let target2 = closest(safe_altar_ring)
    if exists(target2):
        move_towards(target2)
        end_turn()
    let altar_goal = closest(altar_ring)
    # every altar-adjacent tile is taken by a camp (01boss-battle: holes and a monolith): fight it
    if contains(camp_spawns, altar_goal):
        let blocker = first( filter( camps_visible(), in_attack_range() ) )
        if exists(blocker):
            attack(blocker)
            end_turn()
    move_towards( altar_goal )
    end_turn()

# one camps_visible() query per turn, reused for both attack checks
let camps = camps_visible()

let camp = first( filter( camps, in_attack_range() ) )
if exists(camp):
    # no shields or heals on camps: they would be wasted
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_heal(0):
        cast_at_unit(0, camp)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_heal(1):
        cast_at_unit(1, camp)
    attack(camp)
    end_turn()

# nothing tributed by round 300 (00contest: only monoliths carry gems): go for monoliths too
if team_score(ally()) == 0 and round_number() > 300:
    move_towards( closest( minus( minus( camp_spawns, respawning_visible_spawns() ), golem_tiles() ) ) )
    end_turn()
let goals = minus( minus( minus( camp_spawns, respawning_visible_spawns() ), monolith_tiles() ), golem_tiles() )

# already standing on a cleared camp spawn: hold here so the capture timer keeps running
if contains(capturable_spawns(), position()):
    end_turn()

let goal = closest(goals)
# on a dead camp of a group that is not cleared yet, the closest goal is our own tile: walk to the
# nearest living camp instead (not a monolith or golem), so the group can be finished
if distance(goal, position()) == 0:
    let live = nearest(camps)
    if exists(live) and not contains( union( monolith_tiles(), golem_tiles() ), unit_position(live) ):
        move_towards( unit_position(live) )
        end_turn()
move_towards( goal )
let camp2 = first( filter( camps, in_attack_range() ) )
if exists(camp2):
    attack(camp2)
set_priority( 1 + random_int(100) )
end_turn()
```

## Version 1 (score 0.699)
Win rate (your gems - their gems per game): vs builtin:starter 95% (962-182), vs v7-zerogem 46% (751-749), vs v7 52% (756-719), vs v5d-fs2 63% (793-685), vs v5d 79% (848-568), vs v4 76% (835-565), vs locker 98% (769-58), vs fs-2 71% (824-630)
```policy
# v2: v1 + ability filtering. Heals and shields are no longer cast at enemies or camps. Damage, stun
# and AoE abilities are used on fight targets, and a self shield goes up when health drops below 60%
# during a fight. Everything else from v1 is unchanged.
# v7-zerogem: v7 + fixes for the three maps where a v7 mirror tributes nothing (docs/ZERO_GEM_MAPS.md):
# no fighting enemies on their own spawn, fight a camp that is the only way to an altar, and go
# for monoliths when nothing is tributed by round 300. Proposal from the sim-calibration session.
# v7: v5d-fs2 + idle fix (docs/FARM_DIAGNOSIS.md on deploy/v0): when standing on a dead camp of an
# uncleared group, walk to the nearest living camp instead of idling.
# v5d-fs2 [hybrid line]: v5d plus fs-2's league finds (Treasure/Jungle shards; tribute at >= 10 gems, when hurt, or after round 1500).
# v5d: v5 with a fixed draft order (the composition that won 75% of a v4 mirror).
# v5: v4 attacking the weakest enemy in range (focus fire) instead of the first.
# v4: v3 + altar fixes from docs/LADDER_LOSSES_V3.md: never freeze when every altar is locked
# (tributing a locked altar attacks the lock), and prefer altars out of monolith reach.
# v3: fs-1 + three fixes from the ladder-loss analysis (docs/LADDER_LOSSES.md on analysis/sprint1):
# retreat toward spawn below 30% health while in_danger() and recall only once clear; hold on a
# camp tile only when its group is capturable; skip monoliths and golems.
# Based on fs-1: FunSearch pilot #146 (5 Haiku edits from v1): split strength/health shards, heal on spawn,
# retreat at 50% health when carrying gems, hold on a cleared camp spawn to capture, one camps_visible() per turn.

# attack-type abilities only (no heals or shields) on a fight target
def fight_unit(u):
    if ability_ready(0) and (slot_is_damage(0) or slot_is_stun(0) or slot_is_aoe(0)):
        cast_at_unit(0, u)
    if ability_ready(1) and (slot_is_damage(1) or slot_is_stun(1) or slot_is_aoe(1)):
        cast_at_unit(1, u)

# self shield when hurt in a fight
def shield_up():
    if ability_ready(0) and slot_is_shield(0) and health() < 0.6 * max_health():
        cast_self(0)
    if ability_ready(1) and slot_is_shield(1) and health() < 0.6 * max_health():
        cast_self(1)

# ---- draft ----
if is_draft():
    let pool = unpicked_champions()
    if available(pool, champ_vesper_vale()):
        pick(champ_vesper_vale())
    elif available(pool, champ_tavi()):
        pick(champ_tavi())
    elif available(pool, champ_marcella()):
        pick(champ_marcella())
    elif available(pool, champ_stellar()):
        pick(champ_stellar())
    elif available(pool, champ_ren()):
        pick(champ_ren())
    else:
        pick( random_champion(pool) )
    end_turn()

# ---- every turn ----
keep camp_spawns = camp_spawn_tiles()
keep altar_ring = ring( altars(), 1 )
keep safe_altar_ring = ring( minus( altars(), ring(monolith_tiles(), 5) ), 1 )

if not alive() or channeling() or (not can_move() and not can_attack()):
    end_turn()

let at_spawn = contains( spawn_region(ally()), position() )
if at_spawn:
    let shards_bought = floor( gold() / 30 )
    let treasure_n = floor( shards_bought / 2 )
    let rest_after_treasure = shards_bought - treasure_n
    let jungle_n = floor( rest_after_treasure / 3 )
    let rest_after_jungle = rest_after_treasure - jungle_n
    let strength_shards = floor( rest_after_jungle / 2 )
    buy( shard_of(family_treasure(), stat_strength()), treasure_n )
    buy( shard_of(family_jungle(), stat_health()), jungle_n )
    buy( shard(stat_strength()), strength_shards )
    buy( shard(stat_health()), rest_after_jungle - strength_shards )
    # heal on spawn before heading back out, unless an enemy is already in reach
    if health() < max_health() and not exists(first(filter(enemies_visible(), in_attack_range()))):
        end_turn()

# retreat at 20% health normally, but at 50% when carrying gems
if not at_spawn and health() < 0.3 * max_health():
    if in_danger():
        move_towards( closest( spawn_region(ally()) ) )
        end_turn()
    recall()
    end_turn()
if not at_spawn and gems() > 0 and health() < 0.5 * max_health() and not in_danger():
    recall()
    end_turn()

let enemy = weakest( filter( enemies_visible(), in_attack_range() ) )
# an enemy on its own spawn is healed every turn: fighting it there never ends (00reverse-spiral)
if exists(enemy) and not contains( spawn_region(enemy()), unit_position(enemy) ):
    shield_up()
    fight_unit(enemy)
    attack(enemy)
    end_turn()

# tribute only with a worthwhile bag (or when hurt / late game)
let bag_ready = gems() >= 10 or round_number() > 1500 or health() < 0.5 * max_health()
if gems() > 0 and bag_ready:
    # an altar next to us works even when locked: tributing there attacks the lock (5 hits clear it)
    let altar = first( filter( altars(), within(1, position()) ) )
    if exists(altar):
        tribute(altar)
        end_turn()
    # walk to an open altar out of monolith reach (5); else any altar out of reach; else any altar
    let target = closest( minus( safe_altar_ring, ring(locked_altars(), 1) ) )
    if exists(target):
        move_towards(target)
        end_turn()
    let target2 = closest(safe_altar_ring)
    if exists(target2):
        move_towards(target2)
        end_turn()
    let altar_goal = closest(altar_ring)
    # every altar-adjacent tile is taken by a camp (01boss-battle: holes and a monolith): fight it
    if contains(camp_spawns, altar_goal):
        let blocker = first( filter( camps_visible(), in_attack_range() ) )
        if exists(blocker):
            fight_unit(blocker)
            attack(blocker)
            end_turn()
    move_towards( altar_goal )
    end_turn()

# one camps_visible() query per turn, reused for both attack checks
let camps = camps_visible()

let camp = first( filter( camps, in_attack_range() ) )
if exists(camp):
    fight_unit(camp)
    attack(camp)
    end_turn()

# nothing tributed by round 300 (00contest: only monoliths carry gems): go for monoliths too
if team_score(ally()) == 0 and round_number() > 300:
    move_towards( closest( minus( minus( camp_spawns, respawning_visible_spawns() ), golem_tiles() ) ) )
    end_turn()
let goals = minus( minus( minus( camp_spawns, respawning_visible_spawns() ), monolith_tiles() ), golem_tiles() )

# already standing on a cleared camp spawn: hold here so the capture timer keeps running
if contains(capturable_spawns(), position()):
    end_turn()

let goal = closest(goals)
# on a dead camp of a group that is not cleared yet, the closest goal is our own tile: walk to the
# nearest living camp instead (not a monolith or golem), so the group can be finished
if distance(goal, position()) == 0:
    let live = nearest(camps)
    if exists(live) and not contains( union( monolith_tiles(), golem_tiles() ), unit_position(live) ):
        move_towards( unit_position(live) )
        end_turn()
move_towards( goal )
let camp2 = first( filter( camps, in_attack_range() ) )
if exists(camp2):
    attack(camp2)
set_priority( 1 + random_int(100) )
end_turn()
```

## Version 2
Write it.
```
