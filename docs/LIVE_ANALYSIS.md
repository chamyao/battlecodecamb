# Live analysis of our ranked games (v21, v22/v24; 12:40-17:40 UTC, 24 Oct)

## Data

- **Source:** the live stream (`analysis/live.py`), which pulls every finished game as it lands and tags our version from the deploy times.
- **Games:** 135 ranked games of v21, v22 and v24, against opponents near our rating (1550-1650). Our record is 68-67.
- **Tools:** `analysis/gaps.py`, `analysis/race_analysis.py`, `analysis/live_report.py`.
- **Uncertainty:** ± is one bootstrap SE over games.

## 1. Against peers, we lose on economy, not fights

v22 and v24 ranked (60 games, 33-27):

| per game | our wins | our losses |
|---|---|---|
| gems captured, us / them | 1169 / 624 | **751 / 1029** |
| gems per capture, us / them | 14.8 / 14.6 | **11.5 / 17.1** |
| tributes, us / them | 28.6 / 16.1 | **17.7 / 34.6** |
| our deaths to champions | 7.5 | 8.1 |
| low-HP crossings that end in death | 32% | 44% |

Deaths to champions are almost the same in wins and losses. What decides the games is how much we capture, and how fast the opponent banks.

## 2. Slow start

Gems tributed by a given round, all 135 ranked games:

| | by r250 | by r500 | by r750 | first tribute (median round) |
|---|---|---|---|---|
| us in our wins | 58 | 184 | 351 | 187 |
| us in our losses | 50 | 147 | 226 | 190 |
| them in our wins | 49 | 136 | 236 | 130 |
| them in our losses | **81** | **241** | **422** | **104** |

- Our first bank comes at round ~190 whatever the result.
- Opponents who beat us bank at round ~104 and are 30-100 gems ahead from round 250 on.
- On the maps we lose most, their first tribute comes at round 40-70 (00lost_world, 00expanse, 00quadrants).

## 3. Maps we lose, and why

| map | W-L | what happens |
|---|---|---|
| **00great_wall** | 1-4 | **The monoliths kill us.** Our deaths are 18-26 per game, and **13-20 of them are to a monolith** (camp type 4). The opponents die 0-8 times in total. All 4 altars are within 3 tiles of a monolith. |
| **01shortcut** | 0-3 | **We can't bank.** Both altars are next to a monolith (distance 1). Our altar choice excludes altars within 5 of a monolith, so our carriers walk around with 30-137 gems for hundreds of rounds. Our first tribute comes at round 1265-1523 (theirs 141-247). We lose 430-670 gems on death per game, and 1-9 of our deaths per game are to the monolith. |
| **01boss_battle** | 5-4 | One altar, next to a monolith. Both sides bank late (around round 1000). We die 16-30 times per game, **7-19 of them to the monolith**. We win when we take the monolith's 400-1200 gems and lose when we don't. |
| **00lost_world** | 0-4 | **Low yield, slow banking.** Our captures pay 5-8 gems, theirs 13-18. We capture ~350, they capture ~1000. They make 53-59 tributes, the first at round 40-64. |
| **00expanse** | 0-4 | Low yield (6-7 against 9-13 gems per capture). Their first tribute comes at round ~50, ours at round 176-288. |
| 00quadrants | 2-4 | Their first tribute comes at round 33-80, ours at ~127. The golem group (240 gems) decides the race. |

Maps we always won (2+ games): 00monolith, 00road_of_riches, 00swirl, 01fracture, 01hooks.

## What it means for the bot (sensing blocks, in the coordinator's format)

1. **Monolith deaths: the largest, a bug-level gap.** We die to a monolith up to 20 times per game on monolith maps.
   - The bot would need to observe **a monolith's threat zone and state**: whether it is awake or aggroed, its attack range, and turns until it can hit me.
   - It would also need **whether my path or my target tile is inside that zone**.
   - Proposed blocks: `monolith_threat(Tile)` (the monolith damage per turn a champion standing on the tile would take) and `in_monolith_zone()`.
2. **Banking at monolith-guarded altars (01shortcut).** We would need to observe **whether an altar-adjacent tile is outside the monolith's attack zone and free**. Opponents bank there 10-25 times per game, so it can be done.
   - Today's static rule (exclude altars within 5 of a monolith) leaves no altar at all on that map.
   - Proposed block: `altar_safe_tiles()` (altar-adjacent tiles that no monolith can hit), replacing the radius-5 exclusion.
3. **Slow first bank.** We would need to observe **the gems-per-turn value of banking now against farming on**, early in the game. That is `group_rate` / `altar_eta` from `docs/SENSING_BLOCKS.md`. The opponents' first trip at round ~104, against our ~190, is worth about 30-100 gems by round 250-750 in our losses.
4. **Low yield on open maps (00lost_world, 00expanse).** `group_rate(Tile)`, the gems per turn of a group including travel and kill time (`docs/SENSING_BLOCKS.md` rank 2). There our captures pay half of theirs.

