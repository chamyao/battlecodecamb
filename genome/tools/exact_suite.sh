#!/bin/bash
# exact_suite.sh BASE_REV [OUT] : checks that this checkout's simulator gives bit-identical results to
# BASE_REV's (for speed work: fuel is a rule of the game, so not one charge may change).
# Builds BASE_REV's genome_eval in a temporary worktree, compiles the genomes with each tree's own
# runtime, plays the same suite with both binaries and compares every game: winner, gems, rounds,
# suspensions, draft, kills, deaths, damage, captures, tributes and a hash of both teams' per-turn fuel
# (genome_eval --details --fuel-hash). Exit 0 iff identical.
# Suite: v23 genome vs v23 .pol, .pol vs .pol (style-gconv1 vs v7), genome vs builtin:starter,
# builtin:starter vs .pol, at SEEDS (default "1 2"), plus --bot-seeds runs and starter genome vs v23
# genome; 80 games (40 maps, both sides) each. THREADS (default nproc) threads per run.
set -euo pipefail
cd "$(dirname "$0")/../.."
base=$1; out=$(realpath -m "${2:-/tmp/exact_suite}"); seeds=${SEEDS:-1 2}; T=${THREADS:-$(nproc)}
mkdir -p "$out"
here=$(pwd); wt="$out/base"
[ -d "$wt" ] || git worktree add -q --detach "$wt" "$base"
[ -n "${KEEP:-}" ] || trap 'git worktree remove --force "$wt"' EXIT  # KEEP=1: keep the base build for another run
# a base older than --fuel-hash gets this harness (genome_eval.cpp only drives matches and reports)
grep -q fuel-hash "$wt/genome/tools/genome_eval.cpp" || cp genome/tools/genome_eval.cpp "$wt/genome/tools/genome_eval.cpp"
for d in "$here" "$wt"; do
	cmake -S "$d/genome" -B "$d/genome/build" -DCMAKE_BUILD_TYPE=Release > "$out/build.log" 2>&1
	cmake --build "$d/genome/build" -j --target genome_eval >> "$out/build.log" 2>&1
done
pol() { python3 -c "import sys; from pathlib import Path; from policygen.compile import to_prefix; from policygen.text import parse; print(to_prefix(parse(Path(sys.argv[1]).read_text())))" "$1"; }
pol policies/candidates/style-gconv1.policy > "$out/v23.pol"
pol policies/v7.policy > "$out/v7.pol"
run_tree() { # tree tag
	local d=$1 tag=$2 g gs res="$out/$2.txt"
	g=$(cd "$d" && GENOME_CACHE="$out/so-$tag" python3 -m genome.build "$here/genome/seeds/v23.genome")
	gs=$(cd "$d" && GENOME_CACHE="$out/so-$tag" python3 -m genome.build "$here/genome/examples/starter.genome")
	: > "$res"
	one() { # name args...
		local name=$1; shift
		"$d/genome/build/genome_eval" "$@" --games 80 --threads "$T" --details --fuel-hash maps/*.map26a |
			sed 's/"seconds": [0-9.]*, //' | sed "s/^/$name /" >> "$res"
	}
	for s in $seeds; do
		one "g-pol-s$s" --a "genome:$g" --b "$out/v23.pol" --seed "$s"
		one "pol-pol-s$s" --a "$out/v23.pol" --b "$out/v7.pol" --seed "$s"
		one "g-starter-s$s" --a "genome:$g" --b builtin:starter --seed "$s"
		one "starter-pol-s$s" --a builtin:starter --b "$out/v23.pol" --seed "$s"
	done
	one g-pol-bs --a "genome:$g" --b "$out/v23.pol" --seed 3 --bot-seeds
	one pol-pol-bs --a "$out/v23.pol" --b "$out/v7.pol" --seed 3 --bot-seeds
	one gs-g --a "genome:$gs" --b "genome:$g" --seed 4
	sort -o "$res" "$res"
}
t0=$(date +%s); run_tree "$wt" base; t1=$(date +%s); run_tree "$here" new; t2=$(date +%s)
echo "base $((t1 - t0)) s, new $((t2 - t1)) s, $(grep -c fuel_hash "$out/new.txt") games"
if cmp -s "$out/base.txt" "$out/new.txt"; then echo IDENTICAL; else diff "$out/base.txt" "$out/new.txt" | head -20; echo DIFFERENT; exit 1; fi
