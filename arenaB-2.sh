# rev: 681e2e3a90741660b8a8b51e2c0609461f6fddff
# Arena B top-up (Cham, +$5: total $8): resumes arenaB-1 once it has exited (never both at once), same rev and
# settings. --budget is the arena's total cap; spend so far is restored from the copied children.jsonl.
while [ ! -f "$OUT/../arenaB-1/rc" ]; do sleep 60; done
echo "arenaB-1 exited rc=$(cat "$OUT/../arenaB-1/rc"); resuming"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaB-1/arena" --tag B --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --intel-branch genome/intel
