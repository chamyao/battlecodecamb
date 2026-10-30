# Genome fuel: how the simulator prices a genome, and how it was calibrated

Genomes run on the genome runtime (`runtime/genome_rt.h`), not the policy interpreter, so the
interpreter's measured block prices (`docs/FUEL.md`) do not apply. In the simulator a genome pays:
- engine calls, through `cbs::Api` with `PriceTable::bot_wrapper()` (as the policy bot);
- its own operations, `F(n)` in the generated code, at `GENOME_OP_FUEL` (1) each: compiled
  arithmetic is nearly free in the bot (18 if-compares cost 11, constant loops fold away); plus
  `GENOME_LOOP_FUEL` (8) per loop iteration (`FL`; `FLU` adds 11 for a loop over units) and `FX(n)`
  for a memoised gene's hit (28 for a scalar, 65 for Tiles / Field: the copy out);
- the runtime's own work beyond those calls, `Ctx::extra()` in each primitive (simulator only),
  fitted below. Without it the simulator undercharged genomes ~6.7x (Oct 24).

## fuel()-threshold genes are high-variance between sim and real (Oct 30)

x8-140 (live v43) vs v40: real 81 / 140, sim 72 (ensemble 69.2). The rules are exact. At 1e8 both teams play the
same actions, and real 1x games replayed through the sim from their actions (oracle/replays/rereplay_v2.sh) show
0 state divergences. In 00lost-world game 37 the bots part at round 21: real x8 dashes, sim x8 does not.
x8's `dash_gate` needs `fuel() > 45000` at scoring time; other genes gate at 40k, 60k and 65k. On identical games
the real bot has a median 280-450 more fuel left at a turn's first decision. Whole games are 1.005-1.011 sim/real
for x8 and 1.000 for v40, so the gate tips toward "no dash" in the sim. Sim fuel x1.01 / x1.02 / x1.04 gives
76 / 68 / 68 (x1.00: 72): such genes make a genome's result jump with a few hundred fuel of price error rather
than shift. Gate genomes with fuel() thresholds on real games. v43 was also picked from 8 keepers by its real
score (keepers' sim 69.6-71.4), so its 81 carries some selection.

## First turn on cambc 4.0.0: start-up refit, group tile builds priced (Oct 30)

The reversed game (01elk-arena, A103823-w1 as team A vs v39a) is real 0-1008 and sim 900-468 at every fuel
level. At 1e8 fuel it replays action for action, both teams (8024 / 8505 actions). At the normal budget it
diverges on round 1: the sim's champions run a second pass (dash + move), the real ones do not. Real first
play turns cost ~190k against the sim's 140-170k.
- Start-up (`GenomePlayer::make_bot`): the 3.0.5 fit (17444 + 3.13 WH + 35.5 holes + 376 camps) was off by
  -191k to +8k on cambc 4.0.0 (holes no longer cost anything). Refit with the idle genome on all 70 maps (the
  largest first turn of team A): 24802 + 0.74 WH + 276 camps + 278 groups + 354 altars; resid sd 2.5k, max 7.1k.
- `group_tiles(g)` builds its set once per group and was priced 0: 46 + 148 per camp. First-turn probe genomes
  (genome/examples/firstturn: idle, one construct each on turn 1) put the miss at 10-14k per champion on
  01elk-arena / 00lanes for a genome touching every group, as A103823-w1's `mono_groups` does. With the price,
  ft_gt matches idle exactly and ft_mono is within 1.5k.

- `camp_spawns()` and `type_spawns(k)` builds were priced 0 too: 44 per camp, and 123 + 17.8 per camp per type.
  With these, ft_cs and ft_ts match idle to within 150 on all three maps.

Why it decided the reversed game: cambc 4.0.0 starts the first play turn with ~177.6k left. The bot's instance
start-up comes out of the 200k (probe: starter-cpp shows 177.6k remaining at its first play turn). v39a's first
turns need 201-206k (1e8 games), so the real bot is cut off on turn 1, while the sim, 8k cheaper there, fitted
them in. After the build prices, identical-game first turns are within ~1k on both teams (whole games 1.000 /
1.003). The game now resolves as in real: v39a wins 972-468 (real 1008-0); the side-swapped game also matches.
(My 1x trace of that game used the trace build, whose @@G printing costs real fuel. It cannot judge
first-turn passes at the normal budget: use normal builds for 1x fuel comparisons.)

Matchups after this (sim A wins / real; per-game agreement):

| matchup | original | now | real |
|---|---|---|---|
| A103823-w1 vs v39a | 83 (87/140) | 69 (87/140) | 68 |
| A103930-w1 vs v39a | 78 | 66 | 63 (lead's gate) |
| A61188 vs B792 | 73 (90) | 75 (90) | 83 |
| B792 vs B318 | 75 (90) | 76 (89) | 65 |
| B1145 vs A61188 | 56 (89) | 57 (94) | 61 |

Mean sim - real +5.0 -> +0.6; mean |sim - real| 11.0 -> 5.4.

## Sim optimistic for evolved genomes: extra() x 1.04 (Oct 30)

Search's gate (regate40/BIAS.md) had the sim above real for all 9 gated genomes (mean +9.8 / 140; worst:
A103823-w1 vs v39a, sim 83 vs real 66). Traced on cambc 4.0.0:
- Rules are exact. A103823-w1 and v39a each replay action for action on 6 maps (00lanes, 01elk-arena,
  02arena, 00crater, 02treasure-box, 00galaxy) at 1e8 fuel.
- Fuel was under, and more so on heavy turns. On identical games both genomes ran at 0.971-0.985 of real.
  Per turn, real = 1.04-1.09 x sim - ~1000: light turns are right, 40-70k turns 2-4k under. The per-op,
  per-gene and per-phase fits do not isolate one primitive. The profile build adds ~35% on the real side, and
  the gap does not follow chunks; it grows on taller maps.
- At 1x that shows up as budget hits. In 140 real games of A103823-w1 vs v39a, turns at the 100k cap per game:
  A103823-w1 9.1 real vs 6.5 sim, v39a 7.9 vs 6.3. The heavier genome was spared more in the sim.
- Sim fuel multiplier 0.975 / 0.95 took the sim from 83 to 77 / 74 A wins (real 68 in my 140 games).

Fix: every `extra()` price x 1.04 (`kExtraScale`). Host calls and own ops are unchanged; own ops x 2 or x 3
also moved the h2h but overshot whole-game fuel by ~900 per turn. With x 1.04:

| measure | before | after |
|---|---|---|
| whole game sim / real, A103823-w1 and v39a, 4 maps | 0.971-0.985 | 0.996-1.011 |
| heavy-turn quartile gap per turn | +1.8k to +2.7k | +0.1k to +0.9k |
| A103823-w1 vs v39a, sim A wins (real 68) | 83 | 73 (agree 87 -> 89 / 140) |
| A103930-w1 vs v39a, sim A wins (real 63, lead's gate) | 78 | 69 |
| A61188 vs B792 (real 83) | 73 | 79 (agree 90 -> 90) |
| B792 vs B318 (real 65) | 75 | 78 (agree 90 -> 89) |
| B1145 vs A61188 (real 61) | 56 | 52 (agree 89 -> 93) |

Over the five matchups the mean sim - real goes from +5.0 to +2.2 (mean |sim - real| 11.0 -> 7.4). Total per-game agreement over the four with
my real games goes from 356 to 361 / 560. Single matchups carry about +-7 of noise: 1% fuel flips about 20% of
these games. The part of a gate's offset that remains is selection: a genome is gated because its sim score is
high. Every genome's sim fuel moves with this change, by design. The per-primitive probe prices above are now
~4% over their probes.

## Engine 2.0.0 (cambc 4.0.0) port (Oct 30)

The ladder moved to engine 2.0.0: 70 maps (30 new), 42 new items (seven families of shards and emblems,
84 in all), six new item passives, a champion rebalance and `camp_group_capture_state`. Host fuel metering is
unchanged (the fuel probe fits the same on 3.0.5 and 4.0.0); `camp_group_capture_state` costs 7, like
`camp_group_cooldown`.

**Rules, measured with the differential tracer** (random item buys; `oracle/run_trace.py`): every passive was
fitted on the traced cases, then all traces were replayed line for line. 36 games on 10 maps (00ambush,
00anvil, 01elk-arena, 02arena, 02guardians, 02treasure-box, 01gold-rush, 00crater, 02famine, 00galaxy)
replay with no difference, capture state included.

| passive | effect (sim/src/game.cpp) |
|---|---|
| tribute (0.33) | tribute channel = ceil(duration * 0.67); 20 of 20 traced starts |
| capture (3.0) | capture takes 3 rounds instead of 5 while a holder is on the region: the timer is clamped to 3 when a holder steps on and before each round's countdown (holder from the start, joining midway, leaving after the first round) |
| prospector (0.25) | +25% (floored) of the holder's share of the gold_cluster / gem_cluster rewards only, added before bonus gold; a split's remainder goes with the first champion's share |
| hunter (50) | +50 kill gold |
| skirmish (0.05) | x1.05 damage against champions |
| collectors (0.01) | +1% damage per item family with an emblem held (any emblem, passive or not; distinct families) |
| monster / treasure | 1.15 (was 1.1) / +10% gold (was +20%) |

**Prices refitted on cambc 4.0.0 probes** (same method as calib5/6: identical games at 1e8 fuel against
the interpreted v23; per-call net fuel over p_empty):

| read | 3.0.5 price | 4.0.0 price | why |
|---|---|---|---|
| `capture_state`, `capture_timer` (new) | | RW_CAP 74 | calib9: group_cooldown + 31 (94 real); group_cooldown is 63 or 72 by context, so +-4% |
| `item_count` fetch | 206 | 374 | the item record doubled (84 entries); the cached read is unchanged |
| self items (`load_items`) | 210 | 378 | same record |
| champion fight data (attack_damage, cast_damage, shield) | 900 | 1650 | 84 items and the emblem families (calib4: now 0.97-1.01) |
| ward list | 1005 | 752 | calib6 and calib10 agree |
| `sight`, `ward_sight` | 423, 384 | 326, 274; off-map tile 217, 181 (was 0) | calib10: on and off the map |

No current genome (candidates, B1145, seed) calls any of these prims. The one that reaches them is the
runtime's own self-item load, which lists Tavi's SELL options on spawn. Every existing genome compiles to
the same C++ as before the port.

**Fuel budget:** cambc 4.0.0 gives the first draft turn 10M (100x the turn's 100k; it was 10x). The
simulator's `FuelBudget::draft_first_turn_multiplier` now matches; no genome uses more than ~50k there.

**Validation on cambc 4.0.0.** Whole game, sim fuel / real fuel on identical games (1e8 fuel against the
interpreted v23, sim at 1000x against `gconv1.pol`), same as the table below for 3.0.5:

| genome | 00lanes | 01elk-arena | 02arena | 00crater |
|---|---|---|---|---|
| A61188 | 0.975 (3.0.5: 0.974) | 0.968 | 0.991 | 0.983 |
| B792 | 0.965 (3.0.5: 0.962) | 0.959 | 0.972 | 0.968 |
| v28-emblem | 0.969 (3.0.5: 0.968) | 0.969 | | |

Head-to-head against real cambc 4.0.0 at 1x, 140 games each (all 70 maps, both sides; games paired by map
and side):

| matchup | real wins | sim wins | sim picks the real winner |
|---|---|---|---|
| A61188 vs B792 | 83 | 73 | 90 of 140 |
| B792 vs B318 | 65 | 75 | 90 of 140 |
| B1145 vs A61188 | 61 | 56 | 89 of 140 |

These games are chaotic at 1x: the same simulated matchup run at 0.99x or 1.01x fuel picks a different winner
in 24 and 28 of 140 games (at 0.97x / 1.03x in 38 and 44), so per-game agreement with real games cannot get
near 140 while the sim is ~3% under real fuel.

Identity: against the runtime before the price refits (922b98f), vs starter and head to head, at 1x and 100x,
A61188's games are fuel-identical (140/140 each). v28-emblem's fuel moves in every game, with the same winner
in 140/140: its `items_owned` read goes through the self-item load, now 378 (see above).

## State of calibration (Oct 25, memo hits typed and by call site)

Whole game, sim fuel / real fuel on identical games: cambc at 1e8 fuel against the interpreted v23
(`~/ws/bots/v23interp`), sim at 1000x against `gconv1.pol` with `--bot-seeds`. Real runs are from the current bot.

| genome | 00ambush | 00lanes | 01big-world |
|---|---|---|---|
| seed | 0.982 | 0.970 | 0.967 |
| B318 | 0.980 | 0.962 | 0.966 |
| B792 | 0.972 | 0.962 | 0.960 |
| A458 (arena A) | 0.988 | 0.974 | 0.971 |
| A61188 (live as v27) | 0.989 | 0.974 | 0.972 |
| a61188-mono (v28) | 0.989 | 0.971 | 0.972 |
| v28-emblem (v29) | 0.991 | 0.968 | 0.973 |
| B1145 (arena B #1) | 0.971 | 0.961 | 0.959 |
| B1092 (arena B, other species) | 0.973 | 0.938 | 0.957 |
| starter | 1.026 | 1.032 | 1.025 |
| idle (no consider()) | 0.984 | 0.969 | 0.983 |
| v23 | 1.031 | 1.030 | 1.022 |

Head-to-head against real cambc at 1x, 80 games each (both sides, all maps):

| matchup | real wins | sim wins | sim picks the real winner |
|---|---|---|---|
| A61188 vs B792 | 48 | 48 | 58 of 80 |
| B792 vs B318 | 40 | 42 | 52 of 80 |
| B1145 vs A61188 (held out) | 32 | 32 | 54 of 80 |

Evolved genomes run 1-6% under in absolute terms (starter and v23 2-3% over). So they may hit the
real per-turn cap a little more often than the sim predicts. Real cambc stays the upload decider.

Open gaps:
- (closed Oct 25: typed memo hits; v23 is now 1.01-1.02) v23 was over by 9-12%. Its per-option score path calls memoised genes (`here`, `walks`,
  `shop_pending`) that the compiler inlines. Such a hit costs ~30 in the bot against 73 charged, while
  the seed family's memo hits, called from large genes, are slightly under. A fix needs memo-hit cost
  per call site (inlined or not) from each genome's wasm; parked by the genome lead.
- A gene framed only through inlined callees keeps its old pricing (18 such genes in seed).
- Any runtime change can move the bot's real cost (simspeed's `combine()` did by ~5% on seed):
  rerun the real side after merging runtime changes from others, not only the sim.
- `walk_nearest` prices follow the policy bot's history-dependent search mirror; probes in isolation
  read 1.1-1.5x, in genomes it is in line.
- Later passes are priced 0: a free fit wants them negative, so complex genomes' second passes are
  priced high somewhere else (memo misses, most likely).

Protocol for a new primitive (each step is in a section below):
1. Add it to `lang.PRIMS` and the runtime, and put it in `lang.UNCALIBRATED`; the search cannot use
   it until it is priced.
2. Write a probe genome (`examples/calib5..8.genome` pattern: `update()` runs one probe per turn in
   rotation, plus an empty probe). Run `tools/prof_pair.sh` with `BIG_FUEL=1 OPP_BOT=v23interp
   OPP_SIM=/tmp/.../gconv1.pol` on 00ambush, 01big-world, 00lanes, 00packs, and compare steady
   per-call self fuel net of the empty probe, real against sim. For a cached record, probe a fetch
   and a fetch + hit.
3. Set the `extra()` prices until every probe is within ~0.95-1.05. Check whether its inlined bot code
   needs a frame (compile it alone with the bot's flags and look for the stack-pointer write); if so,
   add it to `lang.FRAMED_PRIMS`.
4. Remove it from `UNCALIBRATED`. Check that starter, seed, v23, B318 and B792 are identical
   (results and fuel, 80 games against builtin:starter, 1x and 100x) against the previous head.
5. For a pricing change (not a new primitive): report whole-game ratios before and after for the
   genomes above, plus 1x result changes and B792 vs B318 at 1x.
Tools: `tools/prof_pair.sh`, score variants (genomes that never act), `consider()` variants,
`GENOME_TURN_CALLS=1` per-turn lines (`@@TC r c passes opts ops extra spent`, then per-gene calls
for champion 0), and `GENOME_DEFS=GENOME_TURN_ORDER` in the bot. A cambc run needs its own bot folder
per concurrent run. Rebuild `genome/build` and `genome/build-prof` after every runtime change:
`genome_eval` refuses a genome compiled against another Ctx layout.

## Bot fix: camp groups' gold and gems were 0 in the real bot (Oct 25)

The bot's map build (the policy bot's `bot/src/bot_api.cpp`, vendored by `sync.sh`) fills each camp group's
camps but not its gold, gems or respawn. So `group_gold` / `group_gems` read 0 in cambc and the design
totals in the sim. `genome/bot/main.cpp` now fills them after the map build, from the camp designs, as
`sim/src/map.cpp` does. Checked against the engine's own per-group numbers (the camp layout's header,
`GENOME_DEFS=GENOME_VERIFY_GROUPS`): 0 mismatches over 29 / 15 / 12 groups on 01elk-arena / 01gold-rush /
00ambush.

v29-gg (`genome/arenab/cand/v29-gg.genome`, reads group_gems) against the interpreted v23 at 1e8. The bot
and the sim now take identical actions: 6505 play actions on 01elk-arena, 4221 on 01gold-rush. The
unfixed bot leaves the sim's game at action 16.

Every other Map field the runtime reads is filled by the bot: walls, bushes, holes, altars, altar_list,
spawn_mask, and camps (type, position, group). `camp_at` is left empty, but the runtime keeps its own
index. `group_reward` / `group_respawning` read the engine (camp_group_state), so they were right
already. Of the genomes here, only v29-gg reads group_gems / group_gold. A61188, v28, v29, B792 and seed
do not, so their real play was unaffected. The sim is unchanged; the policy bot computes group gems from
the designs itself.

## Memo hits by return type, and per-call-site inlining (Oct 25)

I read the bot's compiled code per genome: genes.cpp built as the bot builds it (wasi-sdk -O3, the host
bitboard, GENOME_BOT), with each gene's out-of-line calls listed from the relocations. Most memoised genes
are called, not inlined (`here` from ~30 sites in A61188). Score variants then read one memoised gene on
every option, never acting, against idle, measuring real cost per hit:

| return type | in the wasm | real cost per hit |
|---|---|---|
| Num | inlined | ~27 |
| Bool | inlined | ~35 |
| Tile | called | ~44 |
| Unit | called | ~57 |
| Tiles | inlined | ~68 |
| Num (large body) | called | ~30 |
| Tiles (large body) | called | ~80 |

So inlining moves a hit little; its return type (the copy out) sets the cost. The sim had charged 73 for
every non-set type and 78 for sets. Hits are now priced by type (`lang.MEMO_HIT`: 30 / 30 / 44 / 57 / 74).
- The per-pass price was refitted with it (later passes 0 -> 800).
- A caller-dependent extra (more from callers with a shadow-stack frame, as a whole-game fit suggested)
  was tried at +12 and +24. It brings whole-game ratios nearer 1, but on the two matchups used to choose
  prices it did worse (63 -> 58 -> 55 and 54 -> 52 of 80). The held-out matchup then decided: +12, below.

Held out (not used to choose prices), B1145 vs A61188, 80 real games: B1145 wins 32.
- bc70ece: sim 39, picks the real winner in 53 of 80.
- typed: sim 32, 52 of 80.
- framed +12: sim 32, 54 of 80.
Framed +12 won the held-out matchup by 2 games (within noise; summed over the three matchups typed leads
169 to 164), and by the agreed rule it ships: `lang.MEMO_FRAMED` = 12 per hit from a caller with a frame,
the price set at each call site (MH_).

80 real games each, A61188 vs B792 (real 48) and B792 vs B318 (real 40), at 1x:

| pricing | A61188 vs B792 | B792 vs B318 |
|---|---|---|
| bc70ece | 40 wins, 54 / 80 agree | 49 wins, 53 / 80 agree |
| typed hits, later 800 | 51 wins, 63 / 80 agree | 40 wins, 54 / 80 agree |
| + framed +12 | 48 wins, 58 / 80 agree | 42 wins, 52 / 80 agree |

BUY_LOCK is now listed only where consumables can be bought (on spawn or dead, as BUY_TP). Before, Tavi
off spawn listed it, and the engine refused it.

Identity against bc70ece, 80 games: 100x identical for starter, seed, v23, B318, B792 and B792 vs B318
(44). At 1x the results move with the prices (seed 79 -> 78, B792 79 -> 78, v23 78 -> 79; B318 and
starter keep their wins).

## A61188 vs B792 at 1x: why the sim moved from 49 to 40 of 80 (Oct 25)

80 real cambc games (A61188 vs B792 at default fuel, both sides on all 40 maps, bots from bc70ece):
A61188 wins 48. Per game, the sim agrees with real on 51 games at f23aaa0 and on 54 at bc70ece. On the 21
games that flip between the two, real sides with f23aaa0 on 9 and with bc70ece on 12. So bc70ece is the
more faithful simulator, game by game.

Its total (40) is further from real because its remaining errors lean one way: 17 games A61188 wins in
real but loses in the sim, against 9 the other way. A61188 is over-charged relative to B792.
- Whole game against v23: A61188 1.008-1.054 (00split 1.042, 00collision 1.054); B792 0.990-1.010.
- Under f23aaa0 both were over by similar amounts (A61188 1.03-1.06, B792 1.02-1.06). Their errors
  cancelled in the head to head, while each game was simulated less faithfully.
- Per gene, A61188's excess over B792 is spread out. `reach_camp` is `best(camps(), ...)` with a lambda
  that only calls `in_reach`, which the compiler inlines (~16 per camp less than charged). `walks` /
  `here` / `shop_pending` are memo hits that A61188 makes 1.6x as often. These are compiler-inlining
  effects (see the open gap on memo hits). A lower memo-hit price shifts every genome alike, so it does
  not fix the relative bias.
Tooling note: on 00collision and 01broken-curve the fuel file has 3 draft turns, not 5. Aligned at
offset 2, the games are identical (correlation 0.994).

## TELEPORT, BUY_TP, SELL (Oct 25)

New option kinds, after BREAK:
- TELEPORT (13): a teleport crystal to a tile within 3, landable as a move. Listed while we hold a crystal.
- BUY_TP (14): buy a crystal, on spawn or dead.
- SELL (15): Tavi on spawn, one sale per turn.
`examples/tpsell.genome` (the seed with all three scored first; Tavi buys no crystals and recalls every
60 rounds) against the interpreted v23. The bot and the sim take identical actions:
- 01broken-curve: 3164 play actions, with 106 teleports, 106 crystal buys and 35 sales.
- 00lanes: 4641 play actions, with 38 / 38 / 10.
No listed option of the three failed in the sim.

Prices come from genome pairs whose games are identical, differing only in consider() for one kind (scored 0):
- TELEPORT listed while a crystal is held: +15.9k real per turn against +16.8k in the sim (~45
  options a pass, each scored), so 60 per option on top of a 600 scan.
- The SELL check (Tavi) and the BUY_TP check: +45 and +130 real per turn. Their sim deltas also hold
  consider()'s early-return path, so they are not separated further.

Set algebra refitted after the simspeed `combine()` change: | and & are 178 + 1.88 x chunks, - is
166 + 2.9 x chunks (calib7 / calib8 probes 0.99-1.02 of real).

Against f18654e7, 80 games:
- 100x: identical for all five references and for B792 vs B318.
- 1x against builtin:starter: seed, B318 and B792 identical; starter 39 -> 41; v23 78 -> 78 with
  different games.
- B792 vs B318 at 1x: 47 -> 49 (the set-price correction).

## BREAK: attacking enemy altar locks (Oct 25)

The loop did not list a basic attack on a visible enemy altar lock, though it is legal (5 clear a lock;
a tribute at that altar hits it too). It is now option kind BREAK (12). Checks and prices:
- `examples/breaker.genome` (the seed, plus BREAK listed and scored 1000) against the interpreted v23 on
  01broken-curve. The bot and the sim take identical actions over all 2790 play turns, including 5
  BREAKs on one lock (r309-313), after which the lock is gone in both.
- Listing (consider() variants that list only BREAK, against only PICK): the altar scan costs 83 + 16
  per altar in the bot. The lock list is read only when an altar is within attack range (lock_at's
  price). Per option listed: 97, as ATTACK.
Against builtin:starter, 80 games, against 8296d5d4: identical at 100x for all five. At 1x seed, B318
and B792 (consider() genomes) are identical; starter 38 -> 39 and v23 79 -> 78, since genomes without
consider() now pay the scan, a real cost in the bot too.

## Calibration (Oct 24, cambc 3.0.5)

`examples/calib.genome` runs one probe gene per primitive per turn (in rotation). Built with
`GENOME_PROF`, each gene's inclusive fuel is logged (`@@GENE`), in the real bot (`bot/sync.sh` +
`cambc run`) and in the simulator. `tools/calib_compare.py` prints real/sim per probe for
00ambush, 01big-world (100x100, 169 chunks) and 00lanes (90x30, 48 chunks). The extra charges are a
constant plus a term in map chunks, set size or units, e.g.:

