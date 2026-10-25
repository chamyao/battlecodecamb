#!/bin/bash
# arenaA-7 (Arena A lead; Cham: performance push): the Z-5 setup (a Claude Code session answers every Claude call through
# the file queue, with M2 feedback) applied to Arena A, resumed from arenaA-6's final population, on genome/search at SHA
# (genome/v0 ca5180b runtime). Builds the checkout, fetches arenaA-6's final state and A61188 (ladder v27).
#   bash setup_a7.sh DIR SHA
set -e
D=${1:?usage: setup_a7.sh DIR SHA}; SHA=${2:?genome/search sha}
REPO=$(git rev-parse --show-toplevel)
git -C "$REPO" fetch -q origin genome/search remote/genome genome/v0
git -C "$REPO" worktree add -q --detach "$D" "$SHA"
cd "$D"
cmake -S genome -B genome/build -DCMAKE_BUILD_TYPE=Release > build.log 2>&1
cmake --build genome/build -j"$(nproc)" --target genome_eval >> build.log 2>&1
mkdir -p a7/src
for f in $(git ls-tree -r --name-only origin/remote/genome arenaA-6/arena/ | grep -v "/matches.jsonl$"); do
  r=a7/src/${f#arenaA-6/arena/}; mkdir -p "$(dirname "$r")"; git show "origin/remote/genome:$f" > "$r"
done
git show 0372259:genome/candidates/A61188.genome > a7/A61188.genome
python3 -c "import json; s=json.load(open('a7/src/state.json')); print('arenaA-6 final:', s['births'], 'births')"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
echo "arenaA-7 checkout ready: $D"
