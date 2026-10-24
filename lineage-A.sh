# rev: f0e6ce0c575a2d10147ba7bef48334a98c78bd53
# lineage-A (Arena A lead; Cham-approved analysis, CPU only, no API) on genome/rt-a-fast 648bafd (= db3f945, 65-cell check):
# (a) the main-line ancestors of A659/A711 plus the crossover second parents on that line, (b) single-gene ablations of
# A659 and A711 (each gene whose body differs from the seed's reverted to the seed's), each vs the 13 panel opponents,
# 80 distinct games (bot seeds) -> $OUT/lineage.jsonl. Genomes from arenaA-3's final state (it holds arenaA-1's too).
cp genome/candidates/B318.genome $OUT/B318.genome
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
C=policies/candidates; P=policies
python3 -m genome.search.lineage --out $OUT/lineage.jsonl --state $OUT/../arenaA-3/arena --threads $THREADS \
    --ancestors A1,A3,A7,A8,A20,A67,A107,A129,A137,A141,A161,A177,A196,A259,A263,A314,A324,A335,A341,A352,A494,A509,A514,A543,A548,A615,A622,A637,A646,A659,A679,A711,A128,A305,A508,A435,A575 \
    --ablate A659,A711 \
    --opponents $C/style-gconv1.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$P/v7.policy,$P/opp-tune5-metadraft.policy,$C/tune-v20-L1c.policy,$OUT/B318.genome \
    --opponents $P/v5.policy,$P/v6.policy,$P/v7-zerogem.policy,$C/tune-v19-L1c.policy,$C/hyb-t5m.policy,$C/tune-r-all-v2.policy
