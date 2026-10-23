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

**Measurement.** `oracle/run_bot_profile.sh MAP...` builds a profiling copy of the bot
(`bot/profile_patch.py`; `bot/` itself is untouched) and plays it against starter-cpp with
`--fuel 1e8`, so costs are never truncated. Every 10th turn it logs, for each interpreter
block and each API wrapper call, the **self** fuel and the work it did. Self fuel excludes
child blocks, API calls and the profiler's own cost: a scope's fixed 43-fuel window is
subtracted, and the parent is charged the scope's remaining 38. The work logged is
distance-field expansions, destination tiles and occupancy-cache refreshes. It also logs
the turn total.

**Model.** `oracle/tools/fuel_calibrate.py MAP...` fits each block and wrapper as a
non-negative linear model over features the simulator can compute. The features are map
rows H, chunks ch, expansions x chunks, destination tiles, cache refreshes (x H), camp and
group counts, and input-set size. Each call gets only physically meaningful features. The
script generates:
- `sim/src/fuel_bot_gen.inc`: `PriceTable::bot_wrapper()`, the API as called through
  `bot_api.cpp`. A `cbs::Player` may return it from `prices()`; the policy player does.
- `interp/src/block_costs_gen.inc`: per-block self costs and the per-turn step-loop cost.
  The interpreter charges each block when it finishes. A Charge guard counts the block's
  own work, and blocks the calibration never exercised get 200.
- `docs/fuel_calibration.json`: all fits with sample counts and errors.

Calibration on 00elkring, 00lanes, 00monolith, 00collision, 01starvation and 01big-world.
Largest items (fuel; mean and mean absolute error over the samples):

| Block / wrapper | Model | Mean | MAE |
| --- | --- | --- | --- |
| `api:distance_field` | 2582 + 129·H + 126·ch + 1.04·exp·ch + 49.9·dests | 27629 | 816 |
| `api:*_occupancy` | −224 + 46.6·H + 19.8·ch | 4256 | 243 |
| `api:camp`, `api:champion` | 30, 42 | | 0 |
| `closest(TileSet)` | 360 + 12.1k·refresh + 109·refresh·H + 24.6·dests | 18072 | 125 |
| `move_towards(Tile)` | 1512 + 48·H + 4.4k·refresh + 11.3k·dests | 14422 | 294 |
| `dash_towards(Num,Tile)` | 677 + 383·dests | 7084 | 420 |
| `camps_visible()` | 501 + 136·camps | 8889 | 522 |
| `respawning_visible_spawns()` | 3597 + 139·groups | 6634 | 175 |
| `minus(TileSet,TileSet)` | 4180 + 16.3·H | 5133 | 88 |
| `ring(TileSet,Num)` | 3841 + 22·H + 313·input tiles | 7168 | 26 |
| `spawn_region`, `altars()` | 2132, 1960 | | ~30 |
| simple blocks (`or`, `not`, `alive()`, arithmetic) | 150-320 | | 0-80 |
| step loop, per turn | −739 + 73.4·blocks + 1.81·blocks·H | | 1046 |

Board-valued blocks cost thousands each because a `cbs::Bitboard` is a fixed 1600 bytes,
which costs about 1 fuel per byte to copy in wasm. Simple blocks cost ~150-300
(interpreter dispatch plus a host call).

**Validation.** `oracle/tools/fuel_validate.py MAP...` applies the model to every
profiled turn's logged features and compares it with the turn's measured fuel (same game
state):