| primitive | real fuel | extra charged in the sim |
| --- | --- | --- |
| tile-set union / intersection / minus | 520-1170 | 224 + 3.1 x chunks (minus 4.0) |
| `near` | 420-670 | 122 + 1.03 x chunks |
| `size` | 136-262 | 80 + 1.0 x chunks |
| `field` | 2.5k (48 ch) - 35k (169 ch) | search 9 + (16 + expansions) x chunks, exact; + wrapper 527 + 8.1 x chunks |
| `field_avoid` | as `field` | search as `field` (+ 2 with a stop set); wrapper 528 + 7.1 x chunks |
| iterating a tile set | ~66-91 per tile | 970 + chunks + 81 x tiles |
| `nearest` | ~52 per tile | 120 + 52 x tiles |
| `camps()` | 640-2000 | 600 + 80 x visible camps |
| `visible`, `contains` | ~230 / 55-66 | 150 / 52 |
| `vision`, `ally_tiles`, `enemy_tiles`, `camp_tiles` | 262 (48 ch) - 515 (169 ch) | beyond the Api's price: 100 + 2.1 x chunks (vision), 148 + 1.1 x chunks (occupancy) |
| `walk_nearest` | 1.9k-7k (the bot's memoised nearest-by-walk) | none: the Api prices the bot's memo; sim 0.84-1.38x real per call |
| `type_spawns` | ~100-120 | 100 |
| `spawn_type`, `spawn_group` | ~55-65; first call fills a W x H table, ~3 per tile | 55; 2700 + 3 x W x H once |
| `is_awake`, `camp_spawn` | 37 / 29 | 16 / 17 |
| `camp_base_health/strength` | ~15 | 6 |
| `group_reward`, `group_respawning` | 47 | 26 |
| `alive`; `can_move`, `can_attack`, `channeling` | 12; ~24 | 4; 11 |
| `rand` | 20 | 12 |
| `consider(kind)` | 27 per call (once per kind per pass) | ops only (sim 35) |
| `me()` (cached), `dist`, `at` (field read) | ~20 / ~30 / ~70 | 18 / 30 / 70 |
| cached `enemies()` / `allies()` / `camps()` | ~27 | 27 |
| `camps()` (fetch) | 212 + 3 x chunks + 510 per camp (with `enemies()`) | 174 + 3 x chunks + 253 per camp |
| listing the legal options | ~55-60 per tile option, ~100 per unit option, fixed parts per section | by section (below) |
| scoring an option (the loop) | ~30 beyond the gene's own work | 30 per option scored |
| a champion's first turn (start-up) | 35k (41x30) - 131k (100x100) | 17444 + 3.13 x W x H + 35.5 x holes + 376 x camps |

Fields (re-fit Oct 24 after a5bbfcf, `examples/calib2.genome`): the bot runs the host search into
its own buffer, so the simulator now prices the search on its own expansion count instead of the policy
bot's distance-field memo; per call the profiled search matches the host to the fuel
(`@@FIELD` lines: real = 28 + 16 x chunks + expansions x chunks over 1,200 searches on three maps, of
which 19 is the profiler's own `fuel_remaining`), and whole probes to 0-2%. `field_avoid`'s stop set
follows the host's ComputeTo: the search runs until *every* reachable stop tile is reached (it used
to stop at the first one in the simulator, so a genome with a stop set of several tiles played
differently in the bot; one stop tile, as v23 uses, is unaffected).

Whole games, genome as team A vs starter (`tools/game_fuel.sh GENOME MAP`: cambc with the plain bot
and the simulator, same map), mean fuel per champion turn real / sim, and turns at the 100k cap
real / sim (the 4-6 first turns over 100k, on their 200k budget, count too). Oct 24, after the
listing rewrite and the re-fit:

| genome | 00ambush | 01big-world | 00lanes | 00rows |
| --- | --- | --- | --- | --- |
| starter | 28.8k / 25.5k (0.89); cap 6 / 10 | 23.4k / 24.1k (1.03); 16 / 23 | 28.9k / 28.7k (0.99); 21 / 30 | 16.8k / 15.9k (0.95); 13 / 11 |
| farmer | 25.7k / 26.8k (1.04); 7 / 7 | 23.8k / 24.6k (1.04); 7 / 7 | 20.1k / 20.8k (1.03); 2 / 2 | 15.9k / 16.3k (1.03); 0 / 0 |
| fartest | 58.8k / 57.2k (0.97); 6 / 6 | 89.8k / 87.8k (0.98); 6 / 6 | 30.8k / 29.3k (0.95); 0 / 0 | 29.3k / 27.7k (0.95); 0 / 0 |
| seeds/v23 | 59.8k / 60.9k (1.02); 1425 / 1228 | 61.2k / 59.5k (0.97); 1252 / 843 | 51.7k / 51.3k (0.99); 382 / 279 | 54.6k / 52.9k (0.97); 216 / 188 |

(Before: real starter 34-36k per turn, the sim 0.78-1.21x; the listing rewrite cut real starter
fuel by ~20-35%.) v23 runs near the budget, so its capped turns are sensitive: the sim's quartiles
are within ~4% of real, but it still caps 70-90% as often as the bot (its heavy genes over tile
sets, e.g. `group_threat`, `dash_path_ok`, `first_tile`, `altar_eta`, profile 0.66-0.74x real;
`closest`, the memoised nearest-by-walk, 0.88x).

**Exactness** (v23 genome as team A vs the interpreted v23, `policies/candidates/style-gconv1.policy`
through `bot/sync.sh`, against `genome_eval --bot-seeds`): with 1e8 fuel per turn (cambc
`--fuel 100000000`, `--fuel-mult 1000`; no suspensions) the four games match exactly (winner,
gems, end round, kills, deaths: 00ambush 857-1020 r1445, 01big-world 878-1020 r1443, 00lanes
1007-914 r989, 00rows 1024-939 r1741). At the normal budget the winner matches on all four; the
games drift with the genome's suspensions (it caps 200-1000 turns, the interpreted bot 3-5):
gems real / sim 577-1009 / 722-1011, 872-1001 / 757-1040, 920-1016 / 928-1003, 1017-939 / 1012-939.

Exactness checks (bot vs simulator on the same game) need an opponent the simulator plays exactly:
the interpreted v23 (`bot/sync.sh` + `--bot-seeds`) or a genome. Against starter-cpp the games diverge
by ~round 140, because builtin:starter differs from starter-cpp.

Re-run the calibration whenever `runtime/genome_rt.h`, `lang.py`'s codegen or `bot/bot_api.cpp`
changes, and check new primitives with a probe before relying on them. Tools: `tools/prof_pair.sh`
(a GENOME_PROF build in cambc and the simulator; `BIG_FUEL=1` for clean profiles without
suspensions), `tools/calib_compare.py`, `tools/game_fuel.sh`. In a profiled bot each gene call
costs ~80 fuel of profiler overhead in its caller (~18 in the simulator): compare self fuel after
subtracting it, and only for genes that are not cheap.

## First turn, the pass guard, cap-tail check (Oct 24, evening)

**First turn.** Profiled with `@@T1` checkpoints (main start, map built, Api ready, genes made, then
per phase of the first play_turn, printed on turn 2 with per-gene turn-1 totals) at 1e8 fuel. On
01big-world the frozen seed (genome/seed f739709) spent 367k on its first turn: ~51k of bot
start-up (11k before main, 32k map, 5k game and Api), ~200k in update() (its turn-1 caches) and
~115k in its passes. Runtime cuts:
- the terrain class table is built per map row on first use from the chunk words (a 256-entry
  spread table: ~1.6k per 100-tile row) instead of all W x H tiles at once (51k);
- spawn_type / spawn_group: a small open-addressing table keyed by tile index (~8.5k to build, ~115
  per lookup) instead of a W x H int table (~30k to fill);
- iterating a tile set of up to 32 tiles: an insertion sort instead of the counting sort's pass over
  every row (~2.5k -> ~0.8k for a camp group).
The seed's first turn on 01big-world: 367k -> 255k at 1e8 fuel. In real games against the
interpreted v23, its first-turn maximum on the 11 maps that capped at 200k on all five champions is
now 156k-198.6k on 9 of them. 01islands and 01yellow-brick-road still reach 200k: most of what is
left is the seed's own update() (mono_groups ~54k, ring ~20k, closest ~23k on 01big-world).

**Pass guard.** Optional entry gene `reserve() -> Num` (default 15000), read once per turn after
update(): no pass after the first starts with less fuel left than that. The simulator applies it on
its own meter. Seed, real games vs the interpreted v23, turns >= 100k: 01yellow-brick-road 25 -> 4,
01starvation 13 -> 6.

**Re-fit on identical games.** With 1e8 fuel per turn on both sides (cambc `--fuel 100000000`,
`genome_eval --fuel-mult 1000 --bot-seeds`, the genome against the interpreted v23), the bot and the
simulator play the same game (per-turn correlation 0.99-1.00), so real and sim fuel compare turn by
turn. `GENOME_TURN_CALLS=1` in a GENOME_PROF simulator prints each turn's gene calls (`@@TC`) for a
regression of the per-turn gap on them. Changes: static set reads 74, group_tiles 104 (the costs
taken back out of size / set algebra / nearest / iteration, which had absorbed them), memo hits 73
(scalar) / 78 (Tiles, Field), 575 + 1074 per later pass, consider() calls, cached me() 8. Mean fuel
per turn sim / real on identical games: seed 1.02 (01elk-arena) and 0.99 (01starvation), v23 1.12
/ 1.07, starter 0.94 / 0.98, farmer 1.08 / 1.09, fartest 1.12 / 1.06. No single per-construct
model fits all five within 5%: their errors are specific to the genome.

**Capped turns, seed vs the interpreted v23, normal budget** (real / sim per game, both sides):
00swirl 7 / 13, 01yellow-brick-road 4 / 1 and 8 / 4, 01elk-arena 11 / 9 and 6 / 11, 01starvation
6 / 8, 01islands 1 / 0, 01big-world 0 / 2. In total 43 real vs 48 sim.

**box_field(goals, walls)** (Oct 24): the walking field through the bot's distance-field memo (the
interpreter's move_towards path, dests = my tile). The bot fills only my 3 x 3 box, so reads are
valid there and up to my own distance (values above it, or outside the box, read unreachable in both
bot and simulator, which keeps them exact). A walker using it plays the same games as one using
field_avoid stopped at my tile (00lanes, 01big-world, bot and simulator identical). Per call, real /
sim: a far fixed goal 2.0k / 2.2k (00lanes), 3.3k / 3.7k (01big-world), against field_avoid's 3.5k
and 19.2k; nearby goals (camp spawns) 3.4k / 3.2k and 4.9k / 4.6k, dearer than field_avoid (1.7k,
4.5k), whose search is short then. Priced as the Api's memo price plus 300 + 6.5 x chunks.

**dash_field(goal, walls)** (Oct 24): the interpreter's dash_towards path (root = the goal tile,
dests = my 5 x 5 box without it); reads only on the box's tiles nearest to the goal (the first layer
the search reaches), unreachable elsewhere, identically in the bot and the simulator (a walker using
it takes the same 2720 / 5952 actions on 00lanes / 01big-world as the simulator). Per call, identical
games against the interpreted v23 (`prof_pair.sh` with OPP_BOT / OPP_SIM), real / sim: 4117 / 4077
(00lanes), 5388 / 4971 (01big-world), 6264 / 6132 (00ambush). Priced as the Api's memo price plus
1206 + 8.5 x chunks.

