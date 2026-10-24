# FunSearch lead -> coordinator: ladder candidates

One entry per candidate: policy path, commit, h2h vs live (fresh seeds), --bot-seeds 80-game result vs live, notes.

## 1. hyb-t5m (hybrid line), sent 2026-10-24 05:02 UTC

- Policy: `policies/candidates/hyb-t5m.policy` on branch `hybrid/candidates` @ 6e5d894.
- What: tune-5 (live v16) + tune-4's scoreless-monolith fallback limited to maps whose only gems are
  monoliths. A graft of two existing changes; no FunSearch code.
- h2h vs tune-5, fresh per-game seeds: 52.3% over 2000 games (about +/-1.1 SE). vs tune-4: 55.0%.
- cambc-exact vs tune-5 (`--bot-seeds`, 40 maps x 2 sides): 0.537 = 43/80 (pre-check bar 42).
- Notes: just above the bar on both counts. It doesn't address the v16 loss causes (bag deaths,
  group value); a rich-group preference on top of it screened 56% vs tune-5 over 400 games and is
  being confirmed over 1600. That would supersede this entry if it holds.

## 2. tune-r-all (tune line), sent 2026-10-24 07:03 UTC

- Policy: `policies/candidates/tune-r-all.policy` on branch `tune/runs` @ 82d7d28 or later.
- What: tune5-campreset + map fixes (monolith fallback only after round 800; tribute before a camp
  group with group_threat >= 240; skip camp groups containing a monolith, 00lost-world) + safe recall
  (no recall with an enemy champion within 8: retreat home first; threshold 0.3).
- League (tools/league.py, 19 policies, 160 games per pair, seed 1; hunters 2a/b/c NOT yet in the pool):
  r-all 1742 [1729-1754] vs tune5-campreset 1693 [1681-1705], beyond the 90% interval.
- Info: bot-seeded 44/80 vs tune5-campreset; 0 sim suspensions, 0 crashes. Fight metrics vs tune5-campreset
  (80 games): vs v7zg-cast deaths 4.59 vs 5.76, mid-recall deaths 1.88 vs 2.54; vs metadraft wins 93 vs 80%.
- Needs: real-cambc safety checks (bot session). Supersedes candidate 1 (hyb-t5m), which only cleared tune-5.
