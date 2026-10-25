#!/bin/bash
# arenaZ-5 (M2 session mutator) setup: a checkout of 7e40b6f with the file-queue patch, genome/search's queuellm.py and
# queuewait.py, and runtime genome/rt-a-fast 648bafd, built. Usage: bash setup_z5.sh <dir> [genome/search sha]
set -e
D=${1:?usage: setup_z5.sh DIR [SHA]}; SHA=${2:-origin/genome/search}
REPO=$(git rev-parse --show-toplevel)
git -C "$REPO" fetch -q origin genome/search genome/rt-a-fast
git -C "$REPO" worktree add -q --detach "$D" 7e40b6f9582dc78a054cc969f81077bf58ea5294
cd "$D"
git -C "$REPO" show "$SHA:genome/search/patches/arenaZ5-queue.patch" | git apply
for f in queuellm.py queuewait.py; do git -C "$REPO" show "$SHA:genome/search/$f" > genome/search/$f; done
git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt
cmake -S genome -B genome/build -DCMAKE_BUILD_TYPE=Release > build.log 2>&1
cmake --build genome/build -j"$(nproc)" --target genome_eval >> build.log 2>&1
cp genome/examples/starter.genome starter-anchor.genome
python3 -c "from genome.search import arena, queuellm, queuewait; print('arenaZ-5 checkout ready:', '$D')"