**Fight primitives** (Oct 24; `hits_to_kill` was removed later that day, being a model, not a rule):
`attack_damage`, `cast_damage`, `shield`, `hits_to_kill` follow the
engine's damage code (Game::apply_outgoing, damage_champion's reductions, shields first) on the
units' host data: each champion's items (emblem passives) and buffs (shields) are read once per pass.
Exact: `GENOME_CHECK_FIGHT=1` compares every attack / damage cast the loop makes with the target's
actual health and shield loss: 60,498 checks over B792, v23 and farmer games, 0 mismatches. Prices
(`examples/calib4.genome`, identical games against the interpreted v23): the items + buffs read 900
once per champion per pass; attack_damage 140, cast_damage 204, shield 60, hits_to_kill 236 + 26 per
hit; probes 1.01-1.09. Score variants show a cached call is what a genome mostly pays (attack_damage
~134, cast_damage ~200) and that `o.unit` costs ~20 (now priced; B318 / seed whole-game ratios
unchanged at 0.99 / 1.02). A test genome choosing fights by them takes the same actions in the bot
and the simulator (00lanes: 220 attacks, 117 casts; 00ambush; 01big-world); its whole-game fuel is
0.89-0.91 of real (the cost of calling its large score gene, not inlined, is not modelled).

## Raw SDK reads (Oct 24, SDK coverage audit)

