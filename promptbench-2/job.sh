# rev: fe57288757cbe21e7852963cabaeae7b5f6785b4
# Prompt bench round 1 (replaces promptbench-1: every game is fixed by map and side, so child vs parent and anchors
# use the 80 distinct games with bot seeds; prodigy >= 48/80, prodigy check at >= 0.60) (Arena A lead; arenaa/PROMPTBENCH.md), runtime genome/v0 db3f945, Haiku, $0.80 cap (Arena A's
# budget). First the held-out panel: tune-v20-L1c (live bot v22) vs the seed and arenaA-3's current top 3, 80 distinct games (40 maps x 2 sides, bot seeds),
# seed 2000003 -> $OUT/panel.jsonl. Then round 1: 8 prompt variants x 40 (parent, link) cells (seed + arenaA-1's 4
# longest-lived final genomes x 8 one-edge links), child vs parent 200 games, prodigy check vs the 5 anchors, and
# the winner re-tested on 5 fresh parents from the latest Arena A state.
A=$OUT/..
python3 -m genome.search.baseline --out $OUT/panel.jsonl --state $A/arenaA-3/arena --top 3 --threads $THREADS \
    --anchors policies/candidates/tune-v20-L1c.policy --tag panel-L1c@db3f945
RT=$A/arenaA-3/arena; [ -f $A/arenaA-4/arena/state.json ] && RT=$A/arenaA-4/arena
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.promptbench --out $OUT/bench --parents-from $A/arenaA-1/arena --rounds 1 --retest-from $RT \
    --budget 0.8 --workers $THREADS
