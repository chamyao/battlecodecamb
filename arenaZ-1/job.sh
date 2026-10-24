# rev: 7e40b6f
# arenaZ-1 (Arena A lead; Cham-approved, from the Arena A reserve): Arena A trained from zero. Same as arenaA-3 (genome/search
# 7e40b6f: today's prompt/operator mix, Opus every 10th, old matchmaking = 7e40b6f's only mode, population 24, fixed anchors,
# champion anchor every 50 births, in-arena gates off) except the seed and anchors: seed genome/examples/starter.genome;
# the only fixed anchor is a frozen copy of the starter genome (fixed at the arena's initial mu: one anchor sets the scale).
# Runtime genome/rt-a-fast 648bafd. Budget $3. Held-out panel: job panelZ-1.
cp genome/examples/starter.genome $OUT/starter.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 3 --threads $THREADS --fixed-anchors --gate-every 100000000
