# Genome line: Claude API spend

Budget: $50 approved by Cham (Oct 24 2026), more likely later. Independent of the other lines' caps.

| date | run | programs | cost USD | total USD |
| --- | --- | --- | --- | --- |
| 2026-10-24 | Budget (Cham): Arena A $8, Arena B (ladder-informed) $3, on top of ~$2 spent in tests and EC2 dry runs | — | — | committed ~$13 of $50 |
| 2026-10-24 | Budget raise (Cham): Claude API +$40 (line total $90), EC2 +$10 | — | — | committed ~$13 of $90 API |
| 2026-10-24 | Arena B +$3 (cap $11) and the exploiter test $2 (Cham, via the Arena B lead, ~23:30 UTC) | — | — | |

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

**2026-10-25 (Cham): no more Claude API credit.** Every LLM call now goes through Claude Code sessions: arena runs use
the file-queue backend (`--llm-queue`, genome/search/queuellm.py, model "session", cost 0) answered by session writers.
No new API-backed runs (no FUNSEARCH_API_KEY runs, no promptbench --budget); stopped API runs (Z-17a/b/c, exploit-3)
resume only on the queue backend.
