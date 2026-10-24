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
