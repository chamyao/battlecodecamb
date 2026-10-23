# FunSearch

Searches for better policies: sample parents from a program database, ask Claude
for an improved version, score it in the simulator, store it.

```
cmake -S interp -B interp/build && cmake --build interp/build -j --target interp_eval
python3 -m funsearch.run --run pilot --budget 2 --max-programs 200      # needs FUNSEARCH_ANTHROPIC_KEY (or ANTHROPIC_API_KEY)
python3 -m funsearch.run --run test --proposer mutate --max-programs 40  # no API calls
```

- `funsearch/evaluate.py`: compile + play a policy (`interp_eval`), score =
  win rate + 0.25 x gem margin/1000, averaged over opponents.
- `funsearch/database.py`: islands; parents sampled by softmax on score (worst
  first in the prompt); the weaker half of islands is re-seeded every 200 programs.
- `funsearch/llm.py`: prompt = game summary + grammar + block catalog (cached
  system prompt) + parent versions. Model mix: Claude Haiku 5.5, every 10th call
  Claude Opus 5.5 (with server-side refusal fallback). **Hard budget cap**: no
  new call once `--budget` USD is spent (cost from response usage).
- `funsearch/tune.py`: constant mutation ((1+1)-ES); also the LLM-free proposer.
- Output: `runs/<name>/programs.jsonl` (append-only, resumable), `best.policy`.

## Noise

16-game scores are too noisy to rank by: a constant tweak scored 0.70 on 16 games
and 0.48 on 400 fresh ones (starter: 0.50). So every candidate that screens
within `--confirm-margin` of the best is re-scored on `--confirm-games` (160)
fresh games, and that confirmed score is what is stored and compared.
