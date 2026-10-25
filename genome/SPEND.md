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
| 2026-10-24 | Arena B +$3 (cap $11) and the exploiter test $2 (Cham, via the Arena B lead, ~23:30 UTC) | — | — | |
| 2026-10-25 | genome/search exploit-1 (arena run 21: exploiters vs B792, 8 seeds, wins/80; exploiter budget) | 504 | 2.03 | 7.51 |

## Ladder uploads (Cham, Oct 24)

Standing approval: upload a genome when it beats the live ladder bot, with no further ask. Bar, all three:
1. Sim vs the live bot: >= 43/80 head to head over the 80 distinct games (40 maps x 2 sides, --bot-seeds; genome games
   do not depend on the seed, so more games only repeat these), no drop > 3/80 vs any anchor.
2. Real cambc vs the live bot: >= 42/80 over 40 maps x both sides.
3. Real cambc safety: no crashes. (Cham, Oct 24 ~20:00 UTC: the first-turn < 200k and capped-turn limits are
   dropped as requirements; trading turns for compute is a legitimate strategy and the real head-to-head (2) already
   includes its cost. First-turn and capped-turn numbers are still reported with every candidate.)
Uploads go through the intel session's logged-in cambc, on the lead's instruction only. Contact the
project's coordinator only when a candidate clears the bar (both lines upload to the same ladder slot).
Ladder check (Oct 24 22:30 UTC): ranked v24 (v22 ZIP) 67-53, v25 B318 8-12, v26 B792 11-19. Head-to-head wins over
the live bot have not predicted band results; a revert to v24 and a stricter bar are with Cham.