## 4. Why we die to monoliths: our own hits

For each of our monolith deaths (ranked v21-v24), I took the last champion to hit that monolith in the 150 rounds before: a basic attack on it, or a cast within 2 tiles.

| map | monolith deaths | last hit by the victim | by an ally | by an opponent | nobody in 150 rounds |
|---|---|---|---|---|---|
| 00great_wall | 81 | 68 | 11 | 1 | 1 |
| 01shortcut | 29 | 21 | 4 | 1 | 3 |
| 01boss_battle | 143 | 42 | 29 | 30 | 42 |

On great_wall and shortcut it's self-inflicted. In v21/v24's policy (`tune-v21.policy`), the in-range camp attack `first( filter( camps, in_attack_range() ) )` hits any visible camp, monoliths included.
- On 00great_wall, all altars are within 3 tiles of a monolith. A ranged champion at the altar ring has the monolith in range and starts hitting it.
- On 01shortcut, the altar-blocker branch attacks the monolith next to the altar.
- The new `in_monolith_zone` / `monolith_threat` blocks only help if the in-range camp attack can be told not to pick a monolith it can't finish.

## 5. Why our captures pay less: the groups we choose (00lost_world)

00lost_world, 16 games across ranked and band; we lost almost all of them. Captures per game:
- **Opponents** repeat the richest groups: `gemx3` (21 gems) 19-33 times and `gemx2` (14 gems) 13-24 times. That is about 800-900 gems.
- **We** take `gemx3` only 1-6 times (14 once) and `gemx2` 1-8 times. We spend our captures on single gems (7 gems, 7-36 times), `wolfx2` (8 gems) and **pure gold groups worth 0 gems (5-13 times per game)**.

The map is symmetric, so the rich groups are on our side too. Our camp goal is the *nearest* spawn (`goals = closest(camp spawns − ...)`), not the richest per turn. Sensing needed: `group_rate(Tile)` = gems ÷ (travel + kill + capture turns), with gold-only groups at 0.

## 6. Loss causes across all ranked losses (v21, v22, v24; 75 losses)

Labels come from `analysis/live_digest.py`. A loss can have several.

| cause | share of losses |
|---|---|
| low yield (our gems per capture < 70% of theirs) | 59% |
| fights (we die 2x+ as often to champions, 8+ deaths) | 51% |
| 250+ gems lost on death | 35% |
| slow start (their first tribute 60+ rounds earlier, and they lead at round 500) | 32% |
| monolith (5+ deaths to monoliths) | 19% |
| no bank (our first tribute after round 600) | 13% |

The most common combinations are fights + low yield (10), slow start alone (7), low yield + slow start (6), and low yield alone (5).

Latest batch (18:00): v24 lost 0-5 to cory. All 5 losses had low yield (their gems per capture were 1.6-2.8x ours), with 18 camp deaths on 00reverse_spiral and 40 champion deaths on 00fragment.

## 7. Carriers stalled by enemy altar locks (18% of games)

Found while digging into a v24 loss on 01the_farm (18:50, 66-1011):
- The enemy locked both central altars, (26,22) at round 88 and (23,22) at round 183.
- Our three champions then stood about 5-7 tiles from them, holding 27-35 gems each, for about 400 rounds. They barely acted, then died.
- The enemy banked 8 times at those altars in the meantime.

**Detector (`analysis/stalls.py`):** a carrier stall is one of our champions with 20+ gems staying within 2 tiles of one spot for 60+ rounds while alive.

Over 410 live games of v21-v24 (ranked and unranked):
- **73 games (18%) have a stall**, totalling 43,495 champion-rounds.
- **The stall games go 16-57 (22% wins)**, against 132-205 (39%) for the rest.
- **201 of the 256 stalls (about 36,000 of the champion-rounds) are next to an altar the enemy has locked.** Another 27 are next to an altar within 5 of a monolith, and 28 are 4-9 tiles from any altar.
- The most-hit maps are 01boss_battle (18 games), 01broken_curve (11), 00gemfight (6), 00reverse_spiral (5), 00elkring, 00quadrants and 00lost_world (4 each), and 01the_farm (3).

In v21/v24's policy, a locked altar is attacked only when the carrier is already next to it (`first( filter( altars(), within(1, position()) ) )` → tribute, which hits the lock). The walk targets `minus( safe_altar_ring, ring(locked_altars(), 1) )`, then `safe_altar_ring`.
- I haven't confirmed the exact branch.
- But the effect is that our carriers wait near the locked altar instead of either breaking the lock (5 basic attacks) or walking to another altar.

**Sensing the bot would need:**
- whether the altar is locked by the enemy, and how many hits it takes to clear (`locked_altars()` exists; a `lock_hits_left(Tile)` would help);
- the path turns to the nearest *open* altar against the time to break the lock;
- turns spent idle while carrying (`turns_idle()` exists): a stall is directly observable.
