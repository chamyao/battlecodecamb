# Fuel prices (measured against cambc 3.0.5)

Fuel is part of the game state (see `docs/STRATEGY.md`). This file records what each
kind of work costs a C++ bot, measured on the official engine, and how the simulator's
price table (`sim/src/fuel.cpp`, `PriceTable::measured()`) was derived.

## Method

`oracle/bots/fuelprobe` brackets each probe with two `fuel_remaining()` reads and prints
`@@F <name> <n> <fuel>`; an empty bracket costs 2, which is subtracted. Every price below
is therefore what one raw import call costs a bot **including its own call-site
instructions** (argument setup, result loads). Builds are `--release` (as on the
platform), with `--fuel 1e9` so probes never suspend. The draft bot of team A probes the
geometry and static queries on the full map; every champion probes the state queries
every fifth turn while random-walking against `starter-cpp`, so visibility varies.

Maps: 00elkring (30x30), 00lanes (90x30), 00monolith (50x50), 01starvation (80x80),
01big-world (100x100). Reproduce with `oracle/run_fuelprobe.sh MAP` then
`python3 oracle/tools/fuel_fit.py MAP...`.

`chunks` below is `ceil(W/8) * ceil(H/8)`: bitboards are stored as one 64-bit word per
8x8 chunk (16 on 30x30, 49 on 50x50, 169 on 100x100), and board-sized work costs about
one fuel per word.

## Results

**Guest code.** Fuel is Wasmtime fuel: about one unit per wasm instruction executed. A
1000-iteration xorshift-and-add loop costs 23,508 (about 23.5 per iteration). For scale,
the official `starter-cpp` spends 38-50k of its 100k budget per turn (165k on its 2x
first turn), almost all of it in guest code.

**Host calls are cheap.** Constant-price calls (independent of map size and of the number
of units returned in every sample we took):

| Fuel | Calls |
| --- | --- |
| 1 | `my_champion`, `my_team`, `fuel_remaining` |
| 3-5 | `cancel_channel` 3, `num_allies`/`num_enemies` 4, `buy_consumable` 4, `sell` 4, `draft_num_rounds` 4, `champion_is_alive`, `champion_identity`, `champion_design`, `champion_restrictions`, `champion_items`, `champion_consumables`, `champion_gems`, `champion_gold`, `item_info`, `consumable_info`, `spawn_region`, `attack` (failing), `buy_item` (failing), `submit_gems` (failing), `bb_set` 5 |
| 6-9 | `champion` 6, `champion_ability_props` 6, `champion_cooldown` 6, `champion_ability_damage` 6, `bc_round_number` 6, `bc_metadata` 6, `bc_map_symmetry` 6, `draft_get` 6, `map_camp_at` 6, `champion_wards` 7, `champion_channel_time` 7, `champion_can_sell` 7, `camp_state` 7, `camp_design` 7, `camp_group_state` 7, `camp_group_cooldown` 7, `bc_submitted_gems` 7, `map_camp_info` 7, `df_get` 7, `champion_can_shop` 8, `champion_priority` 8, `camp` 8, `place_ward` (failing) 8, `debug_dot` 8, `bb_test` 8, `champion_buff_data` 9, `read_shared_memory` 9, `write_shared_memory` 9 (1 or 8 bytes) |
| 10-11 | `wards`, `teleports`, `altar_locks`, `ward_at`, `champion_at`, `camp_at`, `is_visible`, `has_champion`, `has_camp` 10; `allies`, `enemies`, `champion_ward_positions`, `camp_buffs`, `cast` (failing) 11 |
| 28-29 | `move_to` 28, `set_priority` 29 |

Size-dependent calls:

| Call | Fuel | Fit quality |
| --- | --- | --- |
| board results (`board_vision`, `bc_champion_vision`, all `*_occupancy`, `bc_map_mask`, `bb_zero/one/not/union/intersect/xor/is_zero/is_equal/num_set_bits/shift/reflect`, linear import/export) | 2-8 + chunks | exact |
| `hypothetical_vision` / `ward_vision` | 9 / 8 + 2 * chunks | exact |
| `bb_get_set_bits` | 11 + chunks + n (positions returned) | exact |
| `bb_draw_circle` / `bb_draw_chebyshev` | ~16 + chunks covered by the shape's box | +-2 |
| `df_compute` / `df_compute_to` | 9 / 10 + 16 * chunks + expansions * chunks | exact |
| `bb_shadow_cast` | ~5 + 2 * chunks + 0.56 * tiles scanned | median 5%, max +-120 |
| `bb_reachable` | ~chunks + 11 * BFS layers that grew | median 15%, max +-90 |
| `df_copy` | 12 + 144 * chunks | exact |
| `read_draft_memory` / `bc_submit_draft_memory` | 8 / 5 + n / 8 (n bytes) | exact |
| `map_camp_layout` | 91-279 (grows with camp count) | |

