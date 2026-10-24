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

## 3. tune-r-all-v2 (tune line), sent 2026-10-24 07:19 UTC

- Policy: `policies/candidates/tune-r-all-v2.policy` on branch `tune/runs` @ 3f16905.
- What: tune-r-all (candidate 2) with its fuel fixes: the monolith-group exclusion set is now a `keep`
  (computed once per game), and the T240 threat-bank branch is gated on fuel_remaining() > 65000.
- League (tools/league.py, 19 policies, 160 games per pair, seed 1). Pool: live tune5-campreset (as
  r-campreset, play-identical); hunters opp-hunter2a/2b/2c + opp-hunter; ladder stand-ins opp-icecream,
  opp-odyssey, opp-metab, opp-metadraft; v7zg-cast, v7-zerogem, tune-3, tune-5, tune5-reset; tune variants.
  r-all-v2 1725 [1712-1737] vs tune5-campreset 1672 [1659-1683], beyond the 90% interval. v2 vs r-all 50%.
- Sim fuel (fuel_turns --enforce --bot-seeds vs campreset; starvation, big-world, lost-world; 24 games):
  0 turns >= 100k, 24 turns > 80k (campreset 100), max non-first turn 87.1k, first turn up to 167k.
- Needs: real-cambc safety checks. Supersedes candidate 2 (failed fuel). If starvation still caps in real
  cambc, the tune line will raise the gate or drop T240.

## 4. rall2-ca4 (hybrid line), sent 2026-10-24 07:52 UTC

- Policy: `policies/candidates/rall2-ca4.policy` on branch `hybrid/candidates` @ 7933e00.
- What: live v18 (tune-r-all-v2) + cast-ahead: before the in-range fight, cast damage/stun (not
  dash/shield/heal/reset) at the nearest enemy champion within 4 tiles; no move, turn continues, sets
  team_target. Uses no slot_*/unit_* blocks.
- League (tools/league.py, 160 games per pair, all maps x both sides). Pool: tune5-campreset (v17),
  tune-r-all-v2 (v18, bar), tune-5, opp-hunter2a/2b/2c, opp-icecream, opp-odyssey, opp-metab, opp-metadraft,
  cr-m, cr-m-ca4, hyb-t5m-r-camp. rall2-ca4 1711 [1696-1723] vs v18 1659 [1645-1673]: beyond the 90% interval.
  Worst matchup cr-m-ca4 55%; vs v18 57%.
- Sim safety (80-game --bot-seeds set vs v18): 50/80; 0 capped turns, 0 crashes; fuel 23.0k vs 21.0k per
  champion-turn (+10%); near-cap turns at a 70% cap 4.4 vs 3.6 per game. First-turn fuel not measurable in sim.
- Fights: vs v18 K 8.4/6.8, D 11.1/12.8; vs hunter2b 78.7%; vs metadraft 85.6%.
- Needs: bot session's safety checks (first turn < 200k, BOT_VERIFY).

## 4b. rall2-ca4-lean (hybrid line), sent 2026-10-24 08:08 UTC: replaces 4 (held on one 100k turn)

- Policy: `policies/candidates/rall2-ca4-lean.policy` on `hybrid/candidates` @ a33869c.
- Change vs 4: one shared `let foes = enemies_visible()` per turn; nearest(foes) only when an enemy is visible.
  A fuel_remaining() gate can't help (the block runs early in the turn, when fuel is near full).
- Sim fuel (deploy/v0 49cc030 fuel_turns --enforce --bot-seeds vs v18, 80 games): mean 23.6k (v18 22.8k, 4 was
  24.9k); turns >80k 15 (v18 9, 4 was 20); 0 suspended; peak 95.8k on 00ambush/a (v18 peak 89.9k); first turn 166.6k.
- League (same required pool): lean 1711 [1694-1725] vs v18 1661 [1648-1673].
- Risk: the 95.8k sim peak is close to the cap. If real cambc caps, hybrid's next lever is sharing closest(goals).

## 4c. rall2-ca4-lean2-d65 (hybrid line), sent 2026-10-24 08:20 UTC: replaces 4b (one real 100k turn)

- Policy: `policies/candidates/rall2-ca4-lean2-d65.policy` on `hybrid/candidates` @ 9c0c7e8.
- Change vs 4b: v18's camp-goal dash gated at fuel_remaining() > 65000 (was 55000). Lean's worst turn was v18's own
  far-camp trip (closest(goals) ~20k + dash + move distance fields ~17k each); cast-ahead cost ~0 there.
- Sim fuel (fuel_turns --enforce --bot-seeds vs v18, all 80 games, first turns excluded): peak 89.3k
  (v18 89.9k; target <= 90k met), 9 turns >80k (v18 9), mean 23.6k, 0 suspended, first turn max 158.5k.
- League (required pool + variants, 160 games per pair): d65 1682 [1668-1696] vs v18 1636 [1623-1650], beyond the
  90% interval. (d70 loses the gain: 1641.)
