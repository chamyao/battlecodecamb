# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-8 (Arena A lead): arenaZ-1 exactly, except EVERY Claude call uses Opus (mutations and crossovers by meaning; no Haiku):
# 7e40b6f's own --opus-every 1 (call n is Opus when n % 1 == 0), no patch. Same RNG stream as arenaZ-1 (no salt). --budget 20 so it
# reaches ~475 births (Arena A reserve; Cham: API credits are not the constraint). 7e40b6f, runtime 648bafd, starter seed and only fixed anchor, champions every 50.
cp genome/examples/starter.genome $OUT/starter.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 20 --opus-every 1 --threads $THREADS --fixed-anchors --gate-every 100000000
