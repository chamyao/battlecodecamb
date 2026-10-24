# rev: 5a961dfc82c499b9416979b896d253562a9502f2
# Ladder gate vs the LIVE bot B318 (ladder v25; genome/candidates/B318.genome) on genome/v0 d0c0704, every 10 min
# from the arenas' pushed state: top 5 by rating with >= 200 games. Every game is fixed by map and side, so each
# opponent is one pass over the 80 distinct games (40 maps x 2 sides) with policies seeded as deployed (--bot-seeds):
# pass at >= 43/80 vs B318 and no drop > 3 points (of 80) vs B318's own rate against each anchor (tune-v20-L1c,
# style-gconv1, v7, tune-v20-L1, rall2-ca4-lean-g, opp-tune5-metadraft); fuel x10 head to head logged. Follows every
# arenaA-N / arenaB-N job. Replaces gatekeeper-7.
echo "B318 sha256 $(sha256sum genome/candidates/B318.genome | cut -c1-16)"
A=policies; C=policies/candidates
python3 -m genome.search.gate --out $OUT --arena "arenaA-*" --arena "arenaB-*" --threads $THREADS --top 5 \
    --ref genome/candidates/B318.genome \
    --anchors $C/tune-v20-L1c.policy,$C/style-gconv1.policy,$A/v7.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$A/opp-tune5-metadraft.policy