| Map | Predicted / actual total | Per-turn error, median | 10-90% |
| --- | --- | --- | --- |
| 00elkring | 0.992 | −6.6% | [−14.7%, +2.6%] |
| 00lanes | 0.975 | −4.0% | [−14.7%, +0.9%] |
| 00monolith | 1.023 | +1.1% | [−8.4%, +7.5%] |
| 00collision | 0.999 | −0.8% | [−14.7%, +3.9%] |
| 01starvation | 0.991 | −0.5% | [−1.6%, +12.7%] |
| 01big-world | 1.016 | +18.8% | [−0.1%, +26.7%] |
| 00rows (held out) | 1.031 | +1.9% | [−8.4%, +6.6%] |
| 01hooks (held out) | 0.991 | −5.5% | [−14.7%, +4.3%] |
| 00gem-fields (held out) | 1.016 | +0.7% | [−14.7%, +8.1%] |

Known weak spots:
- 01big-world over-predicts typical turns by ~19%, while its total is right.
- Cheap turns carry ±15% error, mostly from the step-loop term.
- Input-set sizes were only exercised through altar sets (v2 policy).
- The model is for this bot build: re-run `run_bot_profile.sh` and
  `fuel_calibrate.py` whenever `bot/` or the interpreter changes.

**Consequence and outcome check.** With realistic costs v2 suffers ~2,000 suspensions per
game in the simulator, matching cambc: on 40 maps with default fuel, the real bot's turns at
the 100k budget average 2,066 per game against 2,051 simulated suspensions. Win rates of v2
(team A) vs starter on all 40 maps:

| | Win rate |
| --- | --- |
| cambc, default fuel (deploy bot vs starter-cpp) | 33/40 = 82.5% |
| simulator, fuel enforced (5 seeds) | 139/200 = 69.5% |
| simulator, unlimited fuel (3 seeds) | 109/120 = 91% |
| simulator before calibration (both sides, 80 games) | 87.5% |

The remaining ~13-point gap is about 2 standard errors. It is concentrated on 00stampede
(both teams 0 gems, decided by tiebreak) and 00expanse.
- Candidate causes: the simulator's starter port is not starter-cpp; and when a suspension
  lands, the simulator charges a block's cost when the block finishes (after its action),
  while real fuel runs out part-way through.
- Not yet investigated further.
- cambc seeds each match deterministically from the matchup and map (`match.seed` is
  identical across reruns), so repeated cambc runs are not independent samples.

## In the simulator

`PriceTable::measured()` is the default for `cbs::Api` and `MatchOptions`:
`price = base + per_chunk * chunks + per_n_milli * n / 1000`, with the values above.
Geometry through `Api::distance_field`, `Api::shadow_cast` and `Api::reachable` is priced
by its actual work (expansions x chunks, tiles scanned, layers). Unmeasured calls default
to 8. Successful actions were mostly probed on failing paths; their success paths may cost
a few fuel more (RULE?).

A policy's own computation is not visible to the simulator. It must be charged
explicitly (`Api::compute`, or the block prices of the policy interpreter) using guest
costs like those above. The built-in `starter` port charges only its API calls, so in the
simulator it uses far less than the 38-50k per turn the real one spends.

## Replay `.fuel` files

Each team's `team-*.fuel` in a replay bundle is a 13-byte header (`a62leuf\0` plus 5
bytes) followed by little-endian u64s: first the per-instance budgets (draft 10x, then
1x/2x per champion instance), then the fuel each instance used per turn. They give
per-turn totals only, not per-call costs.

## Other engine limits found while probing

- **Bot memory survives death.** A champion's bot instance is not restarted when the
  champion dies and respawns (`oracle/bots/persist`: `main()` runs once and a static
  turn counter keeps counting). It keeps being called every turn while dead (dead
  champions can still shop and read memory).
- **Linear memory cap:** 256 MiB per bot instance (4096 wasm pages; `oracle/bots/memtest`
  grows memory 4 MiB at a time and is refused after 252 MiB).
- **Submission size:** submissions are source ZIPs compiled on the platform. cambc
  rejects a bot whose compressed source exceeds **5 MB** ("compressed source exceeds the
  platform's 5 MB limit"), uncompressed source over 64 MB, or too many source files, and
  stops builds whose log exceeds 16 MiB (strings in the cambc 3.0.5 binary; not exercised).
