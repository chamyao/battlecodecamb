# rev: 52d71e88ea305108bdf4ffb1084ec92f3dd9703f
# Arena B (Arena B lead): resume arenaB-4 (stopped) adding the live bot tune-v20-L1c as an anchor (rated for its first
# 200 games, then frozen; style-gconv1 stays an anchor); same runtime (genome/v0 db3f945), fixed anchors, intel on,
# total cap $8. In-arena gate rounds off (gatekeeper-6 gates vs tune-v20-L1c).
while [ ! -f "$OUT/../arenaB-4/rc" ]; do sleep 60; done
echo "arenaB-4 exited rc=$(cat "$OUT/../arenaB-4/rc"); resuming"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaB-4/arena" --tag B --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --fixed-anchors --gate-every 100000000 --intel-branch genome/intel --add-anchors policies/candidates/tune-v20-L1c.policy --gate-ref policies/candidates/tune-v20-L1c.policy
