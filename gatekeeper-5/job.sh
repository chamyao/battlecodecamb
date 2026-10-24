# rev: 0b4a06d041ff8e7dc2b1deb4abd86e511394d588
# Ladder gate for both arenas at the current runtime (genome/v0 db3f945 prices), from their pushed state every 10 min:
# top 3 by rating with >= 200 games, 400-game screen vs style-gconv1, full gate at >= 55%. Follows every arenaA-N /
# arenaB-N job (resumes included); skips genomes earlier gatekeepers gated; stops when all A and B jobs are done.
# Replaces gatekeeper-4.
python3 -m genome.search.gate --out $OUT --arena "arenaA-*" --arena "arenaB-*" --threads $THREADS
