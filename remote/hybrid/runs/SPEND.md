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
| 2026-10-23 | long3 (seed fs-1; 1x prices; old opponent pool) — stopped at 12 programs, replaced by the self-play league | 12 | 0.03 | 0.94 |
| 2026-10-23 | league-g1 (best fs-1; league v2) — paused at 31 programs when v3 arrived | 31 | 0.23 | 1.17 |
| 2026-10-23 | league2-g1 (best v3; league fs-1, v2) — stopped at 14 programs for the full calibration (282d84f) | 14 | 0.10 | 1.27 |
| 2026-10-23 | league3-g1 (best v3; league fs-1, v2) — promoted fs-2 (62.5% vs v3 on 800 fresh games); paused for v5 | 177 | 1.38 | 2.65 |
| 2026-10-23 | hyb-g1 (best v5d-fs2) — 13 programs, cut short by container restarts and the 9a0ac5b re-profile | 13 | 0.03 | 2.68 |
| 2026-10-23 | hyb2-g1 (best v5d-fs2) — 16 programs, replaced when v7 went live | 16 | 0.14 | 2.82 |
| 2026-10-23 | hyb3-g1 (best v7) — 7 programs, replaced when v7-zerogem went live | 7 | 0.01 | 2.83 |
| 2026-10-24 | hyb4-g1 (best v7-zerogem) — 60 programs; boundary promoted challenger tune-1 | 60 | 0.30 | 3.13 |
| 2026-10-24 | hyb4-g2 (best tune-1) — 15 programs; boundary validation of tune-2/tune2-focus/tune-3/tune-4 in progress when the line moved to remote-server | 15 | 0.05 | 3.18 |
| 2026-10-24 | hyb4-g3 (best tune-4) on remote-server after snapshot bca8693: lost with Cham's machine (g3 verdict and later programs), not in programs.jsonl | ? | ~0.35 | |
| 2026-10-24 | hybrid line cap raised $10 -> $30 (project cap $90 -> $200). League --budget 29.47 = 30 - 0.18 (hyb, hyb2, hyb3) - 0.35 (lost above) | | | |
| 2026-10-24 | exploration test xc1/xp1/xp2 (hybrid session container) | 114 | 3.21 | |
| 2026-10-24 | hyb5 started on v19 (explore), --budget 25.0 | | | |
