# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# Ladder gate for both arenas at the current runtime (genome/v0 db3f945 prices), from their pushed state every 10 min:
# top 3 by rating with >= 200 games, 400-game screen vs style-gconv1, full gate at >= 55%. Follows A's and B's job
# chains; stops when the last A and B jobs are done. Replaces gatekeeper-2/3.
python3 -m genome.search.gate --out $OUT --arena "arenaA-1/arena+arenaA-2/arena+arenaA-3/arena" --arena "arenaB-1/arena+arenaB-2/arena+arenaB-3/arena+arenaB-4/arena" --threads $THREADS
