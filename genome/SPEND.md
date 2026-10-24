# Genome line: Claude API spend

Budget: $50 approved by Cham (Oct 24 2026), more likely later. Independent of the other lines' caps.

| date | run | programs | cost USD | total USD |
| --- | --- | --- | --- | --- |
| 2026-10-24 | Budget (Cham): Arena A $8, Arena B (ladder-informed) $3, on top of ~$2 spent in tests and EC2 dry runs | — | — | committed ~$13 of $50 |
| 2026-10-24 | Budget raise (Cham): Claude API +$40 (line total $90), EC2 +$10 | — | — | committed ~$13 of $90 API |
| 2026-10-24 | genome/search g-live1 | 10 | 0.06 | 0.06 |
| 2026-10-24 | genome/search p-live1 | 7 | 0.02 | 0.08 |
| 2026-10-24 | genome/search g-seed-smoke | 8 | 0.01 | 0.09 |
| 2026-10-24 | genome/search s-smoke (strength loop test, starter.genome) | 24 | 0.01 | 0.10 |
| 2026-10-24 | genome/search EC2 evo-policy-1 (arm a, dropped) | 124 | 1.58 | 1.68 |
| 2026-10-24 | genome/search EC2 evo-starter-pilot | 125 | 0.31 | 1.99 |
| 2026-10-24 | genome/search arena-smoke (arena loop test, starter.genome) | 40 | 0.04 | 2.03 |
| 2026-10-24 | genome/search arena-g (gate round test, starter.genome) | 20 | 0.01 | 2.04 |
| 2026-10-24 | Arena B top-up (Cham): +$5, Arena B total $8 (arenaB-2 resumes arenaB-1) | — | — | committed ~$18 of $90 API |
| 2026-10-24 | genome/search pb-test (prompt bench test, starter.genome, 2 rounds) | 72 | 0.11 | 2.15 |
| 2026-10-24 | Arena B final: arena run 19 (arena-arenaB-11) stopped at the cap, $8.02 of Arena B's $8 in total (1157 births) | 1157 | (Arena B budget) | — |
| 2026-10-24 | genome/search promptexp-1 (Arena A prompt experiment 1, Haiku, A0 vs A1, 120 cells; Arena A budget, cap $0.40) | 240 | 0.26 | 2.41 |
| 2026-10-24 | genome/search EC2 arenaZ-1 (Arena A from the starter genome; Arena A reserve) | 475 | 3.07 | 5.48 |

## Ladder uploads (Cham, Oct 24)

Standing approval: upload a genome when it beats the live ladder bot, with no further ask. Bar, all three:
1. Sim vs the live bot: >= 53.5% head to head over 800 fresh games, no drop > 3 points vs any anchor.
2. Real cambc vs the live bot: >= 42/80 over 40 maps x both sides.
3. Real cambc safety: no crashes. (Cham, Oct 24 ~20:00 UTC: the first-turn < 200k and capped-turn limits are
   dropped as requirements; trading turns for compute is a legitimate strategy and the real head-to-head (2) already
   includes its cost. First-turn and capped-turn numbers are still reported with every candidate.)
Uploads go through the intel session's logged-in cambc, on the lead's instruction only. Contact the
project's coordinator only when a candidate clears the bar (both lines upload to the same ladder slot).
