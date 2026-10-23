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
interpreter over `bot/src/bot_api.cpp`) pays much more: its own interpreter code and its
API wrappers (board conversions, distance-field fills). The simulator originally charged
interpreted policies a placeholder 10 fuel per block. That was **30-100x too low**: v2
vs starter cost a mean of 0.9-6k fuel per turn in the simulator against 27-92k in cambc.
So the simulator is now calibrated against that bot directly.

**Measurement.** `[POLICY=policies/x.policy] [EVERY=10] oracle/run_bot_profile.sh MAP...`
builds a profiling copy of the bot running POLICY (`bot/profile_patch.py`; `bot/` itself is
untouched) and plays it against starter-cpp with `--fuel 1e8`, so costs are never
truncated. Output goes to `/tmp/prof/<policy>/<map>/`. Every EVERY-th turn, and every draft
turn, it logs the **self** fuel and the work done for each interpreter block and each API
wrapper call. Self fuel excludes child blocks, API calls and the profiler's own cost: a
scope's fixed 43-fuel window is subtracted, and the parent is charged the scope's remaining
38. The work logged is distance-field expansions, destination tiles and occupancy-cache
refreshes. It also logs the turn total.

**Coverage.** `policies/coverage.policy` plays v2 but also evaluates every block that v2 and
fs-1 never reach: draft probes, terrain sets, shop and consumables, team memory and unit
queries. Each probe is a separate `let` or `if` so that short-circuiting cannot skip it.
The interpreter allows only 8 variables per type, so most probes are `if` statements or
`buy(x, 0)` calls that bind no variable. Profiled with `EVERY=1`, it exercises all 131 blocks.

**Model.** `oracle/tools/fuel_calibrate.py /tmp/prof/*/*` pools every profiled run across
policies. It fits each block and wrapper as a non-negative linear model over features the
simulator can compute: map rows H, chunks ch, expansions x chunks, destination tiles, cache
refreshes (x H), camp and group counts, and input-set size. Each call gets only physically
meaningful features. The per-turn step-loop fit is weighted for relative error, and each run
counts equally. Without that, the many expensive coverage turns set its constant and cheap
turns are over-predicted. The script generates:
- `sim/src/fuel_bot_gen.inc`: `PriceTable::bot_wrapper()`, the API as called through
  `bot_api.cpp`. A `cbs::Player` may return it from `prices()`; the policy player does.
- `interp/src/block_costs_gen.inc`: per-block self costs and the per-turn step-loop cost.
  The interpreter charges each block when it finishes, and a Charge guard counts the
  block's own work. `interp::load_program` (the simulator's text loader) **refuses a policy
  that uses a block with no measured row**, so an unmeasured block is never silently
  guessed. If a new block is added, extend coverage.policy and re-profile.
- `docs/fuel_calibration.json`: all fits with sample counts and errors.

Current calibration: coverage.policy (EVERY=1, 400 rounds) on 00collision, 00elkring,
00lanes, 00monolith, 01big-world and 01hooks. v2 and fs-1 (EVERY=10, 800 rounds) on those
maps plus 00gem-fields, 00rows and 01starvation. Largest items (fuel; mean and mean absolute
error over the samples):

| Block / wrapper | Model | Mean | MAE |
| --- | --- | --- | --- |
| `api:distance_field` | 3330 + 79.6·H + 149·ch + 1.04·exp·ch + 50.6·dests | 20775 | 580 |
| `api:*_occupancy` | 111 + 28.6·H + 27.8·ch | 3023 | 117 |
| `api:camp`, `api:champion` | 30, 42 | | 0 |
| `closest(TileSet)` | 360 + 11.8k·refresh + 113·refresh·H + 27.3·dests | 17076 | 292 |
| `move_towards(Tile)` | 563 + 45·H + 1.6k·refresh + 40·refresh·H + 12.4k·dests | 14012 | 450 |
| `dash_towards(Num,Tile)` | 776 + 3.7k·refresh + 21·refresh·H + 356·dests | 8351 | 731 |
| `camps_visible()` | 1028 + 133·camps | 8967 | 634 |
| `respawning_visible_spawns()` | 3794 + 131·groups | 6832 | 177 |
| `camp_spawn_tiles()` | 4886 + 13.6·ch | 5574 | 548 |
| `union`, `minus` (TileSet) | ~4.2-4.3k + 17·H | ~5000 | 61-112 |
| `ring(TileSet,Num)` | 3653 + 24·H + 308·input tiles | 6527 | 146 |
| `spawn_region`, `altars()`, `walls()` | 2168, 1947, 1948 | | ~25 |
| consumables, ward (`place_altar_lock`, `teleport_to`, `place_ward`) | 372, 298, 355 | | 0-1 |
| simple blocks (`and`, `or`, `not`, `alive()`, arithmetic) | 150-390 | | 0-110 |
| step loop, per turn | −19 + 95.6·blocks + 0.039·blocks·H | | 1415 |

Board-valued blocks cost thousands each because a `cbs::Bitboard` is a fixed 1600 bytes,
which costs about 1 fuel per byte to copy in wasm. Simple blocks cost ~150-400
(interpreter dispatch plus a host call).

**Validation.** `oracle/tools/fuel_validate.py /tmp/prof/*/*` applies the model to every
profiled turn's logged features and compares it with the turn's measured fuel (same game
state). Over all 28 runs:

| Runs | Predicted / actual total | Per-turn error, median | 10-90% |
| --- | --- | --- | --- |
| coverage (9 runs) | 0.985-0.994 | −1.4% to +0.8% | within [−5.2%, +2.9%] |
| fs-1 (9 maps) | 0.953-0.997 | −4.5% to +1.0% | within [−5.4%, +18.0%] |
| v2 (9 maps) | 0.952-0.997 | −4.2% to +5.6% | within [−6.3%, +18.0%] |

Known weak spots:
- The +17% tail is v2/fs-1's dead or stunned turns, which cost ~1.5k. `or`/`and` are bimodal:
  ~250 when they short-circuit and ~480 when both sides run. The model charges the mean
  (MAE ~100). Fixing it needs an "evaluated both arguments" feature in the profiler and a
  re-profile.
- 01starvation under-predicts by ~5% in total.
- The model is for this bot build: re-run `run_bot_profile.sh` (coverage, v2 and fs-1) and
  `fuel_calibrate.py` whenever `bot/` or the interpreter changes.

**Consequence and outcome check.** With realistic costs v2 suffers ~2,000 suspensions per
game. On 40 maps with default fuel, the real bot (pre-merge build) had 2,066 turns per game at
the 100k budget. The simulator, with the current table, gives 2,162 suspensions. Win rates
of v2 (team A) vs starter on all 40 maps:

| | Win rate |
| --- | --- |
| cambc, default fuel (deploy bot vs starter-cpp) | 33/40 = 82.5% |
| simulator, fuel enforced (5 seeds), current table | 157/200 = 78.5% |
| simulator, fuel enforced (5 seeds), previous v2-only table | 139/200 = 69.5% |
| simulator, unlimited fuel (3 seeds) | 109/120 = 91% |
| simulator before calibration (both sides, 80 games) | 87.5% |

The remaining 4-point gap is within one standard error.