Added: `cooldown`, `ability_kind/cooldown/range/radius/targets/modifier/duration/moveless`, `item_count`,
`unit_gold`, `buff_value`, `buff_turns`, `channel_left`, `group_cooldown`, `lock_hits`, `lock_enemy` (LANGUAGE.md).
These are host reads with no judgement. The bot glue (`genome/bot/bot_api_extra.cpp`) gained `champion_channel_time`, `camp_group_cooldown` and
`camp_buffs`. Records are cached per unit per pass in Ctx. Champions get a slot per handle and camps share
8 direct-mapped slots. Both caches live in Ctx, which sits on the bot's small stack. A heap cache was tried and
dropped: its first use cost ~1-86k fuel in the bot, depending on its size.

Prices beyond the Api's own charge (RW_* in genome_rt.h) were fitted on `examples/calib5.genome`. Each call ran
in a probe gene, and per-probe steady self fuel minus an empty probe was compared on identical games against the
interpreted v23 (1e8 fuel; 00ambush, 01big-world, 00lanes, 00packs). Real / sim, in bot fuel:
- cooldown (champion): 55 / 56. On a camp: fetch 128 / 126, second read 69 / 65.
- ability_* fetch 125 / 126, hit 46 / 47.
- item_count fetch 227 / 227, hit 31 / 33.
- unit_gold 36 / 36; channel_left 40 / 40; group_cooldown 72 / 72.
- buffs on a champion: fetch 131 / 124, hit 55 / 57. On a camp: fetch 121 / 117.
- lock_hits fetch 54 / 54, hit 25 / 25.
All probes fall at 0.95-1.02.

