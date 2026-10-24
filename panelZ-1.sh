# rev: cff0329519d81573f27fef7cfa35a5962f740ea2
# panelZ-1 (Arena A lead): held-out panel for arenaZ-1, CPU only. Milestone 0 = the seed (starter genome); then the top 3
# live genomes every 100 births, each vs 11 opponents never in the arena (fs-1, fs-p2, v4, v7-zerogem, hyb-t5m,
# tune-v20-L1c = v21, v5, v6, v7, fs-p1, fs-p3), 80 distinct games each (bot seeds). Runtime 648bafd, as the arena.
# fs-p1/p2/p3 come from remote/pure. Ends when arenaZ-1 has exited and every reached milestone is played.
git fetch -q origin remote/pure || exit 1
for p in fs-p1 fs-p2 fs-p3; do git show origin/remote/pure:policies/$p.policy > $OUT/$p.policy || exit 1; done
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
while [ ! -f "$OUT/../arenaZ-1/arena/state.json" ]; do sleep 60; done
C=policies/candidates; P=policies
python3 -m genome.search.panelwatch --out $OUT/panel.jsonl --state $OUT/../arenaZ-1/arena --until $OUT/../arenaZ-1/rc \
    --every 100 --top 3 --threads $THREADS \
    --opponents $P/fs-1.policy,$OUT/fs-p2.policy,$P/v4.policy,$P/v7-zerogem.policy,$C/hyb-t5m.policy,$C/tune-v20-L1c.policy \
    --opponents $P/v5.policy,$P/v6.policy,$P/v7.policy,$OUT/fs-p1.policy,$OUT/fs-p3.policy
