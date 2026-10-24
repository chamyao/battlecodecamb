# rev: 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
# panel-A3-db2 (Arena A lead): panel-A3 re-run on genome/rt-a-fast 648bafd (= db3f945 + simspeed; matched db3f945 on all 65
# cells of the 5-genome control; replaces panel-A3-db). All 24 live arenaA-3 genomes + the seed vs the 5 fixed anchors, tune-v20-L1c, B318 and 6 held-out
# opponents (v5, v6, v7-zerogem, tune-v19-L1c, hyb-t5m, tune-r-all-v2); 80 distinct games each (bot seeds). Runtime
# 648bafd. B318.genome is copied from this rev first (the runtime pin only replaces runtime files).
cp genome/candidates/B318.genome $OUT/B318.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
echo "runtime pinned to genome/rt-a-fast 648bafd (= db3f945 results, checked on 65 cells)"
C=policies/candidates; P=policies
python3 -m genome.search.baseline --out $OUT/panel.jsonl --state $OUT/../arenaA-3/arena --all --threads $THREADS --tag panel-A3-db@648bafd \
    --anchors $C/style-gconv1.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$P/v7.policy,$P/opp-tune5-metadraft.policy,$C/tune-v20-L1c.policy,$OUT/B318.genome,$P/v5.policy,$P/v6.policy,$P/v7-zerogem.policy,$C/tune-v19-L1c.policy,$C/hyb-t5m.policy,$C/tune-r-all-v2.policy
