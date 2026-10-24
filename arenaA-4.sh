# rev: df11725ad57541eb2a781dd84a22f3a21fdc20b8
# Arena A (Arena A lead, Cham's decision): resume arenaA-3 after ~150 births on the default prompt (arenaA-3 is
# stopped by arenaA-3.stop), same runtime (genome/v0 db3f945) and fixed anchors, with --mutate-prompt creative.
# --budget 7.83 = $8 minus the $0.17 spent by arenaA-2 (an old-runtime resume that ran 20:21-20:26 and is not
# in this lineage), so Arena A's total stays at $8.
while [ ! -f "$OUT/../arenaA-3/rc" ]; do sleep 60; done
echo "arenaA-3 exited rc=$(cat "$OUT/../arenaA-3/rc"); resuming with the creative mutation prompt"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaA-3/arena" --tag A --seed genome/seeds/v23.genome --budget 7.83 --threads $THREADS --fixed-anchors --gate-every 100000000 --mutate-prompt creative
