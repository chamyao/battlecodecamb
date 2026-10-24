# rev: 52d71e88ea305108bdf4ffb1084ec92f3dd9703f
# Ladder gate vs the LIVE bot tune-v20-L1c (v22; v23 was reverted ~16:50 UTC), current runtime (genome/v0 db3f945),
# from the arenas' pushed state every 10 min: top 3 by rating with >= 200 games, 400-game screen, full gate at >= 55%
# (800 vs L1c, 400 per anchor incl. style-gconv1, fuel x10). Follows every arenaA-N / arenaB-N job. Replaces gatekeeper-5.
A=policies; C=policies/candidates
python3 -m genome.search.gate --out $OUT --arena "arenaA-*" --arena "arenaB-*" --threads $THREADS \
    --ref $C/tune-v20-L1c.policy \
    --anchors $C/style-gconv1.policy,$A/v7.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$A/opp-tune5-metadraft.policy
