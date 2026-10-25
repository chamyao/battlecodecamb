# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-8x (Arena A lead): resume arenaZ-8's final state (155 births, $6.09; it ran at --budget 6 because its start fetched the
# job before the --budget 20 edit) with the same code and flags, every Claude call on Opus (--opus-every 1), --budget 20 (the
# arena's total), so it reaches ~475 births. 7e40b6f, runtime 648bafd, no patch. Panel continues panelZ-8's milestones.
# resume rebases the starter anchor (absolute path in arenaZ-8's out/) to <checkout>/starter.genome: put it there
cp genome/examples/starter.genome starter.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaZ-8/arena" --tag Z --seed genome/examples/starter.genome \
    --budget 20 --opus-every 1 --threads $THREADS --fixed-anchors --gate-every 100000000
