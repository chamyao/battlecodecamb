# rev: 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
# Prompt bench round-1 replicate r1c (Arena A lead): same 8 prompts, Haiku, 80-distinct-game scoring (bot seeds;
# prodigy >= 48/80, check at >= 0.60), parents = the seed + the 4 next-longest-lived arenaA-3 genomes (not in r1b), 8 one-edge links each (link seed 13); round 1 only, no Opus
# variants, no retest; cap $0.60 (Arena A's budget). Runtime genome/simspeed 4b60b58 (= db3f945 results, 2.2x faster).
git fetch -q origin genome/simspeed; git checkout -q 4b60b58 -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
echo "runtime pinned to genome/simspeed 4b60b58 (bit-identical to db3f945)"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.promptbench --out $OUT/bench --parents-from $OUT/../arenaA-3/arena --parents 4 --skip-parents 5 --link-seed 13 --rounds 1 --budget 0.6 --workers $THREADS
