# rev: b08d91b9dd772098b5ccdefc4e2aa3619c6c3d19
# Ladder gate for the running arenas (arenaA-1, arenaB-1), from their pushed state every 10 min: top 3 by rating
# with >= 200 games, 400-game screen vs style-gconv1, full gate at >= 55%. Runs at the arenas' runtime (genome/v0
# 46f8c7a prices) for consistency with their ratings; candidates are re-checked at current prices before upload.
git checkout -q 46f8c7a0f75c -- genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -m genome.search.gate --out $OUT --arena arenaA-1/arena --arena arenaB-1/arena --threads $THREADS
