#!/bin/bash
# Unpack every match-group bundle and extract each game to $OUT/<code>/<nn>.json
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(dirname "$HERE")
OUT=${1:?out dir}
mkdir -p "$OUT/raw"
for f in "$REPO"/data/sprint1/replays/*; do
  code=$(basename "$f")
  mkdir -p "$OUT/raw/$code" "$OUT/$code"
  (cd "$OUT/raw/$code" && unzip -o -q "$f")
  for z in "$OUT/raw/$code"/*.zip; do
    n=$(basename "$z" .zip)
    mkdir -p "$OUT/raw/$code/$n"
    unzip -o -q "$z" -d "$OUT/raw/$code/$n"
    echo "$OUT/raw/$code/$n/replay.repl26a $OUT/$code/$n.json"
  done
done | xargs -P 8 -n 2 env CAMBC_WASM="$HERE/engine/v0_0_3.wasm" node "$HERE/extract.js"
