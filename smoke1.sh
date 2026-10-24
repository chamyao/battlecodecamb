# rev: ff86746cf72a
# smoke test: the starter genome vs builtin:starter, 160 games
SO=$(python3 -m genome.build genome/examples/starter.genome)
genome/build/genome_eval --a genome:$SO --b builtin:starter --games 160 --threads $THREADS maps/*.map26a > $OUT/result.json
