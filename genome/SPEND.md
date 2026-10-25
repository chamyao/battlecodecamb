# Genome line: Claude API spend

Budget: $50 approved by Cham (Oct 24 2026), more likely later. Independent of the other lines' caps.

| date | run | programs | cost USD | total USD |
| --- | --- | --- | --- | --- |
| 2026-10-24 | Budget (Cham): Arena A $8, Arena B (ladder-informed) $3, on top of ~$2 spent in tests and EC2 dry runs | — | — | committed ~$13 of $50 |
| 2026-10-24 | Budget raise (Cham): Claude API +$40 (line total $90), EC2 +$10 | — | — | committed ~$13 of $90 API |
| 2026-10-24 | Arena B (arenaB-1 .. arena run 19, ladder-informed; +$5 top-up approved by Cham ~20:03): stopped at cap 22:16 UTC | 1,157 births | 8.02 | Arena B total $8.02 of $8 granted |
| 2026-10-24 | Budget (Cham, ~23:30 UTC): Arena B next run +$3 (B cap $11), exploiter test vs B792 $2 | — | — | +$5 committed |
| 2026-10-25 | Exploiter test exploit-1 (arena run 21, pool B792, bot seeds) | 504 programs | 2.03 | exploiter $2.03 of $2 |
| 2026-10-25 | Arena B runs 24 (01:43-02:21, 3 anchors missing by a resume bug) and 27 (restart 02:23) | 1,419 births by 02:21 | 3.06 | Arena B $11.08 of $11 (cap reached ~02:32 UTC) |

## Ladder uploads (Cham, Oct 24)

Standing approval: upload a genome when it beats the live ladder bot, with no further ask. Bar, all three:
1. Sim vs the live bot: >= 53.5% head to head over 800 fresh games, no drop > 3 points vs any anchor.
2. Real cambc vs the live bot: >= 42/80 over 40 maps x both sides.
3. Real cambc safety: no crashes. (Cham, Oct 24 ~20:00 UTC: the first-turn < 200k and capped-turn limits are
   dropped as requirements; trading turns for compute is a legitimate strategy and the real head-to-head (2) already
   includes its cost. First-turn and capped-turn numbers are still reported with every candidate.)
Uploads go through the intel session's logged-in cambc, on the lead's instruction only. Contact the
project's coordinator only when a candidate clears the bar (both lines upload to the same ladder slot).
