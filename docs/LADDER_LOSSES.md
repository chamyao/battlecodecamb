# Why fs-1 ("Master") loses on the ladder

Data: our first 15 ranked games on 23 Oct 2026 (2-13 against SilverBullet, bandit, Qual_ify,
all rated ~1,490-1,500); replays in `data/master-2026-10-23/`. They were replayed through the
official engine (`analysis/`), cross-checked against the platform's own match summaries
(`cambc matches summary`), and diagnosed with `analysis/loss_analysis.py`. fs-1 is
`policies/fs-1.policy` on `interp/v0`.

## Totals (15 games)

| | us | opponents |
|---|---|---|
| deaths | 427 | 196 |
| deaths to camps | 324 | 146 |
| kills | 50 | 103 |
| captures | 575 | 1,212 |
| gold earned | 53k | 95k |
| gems tributed | 5.6k | 13.5k |
| share of champion-rounds spent dead | 25% | 12% |
| rounds idle off spawn (>= 15 rounds on one tile, no action) | 4,909 | 950 |

Bot faults (crashes, fuel) per the platform summaries: none.

## Causes, ranked by games cost

### 1. Champions stand and die to camps: no retreat (primary cause in ~8 of 13 losses)

324 of our 427 deaths were to camps: elks 166, monoliths 106, wolves 40, golems 12. A typical
death (`01starvation`, round 84-91): a 900-HP champion walks to the nearest camp spawn, a
monolith next to our base, and trades 35 damage per turn against 200 back. It recalls at 20%
health, which is less than one monolith hit (200/900 = 22%), and recall takes 5 turns and is
cancelled by damage. **297 of the 324 camp deaths had a recall started in the previous 8
rounds**: the recall rule fires too late and never in a safe spot. The champion respawns and
does it again (57 monolith deaths in that game; 24 in `00lost_world`, where we never captured
anything before losing 0-1,008 at round 385).

Losses where this dominates: 01starvation (57 monolith deaths), 00lost_world (24 monolith),
01gold_rush (18 monolith), 00quadrants (12 golem), 00stampede (36 elk), 01fracture (22 elk),
01corridors (37 camp deaths), 00elkring (16 elk).

Checked in our simulator (400 games each vs fs-1; one standard error ±0.025):

| fs-1 change | win rate vs fs-1 |
|---|---|
| retreat: below 30% health, walk toward spawn while any camp/enemy is in range; recall only when nothing is in range | **0.657** |
| same at 40% | 0.618 |
| same at 50% | 0.522 |
| 40% retreat + don't target monolith/golem spawns | 0.640 |
| + tribute only at >= 10 gems | 0.655 |
| don't target monolith/golem spawns (alone) | 0.525 |

Variants are in `policies/experiments/`. The retreat rule alone is worth ~+15 points in our sim.
Excluding monoliths changes little there, probably because the sim's map sample rarely puts a
monolith next to spawn. On the ladder it cost three games outright.

### 2. Farming efficiency: half the captures, tiny bags (secondary in all losses; primary in 00lanes, 00road_of_riches)