Whole game, the plain probe genome scores 0.90-0.94. The same genome with its probes removed scores the same
(0.90 / 0.95). The gap is in its score gene, which calls `nearest(camp_spawns(), me().pos)` per move option, and
not in the reads. starter, seed, v23, B318 and B792 stay identical (results and fuel, 80 games, 1x and 100x).

Batch 2 (`examples/calib6.genome`, same method; 00ambush, 01big-world, 00lanes, 00packs), real / sim:
- `enemy_wards` fetch 1209 / 1207 (two boards built), second read 239 / 239.
- `ward_charges` / `ward_cooldown` 79 / 79; `my_ward` 81 / 81.
- `ward_sight` 883 / 862 and `sight` 924 / 899, size() included. Constant across map sizes.
- `teleport_left` fetch 56 / 56, hit 24 / 23. Probed only with no teleport in flight.
- `priority` 42 / 42; `can_sell` 50 / 50.
All at 0.97-1.00. The SDK glue lives in `genome/bot/bot_api_extra.cpp`, so the policy bot's `bot/src/bot_api.cpp` is untouched.

## Guest pathfinding: wfield, path_step, path_len, territory (Oct 24)

Plain C++ in `genome_rt.h`, the same code in the bot (wasm) and the simulator; each call counts its
own work and the simulator charges the bot's measured fuel per unit (fitted on `@@PRIM` records:
per-call fuel and counters, `examples/calib3.genome` at 1e8 fuel on 00ambush, 01big-world, 00lanes;
`tools/test_guest` checks wfield (k = 0) against the engine's field and path_len / path_step against
field distances: 465k checks, 0 mismatches).
- `wfield` (Dijkstra, 10 circular buckets of doubly linked tiles over a padded cost grid): 20194 +
  85.7 per map tile + 414.7 per tile settled + 32.3 per empty bucket; per call within 0.1%. A full
  100x100 field is ~4.5M fuel (~45 turns of budget), 90x30 ~1.3M: in guest code every wasm
  operation, local reads and writes included, costs fuel. (A first version testing bitboards per
  neighbour cost 2x that.)
