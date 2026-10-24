# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# Arena A (Arena A lead): resume arenaA-1 on the current runtime (genome/v0 db3f945: current prices, after(), faster
# sim) with FIXED anchor ratings (frozen at arenaA-1's final mu, sigma 1), twin-check outcomes recomputed on this
# runtime; --budget is the arena's total cap ($8). First a baseline at the new runtime: the seed and arenaA-1's
# final top 3 vs each fixed anchor, 200 games each on fixed seeds -> $OUT/baseline.jsonl. In-arena gate rounds are
# off (the gatekeeper job gates A and B).
while [ ! -f "$OUT/../arenaA-1/rc" ]; do sleep 60; done
echo "arenaA-1 exited rc=$(cat "$OUT/../arenaA-1/rc"); baseline, then resume"
python3 -m genome.search.baseline --out $OUT/baseline.jsonl --state "$OUT/../arenaA-1/arena" --top 3 --games 200 --threads $THREADS --tag arenaA-1-final@db3f945
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaA-1/arena" --tag A --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000
