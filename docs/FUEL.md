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
`buy(x, 0)` calls that bind no variable. Profiled with `EVERY=1`, it exercises all 139 blocks.

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
`real ≈ 0.956·model − 91·blocks − 64·API calls − 70·turns` (3836 rounds). The generated
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

The bot's start-up (map, camp layout, policy load, allocator) costs each champion's first turn
about 55k + 2.3·W·H + 249·camps + 393·groups more (24 cambc games, MAE 2.7k, against the 200k
first-turn budget). It is not in the profile, so it is charged from a hand fit in `interp`.

Current calibration (deploy/v0 after 1253c6b):
- coverage.policy (EVERY=1, 400 rounds) on 00collision, 00elkring, 00lanes, 00monolith,
  01big-world and 01hooks;
- v2 and fs-1 (EVERY=10, 800 rounds) on those maps plus 00gem-fields, 00rows and 01starvation.

Largest items, in profile fuel before the scale (fuel; mean and mean absolute error over the
samples):

| Block / wrapper | Model | Mean | MAE |
| --- | --- | --- | --- |
| `api:distance_field` | 2035 + 9.7·ch + 18.5·miss·ch + 1.00·layers·ch + 163·dests | 4019 | 701 |
| `api:nearest_by_walk` | 1329 + 15.3·ch + 11.6·miss·ch + 1.42·layers·ch + 2.1·tiles | 4096 | 881 |
| `api:visible_camps` | 196 + 168·occupied camp tiles | 732 | 139 |
| `move_towards(Tile)` | −39 + 11.3·ch + 15·refresh·H + 1519·dests | 2151 | 111 |
| `dash_towards(Num,Tile)` | 522 + 1198·refresh + 73·dests | 2099 | 466 |
| `closest(TileSet)` | −122 + 12.5·ch + 1288·refresh | 1875 | 69 |
| `respawning_visible_spawns()` | 501 + 132·groups | 3383 | 189 |
| `camp_spawn_tiles()` | 1964 + 17.5·ch | 2989 | 629 |
| `filter(UnitList,UnitPred)` | 1094 | 1094 | 411 |
| `union`, `minus` (TileSet) | 595-661 + 3-4·ch | 837-855 | 0-56 |
| `ring(TileSet,Num)` | 235 + 6.4·H + 30·input tiles | 732 | 16 |
| `spawn_region`, `altars()`, `walls()` | 133-352 + ch | 192-410 | 0 |
| `api:camp`, `api:champion`, `api:my_champion`, `api:*_occupancy` | 30, 42, 10, 14 + ch | | 0 |
| simple blocks (`and`, `or`, `not`, arithmetic) | 150-400 | | 0-110 |
| step loop, per turn | 21 + 73.4·blocks + 0.062·blocks·H | | 339 |

Board work now goes through host imports (~6 + chunks fuel per board operation), so
board-valued blocks cost hundreds rather than thousands.

**Validation.** `oracle/tools/fuel_validate.py /tmp/prof/*/*` applies the corrected model to
every logged round and compares it with the plain bot's real fuel for that round. This is
in-sample for the correction.

| Runs | Predicted / real total | Per-round error, median | 10-90% |
| --- | --- | --- | --- |
| coverage (6 maps, every round) | 0.927-1.030 | −6.5% to +4.1% | within [−9.3%, +7.7%] |
| fs-1 (9 maps) | 0.966-1.032 | −0.7% to +4.1% | within [−8.8%, +10.8%] |
| v2 (9 maps) | 0.960-1.018 | −2.3% to +2.3% | within [−10.6%, +10.9%] |

Out of sample, the simulator itself (`interp/tools/fuel_turns --enforce`) was compared with
full cambc games at default fuel on 12 maps (00ambush to 00interlock; different games, since
the drafts differ). Champion turns after the first, in fuel per turn, and first turns:

| | mean | p50 | p90 | p99 | max | capped | first turns: mean, max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fs-1, cambc | 14683 | 12840 | 27425 | 40005 | 61223 | 0 | 112421, 156583 |
| fs-1, simulator | 14290 | 12285 | 27928 | 41071 | 61098 | 0 suspensions | 111266, 156361 |
| v2, cambc | 12001 | 10364 | 27013 | 41470 | 78520 | 0 | 114049, 165553 |
| v2, simulator | 11982 | 9960 | 27157 | 41021 | 78233 | 0 suspensions | 114723, 166615 |

Known weak spots:
- Per call, `distance_field` and `nearest_by_walk` carry ~17-21% MAE. A memo hit through the
  walls-changed proof costs more than a same-walls hit, and the profile does not separate
  them. Per round this averages out.
- `or`/`and` are bimodal (short-circuit or not), charged at their mean (MAE ~100).
- The simulator's memo miss rate ran 5-10 points above the bot's in comparable (not
  identical) games. The memo code is shared and the BFS matches the host exactly, so this is
  probably game differences; it is not verified on an identical game.
- The model is for this bot build: re-run `run_bot_profile.sh` (coverage, v2 and fs-1) and
  `fuel_calibrate.py` whenever `bot/` or the interpreter changes (a run takes ~30 minutes
  on 4 cores), then refit the start-up constants in `Interp::turn` from full cambc games.
- The simulator's bot pricing costs speed: 200 games of v2 vs starter take ~6.9 s against
  ~5.4 s with raw prices (the memo runs its own searches on misses).

**Outcome check.** With the current table, the simulator gives 0 suspensions per game for v2
and fs-1 against starter (40 maps × 5 seeds). Win rates: v2 186/200 = 93%, fs-1 195/200 =
97.5%. cambc, default fuel, current bot: v2 and fs-1 each won 12/12 on the maps above.
Earlier tables (old bot, before the host-backed Bitboard) gave v2 ~2,000 suspensions per
game, matching that bot in cambc at the time.