Typical magnitudes: a full distance field on 100x100 costs a few thousand fuel; a
shadowcast at radius 8 costs 100-400.

**Our own geometry compiled into the bot costs far more.** The simulator's
`sim/src/bitboard.cpp` (bit-parallel, `__int128` rows), run on the same inputs inside the
wasm bot, costs about 115 fuel per tile scanned (shadowcast, vs 0.56 on the host),
2-3k per BFS layer (reachable), and 170-240 per visited tile (distance field, vs about
chunks/64 on the host). That is 30-200x the host versions. **Real bots should always use
the host primitives**; the `cbs` versions are for the native simulator. (Wasm has no
native 128-bit integers, and the host versions are one wasm call each.) `cbs::reachable`
was also rewritten to avoid an 80 KB stack array that overflowed the bot's wasm stack.

**SDK wrapper overhead** (`cambc.h`, same release build):

| Wrapper | Fuel | Raw equivalent |
| --- | --- | --- |
| `cambc::bitboard` construction (heap allocation + zero) | 172 (30x30) to 306 (100x100), about 150 + chunks | `bb_zero` 2 + chunks on an existing buffer |
| `a \| b` on bitboards (allocates the result) | 197 to 331, about 180 + chunks | `bb_union` 6 + chunks |
| `map::walls()` | 171 to 305, about 155 + chunks | `bc_map_mask` 5 + chunks |
| `self().position()` | 73 | `champion` 6 |
| `vision::champion_tiles()` | 429 to 850, about 385 + 2.75 * chunks | |
| `distance_field` construction | 0 | |

The wrappers' cost is mostly allocation and per-call validation. A fuel-tight bot should
keep preallocated raw buffers and call the imports directly.

## Calibrating the simulator to the deploy bot

The prices above are for raw imports. A policy run by our deploy bot (`bot/`: the grammar
interpreter over `bot/src/bot_api.cpp`) pays for its own interpreter code and its API
wrappers as well. The simulator originally charged interpreted policies a placeholder 10 fuel
per block, which was 30-100x too low. It is now calibrated against that bot directly. The
calibration has to follow the bot: the host-backed Bitboard and the distance-field memo
(deploy/v0 a4dca15 onwards) cut its costs 3-10x, and a stale table made the simulator report
~2,200 suspensions per game for fs-1 where cambc shows essentially none.

**What the simulator runs for the bot's composite calls.** `distance_field` and
`nearest_by_walk` go through the bot's memo (`sim/include/cbs/field_memo.h`, shared code:
`bot_api.cpp` runs it over host imports, `sim/src/api.cpp` over the simulator's BFS). Its cost
depends on whether a call hits (a scan) or misses (a host search, 16·chunks + chunks per
layer), so the simulator runs the identical memo to decide. The simulator's answers still
come from its own BFS. The host's ComputeTo with several dests stops only once every dest is
reached; `cbs::distance_field(..., all_dests)` reproduces that exactly (geom fixtures: 240
multi-dest cases match cambc). `visible_camps` is priced on the occupied camp tiles, as the bot
walks them. All this applies when the price table is `PriceTable::bot_wrapper()`
(`bot_memo`), i.e. for the policy player; other players keep raw prices. Memo decisions must
change only in field_memo.h; wrapper changes in `bot_api.cpp` (what is read, `qr`, `have_me`)
must be mirrored in `Api::distance_field` / `nearest_by_walk`.

**Measurement.** `[POLICY=policies/x.policy] [EVERY=10] oracle/run_bot_profile.sh MAP...`
builds a profiling copy of the bot running POLICY (`bot/profile_patch.py`; `bot/` itself is
untouched) and plays it against starter-cpp with `--fuel 1e8`, so costs are never
truncated. Output goes to `/tmp/prof/<policy>/<map>/`. Every EVERY-th turn, and every draft
turn, it logs the **self** fuel and the work done for each interpreter block and each API
wrapper call. Self fuel excludes child blocks, API calls and the profiler's measured window.
The work logged is BFS layers searched and memo misses (distance fields), dest and reachable
tiles, occupied camp tiles and occupancy-cache refreshes. It also logs the turn total. The
same game is then played by the **unpatched** bot (`plain/`). Decisions are identical, so the
game is identical; the script checks this on the opponent's per-turn fuel.

