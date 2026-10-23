# Claude API spend (FunSearch)

Cap: $90 total (of Cham's $100 credits). Pass `--budget <cap - total>` to every run.
Costs as tracked by `funsearch/llm.py` (Haiku 5.5 $0.10/$0.50, Opus 5.5 $4/$20 per MTok;
cache reads counted at 0.1x input, which overstates Opus 5.5's real 0.05x, so the totals here err high).

| Date | Run | Programs | Spend (USD) | Cumulative |
| --- | --- | --- | --- | --- |
| 2026-10-23 | (none yet: no ANTHROPIC_API_KEY in environment) | 0 | 0.00 | 0.00 |
| 2026-10-23 | pilot (seed v1; opp starter, v1; Haiku + Opus every 10th) | 150 | 0.66 | 0.66 |
| 2026-10-23 | long1 (seed fs-1; opp starter, v1, v2, fs-1) — paused at 17 programs on coordinator hold; resumable | 17 | 0.10 | 0.76 |
| 2026-10-23 | long2 (seed fs-1; opp starter, v2, fs-1, ladder_meta, procless; old 3-4x price table) — paused at 13 programs on coordinator request; not to be resumed | 13 | 0.15 | 0.91 |
