# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# Arena B (Arena B lead / genome lead): resume arenaB-1 once it has exited, on the current runtime (genome/v0
# db3f945) with FIXED anchor ratings (frozen at arenaB-1's final mu, sigma 1), twin-check outcomes recomputed,
# intel on; --budget is the arena's total cap ($8). Replaces arenaB-2/arenaB-3 (stopped). In-arena gate rounds off.
while [ ! -f "$OUT/../arenaB-1/rc" ]; do sleep 60; done
echo "arenaB-1 exited rc=$(cat "$OUT/../arenaB-1/rc"); resuming"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaB-1/arena" --tag B --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000 --intel-branch genome/intel
