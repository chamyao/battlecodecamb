# rev: fb14c783bda3090568092fef92757f19af026464
# genome/search evolvability check, arm (a): FunSearch proposer on style-gconv1.policy ($1.50 cap)
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.run --run evo-policy --out $OUT/run --arm policy \
    --seed policies/candidates/style-gconv1.policy \
    --opponents policies/v7.policy,policies/candidates/tune-v20-L1.policy,policies/candidates/rall2-ca4-lean-g.policy \
    --budget 1.5 --max-programs 400 --workers 3 --eval-threads 2
python3 -m genome.search.report $OUT/run --md $OUT/report.md
