# bot/: cambc submission running a grammar policy (work in progress)

`bot/sync.sh [POLICY]` vendors the simulator/interpreter sources into `bot/src` and embeds the
policy pre-encoded (`bot/encode_policy.py`); `bot/src/bot_api.cpp` implements `cbs::Api` over
the engine's raw imports, so `interp/src/policy.cpp` runs unchanged. Run with
`ln -sfn $PWD/bot ~/ws/bots/deploy && cambc run deploy starter-cpp --release ...`.

Status (Oct 23): plays and builds without crashes; init fits in the first turn. Fuel is too
high on large maps: on 01big-world about 40% of turns hit the 100k cap (mean ~60k), on
00elkring mean ~30k with occasional caps. Measured hot spots (per call, 100x100):
`closest` ~94k, `move_towards` ~53k, `minus`/`filter`/`first` on tile sets 7-11k.
Causes: every cbs::Bitboard op touches 1600 bytes (~1 fuel/byte to copy, ~1.7k per OR),
conversions to the host's chunked layout, and host BFS cost ~chunks per layer. Next step
that was being evaluated: back `cbs::Bitboard` in the bot with the host's chunked buffers and
host ops (union/not/intersect cost 6 + chunks; `Union(a,b,a)` aliasing is accepted;
`GetSetBits` returns tiles in row-major order), removing conversions.
Not yet done: full-game runs on all maps, win rate in cambc, `cambc bundle`.
