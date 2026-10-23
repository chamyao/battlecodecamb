# Ladder losses: v5d and v5d-fs2 (ladder version 6)

Data: our ranked games created after 18:57 UTC on 23 Oct 2026, 35 finished. v5d (before 19:22)
went **11-4**; v5d-fs2 (`policies/v5d-fs2.policy` on `funsearch/runs`) went **12-8**. Tools:
`analysis/fetch_mine.py`, `analysis/v6_report.py`, `analysis/local_strength.py`; tables in
`analysis/v6_report.md`. Previous rounds: `docs/LADDER_LOSSES.md` (fs-1) and
`docs/LADDER_LOSSES_V3.md` (v3).

## (a) How the losses end, and the v3 failure modes

| | reached 1000 | gems tiebreak | gold tiebreak (0-0) |
|---|---|---|---|
| v5d (W-L) | 8-1 | 3-1 | 0-2 |
| v5d-fs2 (W-L) | 8-3 | 3-5 | 1-0 |

- **Altar-lock freeze: gone.** One game (`01corridors` vs Chocolate icecream, 9 locks) scored
  slowly but kept scoring (566-694).
- **Monolith-at-altar deaths: gone in v5d-fs2** (0). v5d had 6, all in one `01boss_battle`.
- **0-gem games: still there, from new causes.** 4 of 12 losses:
  - `01boss_battle` x2 (v5d, vs Motu Patlu and Mousa): the only altar is behind a monolith,
    as before. 0-0, lost on gold (359-576, 1,956-3,878), 9,287 and 6,014 idle rounds. Not
    fixed yet.
  - `01broken_curve` vs Patient Gem Thieves (fs2), 0-713: **a new freeze**. Three
    champions with 22 gems each stand 2 tiles from altar (20,23) for 1,650-1,860 rounds.
    `closest(minus(safe_altar_ring, ...))` picks the ring tile (19,22), which a living gold
    cluster occupies. All three stand next to it and can't step onto it. The tribute branch
    ends the turn before the camp-attack branch, so they never clear it, while the free ring
    tile (19,23) is never chosen. The altar is safe (no monolith within 5) and reachable.
  - `01the_farm` vs GPT dot, 0-51: one capture, a champion idle 1,613 rounds on the gold
    cluster tile (9,2) beside two elks, without attacking. Not diagnosed further.
  - `00stampede` vs Chocolate icecream, 0-320: 157 captures but **0 gems**. Our captures are
    gold clusters along our edge; the gem camps are in elk groups in the middle, where we
    died 49 times (36 to champions).

## (b) Top 3 loss causes (12 losses)