**Coverage.** `policies/coverage.policy` plays v2 but also evaluates every block that v2 and
fs-1 never reach: draft probes, terrain and camp-type sets, shop and consumables, team memory
and unit queries. Each probe is a separate `let` or `if` so that short-circuiting cannot skip
it. The interpreter allows only 8 variables per type, so most probes are `if` statements or
`buy(x, 0)` calls that bind no variable. Profiled with `EVERY=1`, it exercises all 147 blocks.

**Model.** `oracle/tools/fuel_calibrate.py /tmp/prof/*/*` pools every profiled run across
policies. It fits each block and wrapper as a non-negative linear model over features the
simulator can compute: map rows H, chunks ch, layers x chunks, misses (x chunks), tiles, cache
refreshes (x H), camp and group counts, and input-set size. Each call gets only physically
meaningful features. The per-turn step loop is fitted for relative error, each run counting
equally.

**Profiler distortion.** The profiling build costs more than the per-scope window it
subtracts: its fuel probes around every block and API call get in the way of the compiler.
Uncorrected, the model over-predicted the plain bot's real fuel by 25-56% on every run. Every
champion logs on the same turns, so each logged round pairs with the plain bot's real fuel
for that round, and the script fits
`real ≈ 0.943·model − 102·blocks − 52·API calls − 75·turns` (3825 rounds). The generated
tables carry the scale on every fitted charge and the rest in the per-turn term.

The script generates:
- `sim/src/fuel_bot_gen.inc`: `PriceTable::bot_wrapper()`, the API as called through
  `bot_api.cpp`. A `cbs::Player` may return it from `prices()`; the policy player does.
- `interp/src/block_costs_gen.inc`: per-block self costs and `INTERP_TURN_COST(blocks, H, API
  calls)`. The interpreter charges each block when it finishes, and a Charge guard counts the
  block's own work. `interp::load_program` (the simulator's text loader) **refuses a policy
  that uses a block with no measured row**, so an unmeasured block is never silently
  guessed. If a new block is added, extend coverage.policy and re-profile.
- `docs/fuel_calibration.json`: all fits with sample counts and errors, and the correction.

The bot's start-up (map, camp layout, allocator) costs each champion's first turn about
22k + 2.2·W·H + 288·camps + 394·groups more (24 cambc games of v7 and fs-1 on deploy/v0 with
interp/v0 6297d62, MAE 1.3k, against the 200k first-turn budget). Since ee76a6e the policy is embedded
pre-parsed; parsing it had cost ~170 fuel per program node, ~40k for v3. Re-fit this after
start-up changes with the scratch comparison of first turns (cambc vs `fuel_turns`): first
turns now match within 1% (v5d 83.3k vs 83.0k mean, fs-1 73.6k vs 74.2k). It is not in the profile, so it is charged from a hand fit in `interp`.

Current calibration (deploy/v0, Oct 23 refit on the bot with the dash check; `real = 0.970·model − 135.4·blocks − 38.6·API
calls + 110·turns`, 4668 rounds):
- coverage.policy (EVERY=1, 400 rounds) on 00collision, 00elkring, 00lanes, 00monolith,
  01big-world and 01hooks;
- fs-1, v7zg-cast and tune-1 (EVERY=10, 800 rounds) on those maps plus 00gem-fields, 00rows
  and 01starvation;
- tune-1 vs v7zg-cast on 01big-world, the full game (EVERY=10), for heavy big-map searches.
Runs from different bot builds list their API scopes differently; `fuel_calibrate.py` maps
them by name.
The profiler-distortion correction is fitted on the real policies' runs only: coverage.policy's
turns (dozens of probe blocks each) are unlike any real policy's, and including them moved
real policies (01big-world, tune-2 vs tune-1, lost its exact match when the gap-block probes
were added).

Largest items, in profile fuel before the scale (fuel; mean and mean absolute error over the
samples):

