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
| 2026-10-23 | style-test (STYLE line smoke test, lockdown directive; 2 programs) | 2 | 0.01 | STYLE 0.01 of $10 |
| 2026-10-23 | style-{a,b,c}-g1 (STYLE islands lockdown/teamfight/monolith, seed v5d) — 7/30/16 programs; dropped for the 9a0ac5b re-profile | 53 | 0.30 | STYLE 0.31 of $10 |
| 2026-10-23 | style5-{a,b,c}-g1 (STYLE islands vs v7zg-cast; seed v7zg-cast) — 40/62/61 programs; ended early for tune-1 + the 340ce89 refit | 163 | 2.78 | STYLE 3.09 of $10 |
| 2026-10-24 | STYLE style5/style6 (Cham's machine; final style6 numbers lost, treated as sunk): style6 recorded $5.48 by 04:15 UTC, b and c exited at their $2.31 caps | — | ~6.9 | STYLE ~10 of $10 (line cap reached) |
| 2026-10-24 | STYLE grant for style7: $2 (lead) + $10 (Cham raised the project cap to $200) = $12. Split h (hunter, fight score) 4.0 / b (combat micro) 3.5 / a 2.25 / c 2.25 | — | 0 | STYLE 0 of $12 |
| 2026-10-24 | style7-{a,b,c}-g1 (old plan on 4f8ce7e, launched on EC2 before the hold; stopped 06:58 UTC, archived) — 8/7/5 programs | 20 | 0.04 | STYLE 0.04 of $12 |
| 2026-10-24 | STYLE style8 re-split (11:30 UTC): island a's unspent $2.21 (spent $0.04, paused) moves to a new island h2 (hunter fallback: seed opp-hunter3, fight weight 0.7, opp-hunter-stack injected); h 3.95 (≈$3.75 spent, g2 stalled), b 3.5, c 2.25 (paused, $0.02 spent) | — | — | STYLE ≈$5.2 of $12 |
| 2026-10-24 | STYLE style8 status 17:05 UTC: h $3.95 (stopped at cap; style-h1 = opp-hunter3), h2 $2.23 (cap, no promotion), b $2.61 (150 boundary no promotion; 14 extra programs after a late stop), gconv $0.72 (style-gconv1 = ladder v23, reverted), gyield $0.75 (stopped: target changed), a $0.04 / c $0.02 (paused); b2 $0.95 and gsub $0.52 allotted, c's $2.23 held | — | ≈10.36 | STYLE ≈10.36 spent + 1.47 allotted of $12 |
| 2026-10-24 | STYLE 17:50 UTC, move to the arena: gsub done on EC2 ($0.47+; #10/#21 41.3% vs live at 800 games on engine 2e1ff7e, not sent); b2 stopped on EC2 at ≈$0.24 (resumes on the arena with the rest of its $0.95); new arena run 5 style8-gsub2 $1.00 from c's held money (lead-approved; --strict-floor, ref funsearch/style 1784c8d = deploy/v0 2e1ff7e merged); c's held money now $1.23 | 26 | ≈11.12 | STYLE ≈11.12 spent (+gsub 0.52, b2 0.24) + 1.71 allotted (b2 0.71, gsub2 1.00) = ≈12.83: ≈$0.83 over the $12 line cap, flagged to the lead |
| 2026-10-24 | STYLE cap raised to $13.50 by the lead (17:46 UTC) to cover gsub2 + b2 (≈$12.83) | — | — | STYLE ≈11.12 spent + 1.71 allotted of $13.50 |
| 2026-10-24 | STYLE recount 17:55 UTC from every style8 programs.jsonl (metrics.cost sums on style/arena-overlay 391f2d4): h-g1 0.611, h-g2 3.340, h2-g1 2.226, b-g1 2.613, b2-g1 0.257, gconv 1.135, gyield 1.220, gsub 0.694, a 0.035, c 0.024 = $12.155 spent (earlier rows under-counted gconv by 0.42, gyield by 0.47, gsub overshot its 0.52 by 0.17). Arena: run 5 gsub2 $1.00, run 6 b2 resumed with $0.69 left → ≈$13.85, ≈$0.35 over the $13.50 cap: flagged to the lead | — | 12.155 | STYLE 12.16 spent + 1.69 allotted of $13.50 |
