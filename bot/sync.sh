#!/bin/bash
# Vendor the simulator/interpreter sources into bot/src (the platform compiles only the
# bot folder, with just the SDK on the include path) and embed a compiled policy.
# Usage: bot/sync.sh [POLICY] [BOT_DIR]   (default policies/v2.policy, bot/ itself)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
policy=$(realpath "${1:-$repo/policies/v2.policy}")
src=$(realpath "${2:-$repo/bot}")/src
rm -rf "$src/cbs" "$src/interp" "$src"/vendor_*.cpp "$src"/*_gen.inc
mkdir -p "$src/cbs" "$src/interp"
for h in "$repo"/sim/include/cbs/*.h; do
	sed -E 's|#include "cbs/([a-z_]+\.h)"|#include "\1"|' "$h" > "$src/cbs/$(basename "$h")"
done
sed -E 's|#include "cbs/([a-z_]+\.h)"|#include "../cbs/\1"|' "$repo/interp/include/interp/policy.h" > "$src/interp/policy.h"
# The bot's Bitboard is host-backed (engine chunked layout, host imports for board-wide work).
cp "$repo/bot/bitboard_host.h" "$src/cbs/bitboard.h"
# Simulator pieces the interpreter links against (no api.cpp/coro.cpp/runner.cpp/bots.cpp/
# game.cpp: bot_api.cpp and coro_stub.cpp replace them; no bitboard.cpp/map.cpp: the bot's
# Bitboard is bot/bitboard_host.h).
for f in constants_gen fuel coverage; do cp "$repo/sim/src/$f.cpp" "$src/vendor_sim_$f.cpp"; done
cp "$repo/interp/src/policy.cpp" "$src/vendor_interp_policy.cpp"
# Generated fuel tables included by those sources (oracle/tools/fuel_calibrate.py).
cp "$repo/sim/src/fuel_bot_gen.inc" "$repo/interp/src/block_costs_gen.inc" "$src/"
# Embedded policy, pre-encoded (no string parsing in the bot).
tmp=$(mktemp)
(cd "$repo" && python3 -m policygen.compile "$policy" "$tmp")
python3 "$repo/bot/encode_policy.py" "$tmp" "$src/policy_data.h" "$(realpath --relative-to="$repo" "$policy")"
rm -f "$tmp"
echo "synced $(ls "$src" | wc -l) entries; policy $(realpath --relative-to="$repo" "$policy")"