| Block / wrapper | Model | Mean | MAE |
| --- | --- | --- | --- |
| `api:distance_field` | 2178 + 4.4·ch + 20.5·miss·ch + 1.05·layers·ch + 204·dests | 3667 | 641 |
| `api:nearest_by_walk` | 1779 + 10.8·ch + 15.3·miss·ch + 1.51·layers·ch + 2.1·tiles | 3581 | 769 |
| `api:visible_camps` | 186 + 162·occupied camp tiles | 682 | 131 |
| `in_danger()` | 311 + 92·camps (early exits: MAE ~30%) | 5957 | 1772 |
| `enemies_within(Num)`, `local_strength(Num)` | 1160, 2565 | | 74, 211 |
| `api:vision` (unseen camp tiles block paths; once per occupancy refresh) | 66 | | 35 |
| `capturable_spawns()` | 83 + 125·groups + 5.8·camps | 3124 | 44 |
| `move_towards(Tile)` | 1467 + 11.7·ch + 12.6·refresh·H | 2459 | 81 |
| `dash_towards(Num,Tile)` | 1375 + 10.6·ch + 43·dests + 1.06·layers·ch | 2777 | 293 |
| `closest(TileSet)` | 1095 + 13.1·ch | 1804 | 22 |
| `respawning_visible_spawns()` | 501 + 132·groups | 3383 | 189 |
| `camp_spawn_tiles()` | 1964 + 17.5·ch | 2989 | 629 |
| `filter(UnitList,UnitPred)` | 1039 | 1039 | 348 |
| `union`, `minus` (TileSet) | 595-661 + 3-4·ch | 837-855 | 0-56 |
| `ring(TileSet,Num)` | 235 + 6.4·H + 30·input tiles | 732 | 16 |
| `spawn_region`, `altars()`, `walls()` | 133-352 + ch | 192-410 | 0 |
| `api:camp`, `api:champion`, `api:my_champion`, `api:*_occupancy` | 30, 42, 10, 14 + ch | | 0 |
| simple blocks (`and`, `or`, `not`, arithmetic) | 150-400 | | 0-110 |
| step loop, per turn | 30 + 69.2·blocks + 0.079·blocks·H | | 481 |

Board work now goes through host imports (~6 + chunks fuel per board operation), so
board-valued blocks cost hundreds rather than thousands.

**Validation.** `oracle/tools/fuel_validate.py /tmp/prof/*/*` applies the corrected model to
every logged round and compares it with the plain bot's real fuel for that round. This is
in-sample for the correction.

| Runs | Predicted / real total | Per-round error, median | 10-90% |
| --- | --- | --- | --- |
| coverage (6 maps, every round) | 0.953-1.018 | −4.3% to +2.7% | within [−6.2%, +4.5%] |
| fs-1 (9 maps) | 0.956-1.025 | −2.3% to +3.3% | within [−10.5%, +10.3%] |
| v3 (9 maps) | 0.986-1.046 | −1.4% to +5.1% | within [−8.1%, +10.4%] |

Out of sample, the simulator itself (`interp/tools/fuel_turns --enforce`) was compared with
full cambc games at default fuel on 12 maps (00ambush to 00interlock; different games, since
the drafts differ). Champion turns after the first, in fuel per turn, and first turns:

| | mean | p50 | p90 | p99 | max | capped | first turns: mean, max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v3, cambc | 19921 | 19837 | 33452 | 46783 | 67005 | 0 | 120786, 166300 |
| v3, simulator | 19865 | 19650 | 34333 | 47825 | 70944 | 0 suspensions | 119133, 165861 |
| fs-1, cambc | 14631 | 12770 | 27356 | 39930 | 61126 | 0 | 112342, 156510 |
| fs-1, simulator | 13998 | 11901 | 26985 | 40539 | 60900 | 0 suspensions | 113533, 158273 |

Known weak spots:
- Per call, `distance_field` and `nearest_by_walk` carry ~17-21% MAE. A memo hit through the
  walls-changed proof costs more than a same-walls hit, and the profile does not separate
  them. Per round this averages out.
