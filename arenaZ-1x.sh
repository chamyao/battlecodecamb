# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-1x (Arena A lead; Cham-approved): resume arenaZ-1's final state (475 births, $3.07) with exactly arenaZ-1's code,
# runtime and flags (7e40b6f, 648bafd, no patch) and run long: --budget 15 (the arena's total, so ~$11.9 more, ~2,000+ births).
# Panel (arena service) continues panelZ-1's milestones from birth 500.
# resume rebases the starter anchor (absolute path in arenaZ-1's out/) to <checkout>/starter.genome: put it there
cp genome/examples/starter.genome starter.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaZ-1/arena" --tag Z --seed genome/examples/starter.genome \
    --budget 15 --threads $THREADS --fixed-anchors --gate-every 100000000
