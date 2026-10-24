#!/bin/bash
# Build a cambc bot folder from a genome: the policy bot's engine-backed Api (bot/src/bot_api.cpp and
# friends), the genome runtime and the genome's generated C++ (compiled with GENOME_BOT: no fuel
# counters, the engine meters real fuel).
# Usage: genome/bot/sync.sh GENOME BOT_DIR   (GENOME_DEFS="GENOME_PROF ...": extra #defines, e.g. profiling)
set -euo pipefail
repo=$(cd "$(dirname "$0")/../.." && pwd)
genome=$(realpath "$1"); dir=$(realpath -m "$2"); src=$dir/src
rm -rf "$src" && mkdir -p "$src/cbs"
for h in "$repo"/sim/include/cbs/*.h; do
	sed -E 's|#include "cbs/([a-z_]+\.h)"|#include "\1"|' "$h" > "$src/cbs/$(basename "$h")"
done
cp "$repo/bot/bitboard_host.h" "$src/cbs/bitboard.h"
cp "$repo"/bot/src/{bot_api.cpp,bot_api.h,coro_stub.cpp,fast_alloc.cpp,fuel_bot_gen.inc} "$src/"
for f in constants_gen fuel coverage; do cp "$repo/sim/src/$f.cpp" "$src/vendor_sim_$f.cpp"; done
{ echo "#define GENOME_BOT // every file of the bot sees the same runtime (one definition rule)"; for d in ${GENOME_DEFS:-}; do echo "#define ${d/=/ }"; done; cat "$repo/genome/runtime/genome_rt.h"; } > "$src/genome_rt.h"
cp "$repo/genome/bot/main.cpp" "$src/main.cpp"
cp "$repo/genome/bot/bot_api_extra.cpp" "$src/"
{ (cd "$repo" && python3 -c "import sys; from genome import lang; print(lang.to_cpp(lang.parse(open(sys.argv[1]).read())))" "$genome"); } > "$src/genes.cpp"
echo "genome bot in $dir ($(realpath --relative-to="$repo" "$genome"))"
