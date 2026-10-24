# rev: 681e2e3a90741660b8a8b51e2c0609461f6fddff
# genome/search survival arena A ($8), seed genome/seeds/v23.genome (genome/seed f739709), runtime genome/v0 46f8c7a
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag A --seed genome/seeds/v23.genome --budget 8 --threads $THREADS 