- `path_step` / `path_len` (A*, a bucket queue on (f, h): f rises by at most 2 per step, so 4 levels
  of h lists; a binary heap cost ~2x): 1427 + 380.9 per tile expanded + 134.1 per neighbour opened or
  improved + 27.3 per empty bucket scanned + 15.2 per step walked back (path_step); once per
  instance 5 per map tile for the scratch arrays. Per call p50 2.5%, p90 6%; per probe 0.93-1.06.
- `territory(mine, theirs, walls)`: two host distance fields (priced exactly, as `field`) and a
  compare in our code over the chunked field entries (chunks x 64): 641 + 22.31 per entry with a
  rival set, 531 + 17.15 per entry without (reachable from `mine`). ~300k on 100x100, ~80k on 90x30.
  The alternative, a two-colour search in our code, is a multi-source wfield (~4.5M on 100x100), so
  the host fields are kept. A first version reading the fields per tile through the generic
  accessor cost 4x.
Acceptance: per probe sim/real 0.93-1.06 (wfield 0.99-1.00, territory 0.93-1.00); a test genome using both
(`/tmp`-style walker: weighted field every 40 turns, A* near camps and to the altar) takes the same
actions in the bot and the simulator on 00lanes, 01big-world, 00ambush, 00rows (2674 actions on
00lanes; against the interpreted v23: games against starter-cpp diverge from builtin:starter,
whatever the genome); whole games at the normal budget, turns at the 100k cap real / sim: 2050 /
1984, 5076 / 4685, 4833 / 4691, 2706 / 2703; at 1e8 fuel mean fuel per turn sim / real 0.96-0.99.