1. **Losing fights to stun/dive compositions (6 losses).** Odyssey x3 (`00elkring`
   506-1015, `00gemfight` 464-1061, `00packs` 204-1012), Chocolate icecream x2
   (`00ambush` 762-849, `00stampede` 0-320), Mousa `00fragment` (140-1030, 39 deaths to
   champions). We die 21-34 times per game vs their 6-14.
   - Who kills us: vs Odyssey, Ryth 29 and Varg 14 (melee; Ryth's AoE stun plus reset). Vs
     Chocolate icecream, Heart of Ruin 48 (stunning dash, more damage at low health), then
     Marcella 20.
   - Local strength at our 314 champion deaths: outnumbered 39%, even 33%, we had more
     champions 28%. As in v3, most of these deaths are in fights we should not lose. Our
     ranged team (Vesper, Tavi, Marcella, Stellar, Ren) stands still and trades with melee
     divers after being stunned.
2. **Freezes and 0-gem games (4 losses).** See (a): `01boss_battle` x2 (unreachable altar),
   `01broken_curve` (approach tile occupied by a camp), `01the_farm` (idle on a camp tile).
   These are bugs, cheap to fix.
3. **Slow scoring (2 losses).** `00rushbait_v2` vs Mousa, 207-687 with 0 deaths: v5d's median
   bag was 4 gems vs their 29 (v5d-fs2's >= 10 rule addresses this). `01corridors` vs Chocolate
   icecream, 566-694: 30 elk deaths and 9 enemy locks; their median bag was 46.

## (c) Opponents

| opponent | our W-L | their draft | deaths us/them per game | gold us/them | their median bag | locks/game |
|---|---|---|---|---|---|---|
| Chocolate icecream | 2-3 | HoR, Vesper, Marcella, Vendetta, Ryth (the ladder meta) | 34.4 / 14.4 | 8.8k / 9.8k | 70 | 4.8 |
| Odyssey | 2-3 | Cassi, Varg, Ryth (+ Stellar) | 21.4 / 6.0 | 2.9k / 4.5k | 14 | 0 |
| Mousa | 2-3 | Cassi/Prism, Vesper, Marcella, Vendetta | 18.6 / 23.0 | 5.9k / 6.1k | 13 | 0 |
| GPT dot | 4-1 | Stellar, Prism, Ren | 7.8 / 14.4 | | 51 | 0 |
| Patient Gem Thieves | 4-1 | Cassi, Ryth, Tavi, Vendetta | 7.2 / 10.0 | | 15 | 0.2 |
| Motu Patlu | 4-1 | Vendetta, Cassi, Ryth | 25.2 / 11.2 | | 14 | 0 |
| 3 Treasure | 5-0 | Prism, Stellar, Cassi | 9.2 / 35.6 | | 15 | 2.2 |

- **Odyssey** brawls with melee stunners (Ryth's AoE stun, Varg's splash and shield, Cassi's
  stun) and wins those fights 6:21 per game. Reaching 1,000 by ~900 rounds, it doesn't need
  more gold than us; it removes our champions.
- **Chocolate icecream** plays the ladder meta: Heart of Ruin dives (48 of our deaths),
  large bags (median 70), and altar locks (4.8 per game). It keeps scoring through fights
  because it banks big bags rarely.
- We beat the ranged/caster teams (GPT dot, 3 Treasure, Patient Gem Thieves) except for the
  freeze game.

## (d) Suggestions

Tactics:
1. **Fix the approach-tile freeze**: target free ring tiles,
   `minus(safe_altar_ring, camp_spawn_tiles())` (static, slightly conservative), or attack
   the camp occupying the chosen tile. One line, worth 1 loss here.
2. **Unreachable altar** (`01boss_battle`, 2 losses): detect it and either take the monolith
   with 3+ champions (`claim_count`) or farm gold for the tiebreak.
3. **Kite melee divers.** Our five champions are ranged or casters. When a melee enemy is
   adjacent, step away and attack next turn (ranged range 3 vs melee 1) instead of trading
   in place. Group up so a dive meets several of us (`allies_within`).
4. **Fight on local strength with a learnable threshold** (as discussed with Cham): engage
   when ally strength / enemy strength >= theta, retreat below it. Don't hard-code
   avoidance.
5. **Draft**: our fixed VV/Tavi/Marcella/Stellar/Ren loses to stun-dive teams. Test a frontline
   (Heart of Ruin or Ryth) in place of Stellar/Ren in the mirror league.

Blocks:
- `free_tiles(TileSet) -> TileSet`: drop tiles occupied by living camps or units (fixes
  the freeze class: any `closest()` target that is occupied).
- `reachable_altars() -> TileSet` (from v3, still needed for `01boss_battle`).
- `nearest_enemy_melee_adjacent() -> Unit` / `enemy_melee_in_range(Num) -> Num` and
  `kite_from(Unit) -> Void`: step to a tile out of the enemy's melee reach while keeping it
  in our attack range.
- `local_strength(Num) -> Num`: allies' hp × dps within r over enemies', for the theta rule.
- `enemy_stun_ready(Unit) -> Bool`: whether a visible enemy's stun is off cooldown (Ryth,
  HoR, Cassi), if the API exposes enemy cooldowns.
