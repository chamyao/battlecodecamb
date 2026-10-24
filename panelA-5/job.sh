# rev: 08770916c1dfbe9ddd9968b747ba090107b37f55
# panelA-5 (Arena A lead): held-out panel checkpoints for arenaA-5. The top 3 live genomes at every 100 births after the
# resume (800, 900, ...; milestone "0" is panel-A3-db2, not re-run), each vs panel-A3-db2's 13 opponents, 80 distinct games
# (bot seeds), runtime 648bafd. Ends when arenaA-5 has exited and every reached milestone is played.
cp genome/candidates/B318.genome $OUT/B318.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
while [ ! -f "$OUT/../arenaA-5/arena/state.json" ]; do sleep 60; done
C=policies/candidates; P=policies
python3 -m genome.search.panelwatch --out $OUT/panel.jsonl --state $OUT/../arenaA-5/arena --until $OUT/../arenaA-5/rc \
    --every 100 --after-births 737 --top 3 --threads $THREADS \
    --opponents $C/style-gconv1.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$P/v7.policy,$P/opp-tune5-metadraft.policy,$C/tune-v20-L1c.policy,$OUT/B318.genome \
    --opponents $P/v5.policy,$P/v6.policy,$P/v7-zerogem.policy,$C/tune-v19-L1c.policy,$C/hyb-t5m.policy,$C/tune-r-all-v2.policy