## Listing the options (task 3, Oct 24)

The bot used to pay ~160-170 fuel per listed option (default-constructing an Option, copying it into
a vector, a non-inlined terrain lookup per tile): a ground-target cast over 81 tiles cost ~13.7k,
wards ~4k per pass. The listing is now written in place into a reused buffer (`OptionList`, 24-byte
`Option`, unit targets as an index into the pass's cached unit lists instead of a copied Unit),
scans tiles row by row over the terrain bytes, tests occupancy per tile on the three SDK masks (no
board unions), walks a precomputed shop list, and fetches only the consumables for the lock check.
Same options, same order (identical 80-game results at 100x fuel for starter, farmer, fartest, v23).
Real fuel per pass of an idle champion: 23.1k -> ~9-12k on 01big-world (cast 13.7k -> 5.4k,
ward 4.0k -> 1.5k, move 2.4k -> 1.8k); an idle turn 20.3k -> 11.8k.

Simulator price per listing section (`@@L` profile lines: fuel, options, scanned items and
activations per section, fitted on idle / starter / farmer in cambc on two maps), beyond the Api's
own charges: start 40 (alive); shop 10 + 24 per shop item + 55 per buy option; move 421 + 1.24 x
chunks + 70 per move option; attack 97 per option (the unit lists are priced in `camps()` /
`enemies()`); cast 248 per slot + 56 per ground tile scanned + 75 per unit scanned; ward 168 + 17.8
per tile + 40 per option; recall 11 + 50; tributes 59 per altar; a dead champion's turn 250.
Idle genome, whole games: real / sim 11.0k / 11.2k (00ambush), 11.8k / 12.0k (01big-world),
10.1k / 10.2k (00lanes), 9.1k / 9.2k (00rows), and within 3% on four more maps.

How the scoring was priced: "score variants" (genomes that list and score every option but never
act, so the game state is the same in the bot and the simulator) differ from the idle genome only in
the score body; the per-option difference against the idle genome (6 champions per map) isolates one
construct at a time (`me()`, `dist`, `at`, memo hits, loops over units, 18 compares, arithmetic).

## Shadow-stack frames and `nearest` (Oct 24, late)

A score gene using `nearest(camp_spawns(), me().pos)` only on MOVE options was priced at 0.90-0.94 of
real. I split it with score variants (they never act; identical games against the interpreted v23 on
00ambush, 00lanes, 00packs, 01big-world and 00rows) and found two causes.

- **Frames.** A gene whose bot code inlines a primitive with an address-taken local (an out-parameter
  of an engine call, a Bitboard) gets a wasm shadow-stack frame. Its prologue and epilogue run on
  every call, ~12 fuel, whether or not the branch with the primitive runs. With `me()` only in a
  branch that never runs, the bot pays ~1k per turn more than idle, and the sim used to charge 0.2k.
  The primitives that need a frame were found by compiling each one alone (noinline, the bot's wasi-sdk
  -O3 flags) and checking for the stack-pointer write: `lang.FRAMED_PRIMS`. In the seed genome every
  gene predicted framed is framed in its wasm; 18 more are framed through inlined callees and keep
  their old pricing. Those primitives' prices were fitted in framed genes, so they already include one
  frame each. The sim now charges the frame (12) only for a framed gene call that ran none of them
  (`FRAME_GUARD` / `FU_`, simulator only). The guard's destructor only records the fuel; the next charge
  bills it. A charge can suspend the coroutine, and a cancelled coroutine unwinds by exception, which must
  not leave a destructor.
- **`nearest`.** The bot walks every chunk of the set, unordered: +2 per map chunk and +20 base on top of
  46 + 52 per tile (gap 48 on 16 chunks, 356-363 on 169).

After the fix, real / sim extra over idle:
- `nearest(camp_spawns(), me().pos)` per MOVE option: 0.99-1.00 on all five maps.
- `me()` in a branch that never runs: 1.00.
- `me().pos.x` per MOVE option: 0.86-0.89. The ~130 per turn left over is `me()` itself.

Open: the idle genome against the interpreted v23 is 0.93-0.95 of real (it matches against starter).
Split per champion (the sim's turn order is the engine's), the gap grows with options listed,
~13 per option (champions with 30 / 53 / 93 / 110 options: 0.98 / 0.93 / 0.91 / 0.91). The
per-option price (30) was fitted on seed and v23, so it is not refitted here. To split a real game by champion,
build the bot with `GENOME_DEFS=GENOME_TURN_ORDER`; the sim's `GENOME_TURN_CALLS=1` lines (`@@TC r c`) give
the turn order, which is the engine's.

Whole game, the same games against the interpreted v23 (sim old -> new pricing, real/sim):
- starter: 0.965 -> 0.993, 0.907 -> 0.934, 0.956 -> 0.982 (00ambush, 00lanes, 01big-world).
- seed: 1.006 -> 1.014, 1.007 -> 1.017, 0.993 -> 1.000.
- B318: 1.000 -> 1.008, 0.985 -> 0.995, 0.986 -> 0.994.
- B792: 0.981 -> 0.988, 0.964 -> 0.973, 0.968 -> 0.974.
- v23: 1.087 -> 1.095, 1.105 -> 1.119, 1.085 -> 1.095.
Against builtin:starter, 80 games: identical at 100x for all five genomes. At 1x, seed, B318 and B792 are
identical; starter wins 40 -> 41, v23 79 -> 78, as their suspensions rise with the higher price.
B792 vs B318 at 1x: 44 -> 44 wins, a few games different.

## Set algebra and the pass price, refitted on the arena genomes (Oct 25)

Whole game against the interpreted v23, the arena's top genomes were A458 1.00-1.02, B1145 0.97-0.99 and
B1092 0.94-0.98. B1092's costliest gene, `closest` (19% of its fuel, 0.82 in the profile), has a fallback
that A458's lacks: `ring(s, 2)`, a `near` plus a union for every tile of `s`.

`examples/calib8.genome` probes the set operations alone (00ambush, 01big-world, 00lanes, 00packs).
Static set reads and `size` match (0.95-1.01). Each operation that makes a new set is under by ~80-110,
once per operation: one union is under 74-107 and three unions 220-311. Refitted prices:
- `near`: 202 + 1.06 x chunks (was 122 + 1.03).
- `|` and `&`: 188 + 2.88 x chunks (was 76 + 3.1).
- `-`: 176 + 3.9 x chunks (was 77 + 4.0).
The pass price had been fitted per turn on seed and v23, so it had absorbed their set-op shortfall. It is
refitted jointly on seed, B318, B792, starter, A458, B1145 and B1092 x 3 maps: first pass 575 -> 93,
later passes 1074 -> 474. A fit with a free later-pass term wants it below zero, so it is bounded to keep
both positive.

Whole game (real/sim; 00ambush / 00lanes / 01big-world):
- seed: 1.014 / 1.015 / 1.000
- B318: 1.012 / 1.007 / 0.999
- B792: 1.001 / 1.003 / 0.991
- starter: 0.985 / 0.996 / 0.983
- A458: 1.020 / 1.019 / 1.005
- B1145: 1.000 / 1.001 / 0.988
- B1092: 1.000 / 0.974 / 0.984
The seven span 0.974-1.020, against 0.934-1.017 before. v23 is 1.11-1.14; it was 1.10-1.12, over for
reasons outside these constructs. The idle genome drops to 0.88-0.91: it lists ~66 options a turn with no
consider(), and the per-option gap above is still open.

Against builtin:starter, 80 games, 100x: identical for all five reference genomes. At 1x the results move
with the prices: seed identical; B318 and B792 79 -> 78; starter 40 -> 38; v23 79 -> 78. B792 vs B318 at
1x: 44 -> 48 of 80.

## Joint per-option refit (Oct 25): what it found

Per-turn records (`GENOME_TURN_CALLS=1` in the profiling sim): `@@TC r c passes opts ops extra spent`, then
calls per gene for team 0's champion 0. Fitting each genome's per-turn gap (real - sim) on these, over
11 genomes x 3 maps:
- Counted operations (F) are 2-6% of sim fuel; primitive extras are 70-90%.
- The gap per option scored follows the score's shape, not a shared constant. Simple scores (idle,
  calib5, starter) are under by 2-17 per option. The seed family is over by 30-40, A458 by ~60, v23 by ~78.
