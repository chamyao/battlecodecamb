# rev: 681e2e3a90741660b8a8b51e2c0609461f6fddff
# genome/search survival arena B, resumed from arenaB-1 (stopped by the runner pause). --budget is the arena's
# total cap: spend so far is restored from the copied children.jsonl, so the remainder is $3 minus it.
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
PREV="$OUT/../arenaB-1/arena"
if [ ! -f "$PREV/state.json" ]; then
  git fetch -q origin remote/genome && mkdir -p "$OUT/prev" && git archive origin/remote/genome arenaB-1/arena | tar x -C "$OUT/prev"
  PREV="$OUT/prev/arenaB-1/arena"
fi
echo "resuming from $PREV"
python3 -m genome.search.arena --out $OUT/arena --resume-from "$PREV" --tag B --seed genome/seeds/v23.genome --budget 3 --threads $THREADS --intel-branch genome/intel
