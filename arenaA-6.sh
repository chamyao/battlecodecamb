# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaA-6 (Arena A lead; their reserve): the CONTROL arm for arenaA-5. Resume arenaA-3's final state (not arenaA-5's) with
# exactly arenaA-3's code and evaluation: 7e40b6f unpatched (old matchmaking: global map pointer, policy anchors seeded per
# game), runtime genome/rt-a-fast 648bafd (= db3f945), same flags as arenaA-3 and arenaA-5, the same +$3.50
# (--budget 7.77 = arenaA-3's $4.27 + 3.50). --tag A6 so new genomes (A6738, ...) and gene IDs never clash with arenaA-5's.
# Panel: job panelA-6.
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaA-3/arena" --tag A6 --seed genome/seeds/v23.genome \
    --budget 7.77 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000