- Opponents captured 2.1x as many camps (1,212 vs 575) and earned 1.8x the gold.
- Our median tribute bag was 5-9 gems, with 78-113 tributes per game in some games
  (`00corners` 113, `01islands` 112, `00lanes` 95). Opponents' bags were 22-58, with 13-60
  tributes. fs-1 walks to an altar whenever it carries any gem. Under the current rules a wolf
  gives 4 gems, so most trips carry one small capture. (My Sprint 1 "tribute after every
  capture" advice came from the old rules, where a capture was 22+ gems.)
- But a bag threshold of 20 *lost* to fs-1 in our sim (0.463), and 10 was neutral when
  combined with the retreat. So trips cost less in our sim than they seem to on the ladder,
  or a bigger bag only pays when champions stop dying. Re-test after the retreat fix.

### 3. Losing fights (primary in 01hooks, 00interlock)

- `01hooks`: 31 deaths to champions, only 2 tributes. Gems collected (297) are mostly lost to
  kills (opponents stole 187).
- `00interlock`: we chased kills (18 kills, Tavi and Stellar 9 each) but captured only 18
  camps against 86, and lost 42-1,005.
- fs-1 attacks any enemy in range regardless of health, numbers or gems carried.

### 4. Map awareness: `01the_farm` (0-0 at round 2,000, lost on gold 256 vs 300)

Neither side tributed; the game went to the lifetime-gold tiebreak. We spent 9 lives on elks and
earned less gold. When no altar is reachable, farm gold safely.

### 5. Looks broken

- **Idle champions**: 84 episodes, 4,909 rounds, of a champion alive off spawn on one tile for
  >= 15 rounds with no action (opponents: 950). Only 179 of those rounds are next to an altar
  and 835 on a camp spawn tile (the "hold on a cleared camp spawn" rule waiting on a
  half-cleared group); 2,212 are elsewhere. Example: `01corridors` rounds 1,383-1,422, two
  champions at (16,16)/(16,17) beside a camp row, not acting, one losing health. Worth
  checking `move_towards` / `closest(goals)` when the goal tile is occupied or respawning
  but out of vision.
- **Same draft every game**: Vesper Vale, then `random_champion` gives Tavi, Marcella,
  Stellar, Ren every time (deterministic). Stellar and Ren are near-absent from the
  ladder's top teams.
- **Item count**: 2-4 distinct items per champion (Power Strength/Health shards only);
  opponents 6-10 (Treasure/Bruiser/Jungle families). Gold spent is half theirs.
- **Recall loop**: the champion re-issues `recall()` under fire every turn and stands still
  (see 1).

### Why our sim didn't show this

Every training opponent (starter, v1, my imitations) shares fs-1's skeleton: same camp
targeting (monoliths included), same tribute rule, same recall rule. Self-play against
policies with the same blind spots can't expose them. Opponents that farm efficiently and
retreat would. Ladder replays like these are a cheaper check than waiting for ranked results.

## Tactics worth trying (concrete rules)

1. **Retreat before recall.** If health < 30% and any camp or enemy is in attack range, move
   toward spawn (or away from the threat); recall only when nothing is in range. (+15 pts in
   sim.)
2. **Don't solo monoliths or golems.** Exclude `monolith_tiles()` and `golem_tiles()` from
   goals unless `claim_count(tile) >= 3`.
3. **Pick camps you can clear.** Early, farm gold clusters and single wolves (opponents'
   most-attacked groups: gold+wolf 14%, elk+gem+gold 11%, gem+wolf 9%). Take multi-elk groups
   only with allies or after ~10 shards. Elk does 60 per hit at range 4.
4. **Bigger bags once deaths are fixed.** Tribute at ~20 gems, or immediately when health
   < 50% or an enemy is visible. Opponents' median bag is 22-58.
5. **Fight only when ahead.** Attack champions when at least as many allies are near and
   health > 50%; if carrying gems, disengage toward an altar.
6. **Spend gold on more families.** Treasure first (gold), then Bruiser/Jungle (Jungle: 30%
   less camp damage, directly against cause 1), as the ladder's top teams do.
7. **Draft the meta deterministically**: Vesper Vale, Heart of Ruin, Marcella, Vendetta,
   Ryth, instead of `random_champion`.

## Missing blocks (proposed signatures)

- `in_danger() -> Bool`: any camp or enemy has this champion in its attack range, using
  camps' ranges (wolf 3, elk/golem 4, monolith 5), not ours. Needed for rule 1; the current
  approximation uses *our* attack range.
- `move_away_from(Tile) -> Void` / `flee() -> Void`: step that maximises distance from
  threats while heading to spawn. `move_towards(spawn)` can walk past a camp.
- `group_hp(Tile) -> Num`, `group_dps(Tile) -> Num`: total HP and damage per turn of the
  camp group whose spawn contains the tile (static types plus live HP when in vision).
  Lets a policy filter goals by "can I clear this": with `my_dps()`, turns to kill vs
  damage taken.
- `my_dps() -> Num`: our expected damage per turn (strength, focus, attack resets).
- `damage_taken_last_turn() -> Num`: cheap danger signal that also covers unseen attackers.
- `allies_within(Num) -> Num`: allied champions within r tiles (for fights and group camps;
  `claim_count` covers claims, not presence).
- `unit_gems(Unit) -> Num`, `unit_health_frac(Unit) -> Num`: pick fights against weak or
  gem-carrying enemies; avoid fights when they outnumber us.
- `turns_idle() -> Num`: rounds since this champion last moved or acted, as a stuck
  fallback (e.g. switch goal when > 10).
- `altar_reachable() -> Bool`: static map fact for the gold-tiebreak switch (01the_farm).
