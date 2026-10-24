# genome/

Independent line (Cham, Oct 24 2026): the clean-slate genome representation in `docs/GENOME.md`.
Branch `genome/v0`, cut from `deploy/v0` (simulator, interpreter, live policy). Does not change the
other lines' code paths. Spend: `genome/SPEND.md`.

## Use

```
cmake -S genome -B genome/build -DCMAKE_BUILD_TYPE=Release && cmake --build genome/build -j --target genome_eval
SO=$(python3 -m genome.build genome/examples/starter.genome)     # compile a genome (cached by hash, ~1.3 s)
genome/build/genome_eval --a genome:$SO --b builtin:starter --games 80 --threads 4 maps/*.map26a
```

`genome_eval` is `interp_eval` plus `genome:` sides: same flags, same JSON, and `.pol` policies as opponents.
`GENOME_TRACE=1` prints every action the loop takes (`@@G` lines on stderr).

- `lang.py`: parser, type checker, edges (calls, keeps, shared bytes), C++ codegen. Reference: `LANGUAGE.md`.
- `runtime/genome_rt.h`: primitives, legal options, the fixed loop, the simulator Player.
- `examples/starter.genome`: the starter bot as a genome; 51.25% vs builtin:starter over 80 games (all maps).
