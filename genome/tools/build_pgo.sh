#!/bin/bash
# build_pgo.sh [BUILD_DIR]: genome_eval built with profile-guided optimisation (and LTO) in
# BUILD_DIR (default genome/build-pgo). Same results as genome/build/genome_eval (PGO and LTO change
# no arithmetic: no fast-math, no FMA), ~5-10% faster where .pol sides dominate.
# Trains on genome/seeds/v23.genome and genome/examples/starter.genome vs policies/candidates/style-gconv1.policy,
# policies/v7.policy and builtin:starter on every third map (~1 min).
set -euo pipefail
cd "$(dirname "$0")/../.."
out=$(realpath -m "${1:-genome/build-pgo}")
prof=$out/profile
rm -rf "$prof" && mkdir -p "$prof"
tmp=$(mktemp -d) && trap 'rm -rf "$tmp"' EXIT
for p in style-gconv1:policies/candidates/style-gconv1.policy v7:policies/v7.policy; do
	python3 -c "import sys; from pathlib import Path; from policygen.compile import to_prefix; from policygen.text import parse; print(to_prefix(parse(Path(sys.argv[1]).read_text())))" "${p#*:}" > "$tmp/${p%%:*}.pol"
done
g1=$(python3 -m genome.build genome/seeds/v23.genome)
g2=$(python3 -m genome.build genome/examples/starter.genome)
maps=$(ls maps/*.map26a | awk 'NR % 3 == 1')
cmake -S genome -B "$out" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON \
	-DCMAKE_CXX_FLAGS="-fprofile-generate -fprofile-update=atomic -fprofile-dir=$prof" > /dev/null
cmake --build "$out" -j --target genome_eval > "$out/build.log" 2>&1 || { tail -20 "$out/build.log"; exit 1; }
for pair in "genome:$g1 $tmp/style-gconv1.pol" "$tmp/style-gconv1.pol $tmp/v7.pol" "genome:$g1 genome:$g2" "genome:$g2 builtin:starter"; do
	set -- $pair
	"$out/genome_eval" --a "$1" --b "$2" --games 28 --threads "$(nproc)" --max-rounds 1000 $maps > /dev/null
done
cmake -S genome -B "$out" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON \
	-DCMAKE_CXX_FLAGS="-fprofile-use -fprofile-partial-training -fprofile-dir=$prof -Wno-missing-profile" > /dev/null
cmake --build "$out" -j --target genome_eval > "$out/build.log" 2>&1 || { tail -20 "$out/build.log"; exit 1; }
echo "$out/genome_eval"
