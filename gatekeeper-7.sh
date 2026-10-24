# rev: bfbdabdcec7c8500a4d33da1e8e52dc9a67429bd
# Ladder gate vs the LIVE bot B318 (ladder v25 since 20:40 UTC; genome/candidates/B318.genome on genome/v0, sha256
# 00e1711a5b5778c9...), at arenaB-5's runtime (genome/v0 db3f945), from the arenas' pushed state every 10 min: top 3
# by rating with >= 200 games, 400-game screen, full gate at >= 55% (800 vs B318; 400 per anchor: tune-v20-L1c,
# style-gconv1, v7, tune-v20-L1, rall2-ca4-lean-g, opp-tune5-metadraft; fuel x10). Follows every arenaA-N / arenaB-N
# job. Replaces gatekeeper-6.
git fetch -q origin genome/v0 && git show origin/genome/v0:genome/candidates/B318.genome > $OUT/B318.genome || exit 1
echo "B318 sha256 $(sha256sum $OUT/B318.genome | cut -c1-16)"
A=policies; C=policies/candidates
python3 -m genome.search.gate --out $OUT --arena "arenaA-*" --arena "arenaB-*" --threads $THREADS --ref $OUT/B318.genome \
    --anchors $C/tune-v20-L1c.policy,$C/style-gconv1.policy,$A/v7.policy,$C/tune-v20-L1.policy,$C/rall2-ca4-lean-g.policy,$A/opp-tune5-metadraft.policy
