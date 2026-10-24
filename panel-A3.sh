# rev: 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
# Held-out panel baseline (Arena A lead), CPU only: all 24 live genomes of arenaA-3's final state + the seed vs the 5 fixed
# anchors, tune-v20-L1c, B318 (v25, genome) and 6 policies used as anchors in neither arena (v5, v6, v7-zerogem,
# tune-v19-L1c, hyb-t5m, tune-r-all-v2); 80 distinct games each (40 maps x 2 sides, bot seeds). Runtime genome/simspeed
# 4b60b58 (= db3f945). B318.genome is copied from this rev first (the runtime pin only replaces runtime files).
cp genome/candidates/B318.genome $OUT/B318.genome
git fetch -q origin genome/simspeed; git checkout -q 4b60b58 -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
echo "runtime pinned to genome/simspeed 4b60b58 (bit-identical to db3f945)"
C=policies/candidates; P=policies
python3 -m genome.search.baseline --out $OUT/panel.jsonl --state $OUT/../arenaA-3/arena --all --threads $THREADS --tag panel-A3@4b60b58 \
    --anchors $C/style-gconv1.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$P/v7.policy,$P/opp-tune5-metadraft.policy,$C/tune-v20-L1c.policy,$OUT/B318.genome,$P/v5.policy,$P/v6.policy,$P/v7-zerogem.policy,$C/tune-v19-L1c.policy,$C/hyb-t5m.policy,$C/tune-r-all-v2.policy
