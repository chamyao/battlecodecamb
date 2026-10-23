# bot/: cambc submission running a grammar policy

`bot/sync.sh [POLICY] [BOT_DIR]` vendors the interpreter (and the few simulator sources it
links against) into `BOT_DIR/src` (default `bot/src`) and embeds the policy pre-encoded
(`bot/encode_policy.py`). `bot/src/bot_api.cpp` implements `cbs::Api` over the engine's raw
imports, so `interp/src/policy.cpp` runs unchanged. Upload ZIPs: `dist/deploy-<policy>.zip`
(built with `cambc bundle` from a synced copy; see below). Do not submit without the
coordinator's go-ahead.

## How it stays within fuel (real cambc fuel, all exact)

- `bot/bitboard_host.h` replaces `cbs::Bitboard` in the bot: the engine's chunked layout, with
  board-wide work done by host imports (~6 + chunks fuel) instead of wasm code over a
  1600-byte array (memory.copy/fill cost 1 fuel per byte). `for_each` is row-major like the
  simulator's; `for_each_unordered` is the cheaper host order (chunk-major).
- Distance fields (`field_query` in `bot_api.cpp`) are memoised. A search stopped at layer L
  holds exact distances up to L, so a request with the same roots is answered from cache when
  the walls are identical, or when they changed only where a proof (`box_unaffected`) shows
  that nothing the caller reads can change. Requests are narrowed to the champion's tile when
  it is a dest, because the host's ComputeTo runs until *every* dest is reached.
- `Api::nearest_by_walk` (closest): candidate-rooted field to the champion (memoisable), then
  `ReachableMask(origin, D) & cand`. `Api::visible_camps` (camps_visible): camp occupancy +
  `camp_at`. In the simulator both are the old code with the old prices.
- `fast_alloc.cpp`: size-class operator new/delete. Init: one `map_camp_layout` call, no unused
  `camp_at` fill, default-initialised `Map` (make_shared would zero ~14 KB).

## Checking it

- `bot/tools/run.sh MAP [OPP] [OUT] [cambc args]`: one game + per-turn fuel summary.
- `bot/tools/pool.sh [OPP] [OUT] [JOBS]`: all 40 maps; per map result, mean/p99/max fuel,
  first (2x) turn, crashes, bot errors (`pool_summary.py`).
- `bot/tools/profile.sh MAP [POLICY]`: per-block real fuel (`profile_patch.py`), with
  `@@HEAVY` lines listing the big blocks of every turn above 50k.
- `bot/tools/exactness.sh [POLICY]`: optimised bot vs `BOT_REFERENCE` build (no memo, the
  simulator's algorithms on fresh host searches), unlimited fuel, all maps; results must be
  identical. `#define BOT_VERIFY` at the top of `bot_api.cpp` checks every memoised answer
  against a fresh host search and prints `@@VERIFY` lines.
- `bot/tools/bbtest.sh MAP...`: self-test of the host Bitboard against a plain reference.

## Status (Oct 23 ~17:00 UTC, cambc 3.0.5, all 40 maps, normal fuel)

| policy | vs starter-cpp as A | as B | peak turn (not first), A / B | p99 (max over maps) | mean by map | first (2x) turn |
| --- | --- | --- | --- | --- | --- | --- |
| fs-1 | 37/40 | 40/40 | 61k / 61k | 55k | 7-21k | <= 160k / 200k |
| v2 | 38/40 | 37/40 | 79k / 83k (01big-world dash turns) | 56k | 6-21k | <= 170k / 200k |

fs-1 beats v2 35/40 head to head; both beat starter-rust on 01big-world. No crashes or bot
errors in any run. Optimised and reference builds give identical games on all 40 maps for
both policies (`bot/tools/exactness.sh`).