- Score variants show why. A memoised gene's hit costs ~30 in the bot when its caller inlines it,
  against 73 charged, while the seed family, whose callers are large genes, is slightly under on memo
  hits. The real price depends on the compiler's inlining, which no per-construct price captures.
- `slot_kind` / `slot_range` were charged 90, but the bot reads them from a per-pass cache: ~44
  (score variant, slot_kind per CAST option: 2.05 -> 1.10 of real). That moves v23 from
  1.135 / 1.111 / 1.109 to 1.109 / 1.091 / 1.088 (00lanes, 00ambush, 01big-world). The others barely
  call it and are unchanged. Against builtin:starter at 1x, v23 is now identical (79 wins).
- A bounded joint fit (pass, option and memo-hit prices) would bring v23 to ~1.03-1.04 and idle to
  ~1.02, but widens starter (to -4%) and B1092 (to +4%), and needs the first pass at ~1960. It is not
  applied; see the message log for the decision.

## The fixed turn and per-option prices, from consider() variants (Oct 25)

Idle variants whose `consider()` drops kinds from the listing (never act; identical games against v23):
- An empty turn (only PICK listed) costs ~1130 in the bot. The sim charged ~525, because the 7b2ff02f
  pass refit had moved fixed cost into the complex genomes' later passes.
- Dropping CAST saves 4.3k real against 4.1k in the sim; dropping WARD 2.54k against 2.28k; dropping
  MOVE 1.0-1.5k against 1.1-1.7k. All listing together was under by ~500-650 per turn, ~7.5 per option
  for idle's ~66 options.
Refit, bounded at zero:
- first pass 93 -> 700 (the measured empty turn);
- per option scored 30 -> 37;
- later passes 474 -> 0 (a free fit wants them below zero: complex genomes' second passes are priced
  high elsewhere).
Whole game (real/sim; ambush / lanes / big-world):
- empty turn: 1.003 / 0.995; idle: 0.998 / 0.982 / 0.995 (was 0.46 and 0.88-0.95)
- calib5: 0.976 / 0.975; starter: 1.013 / 1.023 / 1.015
- seed: 1.019 / 1.022 / 1.005; B318: 1.017 / 1.014 / 1.004; B792: 1.005 / 1.009 / 0.995
- A458: 1.024 / 1.026 / 1.010; B1145: 1.004 / 1.008 / 0.993; B1092: 1.004 / 0.979 / 0.988
- v23: 1.102 / 1.123 / 1.099 (its per-option memo hits, above).
80 games against builtin:starter: identical at 100x; at 1x seed, v23 and B792 are identical to 8a94ac7,
B318 79 -> 78, starter 40 -> 38. B792 vs B318 at 1x: 49 (afc31666) -> 45.

## Bot-side costs worth knowing (what the search pays for)

- A single host bitboard bit test or set costs ~120-170 fuel in the bot. The runtime keeps static
  terrain as plain bytes and caches each camp group's tiles; dynamic sets still pay it.
- A distance field costs 9 + (16 + expansions) x chunks in the host, plus ~530 + 8 x chunks around it.
- A memoised gene's result is copied out on every call (~28 fuel; ~65 for Tiles or Field), and a
  field read costs ~70: read a field once into a local where it is used many times.
- Distance fields cost ~100 fuel per map chunk. A genome that rebuilds its goals and field on every
  pass of the loop pays that each pass (the starter genome: ~2.5 passes, ~33k per turn).
- Row-major iteration over a host bitboard uses an insertion sort (quadratic per chunk row); the
  runtime uses a linear counting sort instead, and `nearest` breaks ties by (y, x) so it can take
  the host's cheap order.
