# genome/search: the search for genomes, and the evolvability check

Design: `docs/GENOME.md` (Identity/crossover, Mutation). Operators in `operators.py`:

- **mutate** (Claude, edge-scoped): picks one edge of `Genome.edges()` (calls, keep links, shared-byte
  links; two edges with probability `--two-edge-prob`, default 0.25). Only the genes on its ends may change;
  Claude may rewrite them, change their parameters, call any gene and create new genes
  (`@gene("new", ...)`). The merge gives new genes fresh IDs (`c<child><a,b..>`) and parents, keeps the
  edited genes' IDs and parents, rejects any change to another gene or an existing keep (checked by
  AST diff), and prunes genes nobody calls. Logged per child: edges, genes changed/added/removed, added
  gene sizes, lines changed.
- **crossover** (no LLM): per gene ID pick either parent's version, then the dependency closure from
  `score`/`update` (calls resolve by ID through the caller's parent); retried until it type-checks and
  differs from both parents. Used when the parents share >= 50% of gene IDs.
- **llm_cross** (Claude): crossover by meaning for unrelated parents (both genomes in full).
- **tune** (no LLM): log-normal rescale of 1-3 numeric literals (indices, `==` operands and zeros skipped).

Prompt (`prompts.py`): game facts (funsearch/catalog.py), `genome/LANGUAGE.md`, the edge's genes in full,
signatures + IDs + descriptions + calls of all other genes, the parent's results. System part cached.
Models: Claude Haiku 5.5, Opus 5.5 every 10th call; hard budget cap (`claude.py`, key from
`FUNSEARCH_API_KEY`).

Scoring (`score.py`): one path for genomes (`genome/build.py` -> `genome:<so>`) and policies (`.pol`)
through `genome/build/genome_eval`; paired seeds (screen seed 0, confirm seed 1: same maps and game seeds
for every program); two-stage confirmation (confirm when the child screens above its parent or within
0.1 of the best; the parent is confirmed on the same games); behavioural twins (child's per-game
outcomes identical to a parent's).

```
python3 -m genome.search.run --run NAME --arm genome --seed genome/examples/starter.genome \
    --opponents builtin:starter --budget 1 --max-programs 100
python3 -m genome.search.run --run NAME --arm policy --seed policies/candidates/style-gconv1.policy ...
python3 -m genome.search.report runs/A runs/B
```

The `policy` arm is the FunSearch baseline on the same harness: funsearch/llm.py's prompt (two parents,
"write an improved version") and funsearch/tune.py constants, same islands, budget, opponents, seeds
and tuning share. Every run with spend is appended to `genome/SPEND.md`.
