#!/bin/bash
# arenaB-14 (Arena B lead): Arena B's next run with a Claude Code session as the writer (file queue, M2 feedback incl. per-anchor
# results), on genome/search at SHA (genome/v0 ca5180b runtime). Builds the checkout and fetches:
#   b14/src            arena-arenaB-13's final state (service run 27, remote/genome)
#   arena_policies/    the genome anchors the state points to (hunter, hunter-carry, farmer, deathball, rushbank, B318,
#                      exploit-353/357), where resume rebases them
#   b14/A61188.genome, b14/a61188-mono.genome  ladder v27 and v28 (live since 03:43Z): new anchors, weight 2
#   b14/seeds/         arenaA-6's top 5 by rating (ingested once each as newborns)
#   bash setup_b14.sh DIR SHA
set -e
D=${1:?usage: setup_b14.sh DIR SHA}; SHA=${2:?genome/search sha}
REPO=$(git rev-parse --show-toplevel)
git -C "$REPO" fetch -q origin genome/search remote/genome genome/intel genome/v0
git -C "$REPO" worktree add -q --detach "$D" "$SHA"
cd "$D"
cmake -S genome -B genome/build -DCMAKE_BUILD_TYPE=Release > build.log 2>&1
cmake --build genome/build -j"$(nproc)" --target genome_eval >> build.log 2>&1
mkdir -p b14/src b14/seeds arena_policies
for f in $(git ls-tree -r --name-only origin/remote/genome arena-arenaB-13/ | grep -v "/matches.jsonl$"); do
  r=b14/src/${f#arena-arenaB-13/}; mkdir -p "$(dirname "$r")"; git show "origin/remote/genome:$f" > "$r"
done
for n in hunter hunter-carry farmer deathball rushbank; do
  git show "origin/genome/intel:genome/intel/stress/$n.genome" > "arena_policies/$n.genome"
done
git show f2304110:genome/candidates/B318.genome > arena_policies/B318.genome
cp genome/search/anchors/exploit-353.genome genome/search/anchors/exploit-357.genome arena_policies/
git show 0372259:genome/candidates/A61188.genome > b14/A61188.genome
git show 568cbf5:genome/candidates/a61188-mono.genome > b14/a61188-mono.genome
for g in A61200 A61203 A61180 A61206 A61191; do
  git show "origin/remote/genome:arenaA-6/arena/genomes/$g.genome" > "b14/seeds/$g.genome"
done
python3 -c "import json; s=json.load(open('b14/src/state.json')); print('arena-arenaB-13 final:', s['births'], 'births')"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
echo "arenaB-14 checkout ready: $D"
