#!/bin/bash
# rereplay_v2.sh BUNDLE.repl26a MAP [MAX]: differential replay of a real engine-2.0.0 (cambc 4.0.0) game through the
# simulator: the recorded actions of both teams are fed to cambsim and the full state is compared at every champion
# turn start (rereplay.py); prints the first divergences. BUNDLE is what `cambc run -o` writes (a zip) or a bare
# replay.repl26a. Sets up, once, in $AN (default /tmp/claude-0/an): analysis/ from origin/analysis/sprint1, intel's
# engine.js port (origin/genome/intel genome/intel/tools/extract_v2) and the v2_0_0 visualiser wasm from the cambc
# 4.0.0 asset cache. Needs node, and sim/build/cambsim*.so (pip install pybind11, then rebuild sim/build).
set -euo pipefail
bundle=$1; map=$2; max=${3:-5}
repo=$(cd "$(dirname "$0")/../.." && pwd); AN=${AN:-/tmp/claude-0/an}
if [ ! -f "$AN/analysis/engine/v2_0_0.wasm" ]; then
	mkdir -p "$AN"
	git -C "$repo" fetch -q origin analysis/sprint1 genome/intel
	git -C "$repo" archive origin/analysis/sprint1 analysis | tar -x -C "$AN"
	git -C "$repo" show origin/genome/intel:genome/intel/tools/extract_v2/engine.js > "$AN/analysis/engine.js"
	cp ~/.cache/cambc/assets/*/visualiser/assets/v2_0_0-*.wasm "$AN/analysis/engine/v2_0_0.wasm"
fi
ls "$repo"/sim/build/cambsim*.so > /dev/null
tmp=$(mktemp -d)
if unzip -l "$bundle" replay.repl26a > /dev/null 2>&1; then unzip -p "$bundle" replay.repl26a > "$tmp/g.repl26a"; else cp "$bundle" "$tmp/g.repl26a"; fi
CAMBC_WASM="$AN/analysis/engine/v2_0_0.wasm" CAMBC_ENGINE_JS="$AN/analysis/engine.js" node "$repo/oracle/replays/dump.js" "$tmp/g.repl26a" "$tmp/g.jsonl"
PYTHONPATH="$repo/sim/build" python3 "$repo/oracle/replays/rereplay.py" "$repo/maps/$map.map26a" "$tmp/g.jsonl" --max "$max"
rm -rf "$tmp"
