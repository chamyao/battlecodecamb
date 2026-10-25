# rev: 051b4954bef9bb57bc6d828321d8fb8356d46511
# arenaA-8c (Arena A lead; Cham confirmed): the API-writer CONTROL for arenaA-8 (session writer via --llm-queue, run by the
# Arena A lead's session, mirrored to arenaa/a8-mirror). Identical code/flags/anchors: genome/search 051b4954 (runtime = genome/v0
# ca5180b), resume arenaA-6's final state (1225 births, $7.80), --refingerprint, anchors exactly as arenaA-6 (no --add-anchors),
# --max-births 1625 (+400). Writer: the default API mix (Haiku 5.5, Opus 5.5 every 10th). --budget 14 = $7.80 + ~2x the ~$2.9
# arenaA-6 spent per 400 births, so --max-births is what stops it. Panel: panelA-8c (local, arena service).
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaA-6/arena" --tag A8C --seed genome/seeds/v23.genome \
    --budget 14 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000 --no-distinct-games --no-bot-seeds \
    --max-births 1625
