# rev: fb14c783bda3090568092fef92757f19af026464
# genome/search pilot: genome arm on starter.genome ($0.30 cap) to check operators at scale
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.run --run evo-starter-pilot --out $OUT/run --arm genome \
    --seed genome/examples/starter.genome --opponents builtin:starter,genome/examples/farmer.genome \
    --budget 0.3 --max-programs 150 --workers 3 --eval-threads 2
python3 -m genome.search.report $OUT/run --md $OUT/report.md
