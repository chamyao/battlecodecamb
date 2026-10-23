#!/bin/bash
# Vendor the simulator/interpreter sources into bot/src (the platform compiles only the
# bot folder, with just the SDK on the include path) and embed a compiled policy.
# Usage: bot/sync.sh [POLICY]   (default policies/v2.policy)
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
src=$repo/bot/src
policy=${1:-$repo/policies/v2.policy}
rm -rf "$src/cbs" "$src/interp" "$src"/vendor_*.cpp
mkdir -p "$src/cbs" "$src/interp"
for h in "$repo"/sim/include/cbs/*.h; do
	sed -E 's|#include "cbs/([a-z_]+\.h)"|#include "\1"|' "$h" > "$src/cbs/$(basename "$h")"
done
sed -E 's|#include "cbs/([a-z_]+\.h)"|#include "../cbs/\1"|' "$repo/interp/include/interp/policy.h" > "$src/interp/policy.h"
# Simulator pieces the interpreter links against (no api.cpp/coro.cpp/runner.cpp/bots.cpp:
# bot_api.cpp and coro_stub.cpp replace them).
for f in bitboard map game constants_gen fuel coverage; do cp "$repo/sim/src/$f.cpp" "$src/vendor_sim_$f.cpp"; done
cp "$repo/interp/src/policy.cpp" "$src/vendor_interp_policy.cpp"
# Embedded policy, pre-encoded (no string parsing in the bot).
tmp=$(mktemp)
(cd "$repo" && python3 -m policygen.compile "$policy" "$tmp")
python3 "$repo/bot/encode_policy.py" "$tmp" "$src/policy_data.h" "$(realpath --relative-to="$repo" "$policy")"
rm -f "$tmp"
echo "synced $(ls "$src" | wc -l) entries; policy $(realpath --relative-to="$repo" "$policy")"