- `or`/`and` are bimodal (short-circuit or not), charged at their mean (MAE ~100).
- `nearest_by_walk`'s history (bot_api.cpp: after a dear reachable mask, a capped
  origin-rooted search on memo misses) is mirrored in `Api::nearest_by_walk`. The bot decides
  on the mask's *measured* fuel; the simulator uses an estimate, max(190 + 1.7 per tile reached,
  0.9·chunks·D) (the bot session's measurements: compact regions vs long open walks),
  so its choice of path can differ on a few turns.
- The model is for this bot build: re-run `run_bot_profile.sh` (coverage, v2 and fs-1) and
  `fuel_calibrate.py` whenever `bot/` or the interpreter changes (a run takes ~30 minutes
  on 4 cores), then refit the start-up constants in `Interp::turn` from full cambc games.
- The simulator's bot pricing costs speed: 200 games of v2 vs starter take ~6.9 s against
  ~5.4 s with raw prices (the memo runs its own searches on misses).

**Exact per-turn check.** Policy-vs-policy games reproduce cambc exactly when the simulator
seeds policies as the bot does (docs/ENGINE_FINDINGS.md, "Match seeding"), so fuel can be
compared turn by turn on the identical game:
`interp/tools/fuel_turns A.pol MAP --enforce --bot-seeds --opp B.pol` against team A's `.fuel`
in the bundle of `cambc run botA botB` (skip the draft turns, one per draft round). The
built-in starter does not play exactly like starter-cpp, so games against it diverge.

v7zg-cast vs fs-1, 12 maps (00ambush to 00interlock), deploy/v0 with interp/v0 d9b8cde. All 12
games are identical (same end round and gems):

| | value |
| --- | --- |
| turns compared | 75,713 |
| total fuel, simulator / cambc | 1.044 (per map 1.008-1.078) |
| per-turn error (turns > 3k), median | +3.5% |
| 10-90% / 1-99% | [−6.1%, +14.3%] / [−17.1%, +27.5%] |
| heaviest turns | within 1% (e.g. 153.9k vs 153.0k, 142.0k vs 142.0k) |

On the same games fs-1 (team B, `--side b`) comes out at 1.008 in total (median −0.8%,
10-90% [−9.0%, +11.8%]), so the +4% is specific to v7zg-cast, not a global offset. (Re-run on
d3f0df8 with the refined mask estimate below: v7zg-cast 1.045.)

**Running total.** The per-turn correction (`INTERP_TURN_COST`: per block and per API call,
negative on balance) is charged after every block, not once at the end of the turn, so the
running total under `--enforce` follows the real meter. Charged at the end, a 93.9k turn
(cambc 88.0k) peaked near 105k mid-turn and was suspended; that was the whole 00ambush
divergence below. Turn totals are unchanged.

tune-1 vs v7zg-cast, 40 maps × 2 sides, `--bot-seeds` against `cambc run-batch`: **80/80 games
end identically** (winner and end round; tie-broken round-2000 draws included), with no
suspensions in either. Before the enemy-spawn dash rule (docs/ENGINE_FINDINGS.md) and the
running total, 75/80. The last one (01big-world, tune-1 as team A) needed the refit with
tune-1 profiles: three turns cambc measured at ~95.7k came out at ~103.5k because
`api:nearest_by_walk` was fitted high on big maps (measured / model median 0.92 on 01big-world,
0.84 for the largest calls; its per-candidate term fell from 2.18 to 1.34 fuel with big-map
samples in the pool). On the same refit, v7zg-cast vs fs-1 (12 maps, all still identical):
total 1.028 (was 1.044), per-turn median +1.6%, 10-90% [−7.8%, +12.7%].

On the ba25401 bot (refit 65ca6e5, then the mask estimate below), tune-2 vs tune-1, 80
`--bot-seeds` games against cambc: **80/80 identical**, including the one game where cambc
itself suspends a turn (01big-world, tune-2 as A, round 1392). 525,805 turns: total 1.011,
per-turn median −0.0%, 10-90% [−11.2%, +12.8%], 1-99% [−23.0%, +24.1%]; turns over 80k:
median 0.997.

`nearest_by_walk`'s choice of the capped origin search depends on what the last reachable
mask cost the bot (it measures it). The simulator estimated it as max(190 + 1.7·tiles,
0.9·chunks·D), which is 3-4x the real cost almost everywhere (median masks are 100-350
fuel), so the simulator took the capped search where the bot did not (an extra ~60 layers on
01big-world). Measured on 33k masks (tune-2 vs tune-1, 10 maps), ReachableMask works layer
by layer on the chunks of the box within k of origin: mask ≈ 97 + 1.54·Σ_{k≤D} chunks(box
of radius k, clipped) + 0.29·tiles (mae 93 fuel; masks over 2k: median 0.995).

**`fuel_remaining()` gates.** Until 756d052 the deploy bot's `fuel_remaining()` returned 2^40
(the simulator's unmetered value; the bot never meters), so any gate on it always passed in
cambc. Now it asks the engine. Policies that gate on it are exact only when the threshold is
far from the values the gate actually sees. tune-3 (`fuel_remaining() > 55000`) vs tune-2:
76/80 identical. Measured on 00ambush (1164 checks, tune-3 as A), the simulator reads the gate
a median 2.75k lower than cambc (p10 −0.1k, p90 +4.2k fuel spent before the check, sim minus
real), while turn totals agree within ~1%: the fit constrains turn totals, not when within
the turn the fuel goes. 117 of the 1164 real reads were within 50-60k. (A probe `printf` in the
bot costs ~3.0k fuel; subtract it when measuring this way.)

**Within-turn timing (gates).** Reads of `fuel_remaining()` were compared directly: tune-3
with its gate set to always pass (same reads, identical games) vs tune-2 on 00ambush,
01big-world, 01starvation and 00collision, both sides; a probe bot prints each turn's first
read (21.5k reads). The simulator read the gate a median 1.8k low (fuel spent before the
check, sim minus real: p10 −2.1k, p90 +3.6k; 3-9% by map), growing with the blocks run so far
(~24 per block) while turn totals agreed: part of what the fit charges per block is paid by
the real bot after the policy runs. `Interp::charge_turn_cost` now holds back 24 per block
run so far and charges it at the end of the turn (totals unchanged). At the gate: median
+0.0k, p10 −3.8k, p90 +1.8k; per map −0.8k to +1.0k (00ambush +1.0k). tune-3 vs tune-2 against
cambc: 76/80 identical (75 before); tune-2 vs tune-1 still 80/80. The rest is per-turn spread
(p10/p90 ±2-4k), which per-block scales do not explain; a gate threshold within a few k of the
values it sees will still flip some decisions.
`FUEL_GATE_DETAIL=1` (fuel_turns, `--enforce`) prints each turn's first `fuel_remaining()` read
(`@@GD`) with the charges so far by block (`@@GDB`) and API call (`@@GDC`).

**Combat (meta draft).** opp-tune5-metadraft (Vesper Vale, Heart of Ruin, Marcella, Vendetta,
Ryth) vs tune-5 (both sides) and vs itself, 40 maps, `--bot-seeds` against `cambc run-batch`
(bot/src at 4f4f9e1): with their `fuel_remaining() > 55000` gates, 110/120 identical (all ten
mismatches on gate-sensitive maps). With the gates set to always pass, **119/120**; the one
left (01big-world, meta as A) is a heavy-turn fuel suspension in the simulator, not combat.
These games fight (e.g. 00contest 46 champion kills, 01elk-arena 30), so champion abilities,
stuns, Heart of Ruin's missing-health bonus and item stats in fights match cambc. Not covered
by these drafts: Prism, Stellar, Willow, Varg, Cassi & Issac in champion fights.

Diagnostics for this kind of check:
- `STATE_TRACE=1` (interp_eval; the bot's main.cpp can set `interp::state_trace` for a cambc
  trace build): per champion turn, `@@ST` (state seen at turn start), `@@SE` (the `end_turn()`
  reached, move target and step, end position, dash target and result), `@@SP` (priority).
  `STATE_TRACE_ROUNDS=a-b` adds `@@SB` counts and order-free hashes of the blocked set, camp
  set and vision; `STATE_TRACE_TILES=r` adds that round's vision as `@@SV` row masks. Printing
  is metered in the bot, so keep the windows short.
- `FUEL_TURN_DETAIL=ROUND:CHAMP` (fuel_turns): that turn's charges by block (`@@DTB`) and API
  call (`@@DTC`, by `cbs::Call`), its total and its correction.

**Outcome check.** With the current table, the simulator gives 0 suspensions per game for v3
and fs-1 against starter (40 maps × 5 seeds). Win rates: v3 196/200 = 98%, fs-1 195/200 =
97.5%, v3 vs fs-1 173/200 = 86.5%. cambc, default fuel, current bot: v3 and fs-1 each won 12/12
against starter-cpp on the maps above.
Earlier tables (old bot, before the host-backed Bitboard) gave v2 ~2,000 suspensions per
game, matching that bot in cambc at the time.
