# Ladder losses: v7, v7-zerogem, v7zg-cast (23 Oct, 20:43-21:35 UTC)

Data: our ranked games since 20:00 UTC (35 finished), split by the coordinator's upload times:
v5d-fs2 from 19:22, v7 from 20:43, v7-zerogem from 20:54, v7zg-cast from 21:14 (±5 min is
ambiguous). Report: `analysis/v7_report.md` (`analysis/v6_report.py` with version boundaries).
Previous rounds: `docs/LADDER_LOSSES_V6.md`.

| version | games | W-L | losses |
|---|---|---|---|
| v5d-fs2 (20:00-20:43) | 20 | 11-9 | fights (Chocolate icecream, Velvet Wolves, ohhhhhh caml), elk deaths on 01starvation/01corridors |
| v7 | 5 | 3-2 | TrueCoders: 650-1011, 689-1013 |
| v7-zerogem | 5 | 1-4 | V4.1 Flash: quadrants 817-1028, big_world 629-1017, starvation 451-492, the_farm 48-1023 |
| v7zg-cast | 5 | 1-4 | DeepSleep: expanse 507-1036, packs 336-1022, rows 119-748, big_world 784-1066 |

The samples are small (5 games each, one opponent per version), but the v7-line losses share a
pattern.

## The v7 line loses on scoring rate, not on fights

- **Few deaths.** v7zg-cast's losses had 0, 5, 8 and 11 deaths; v7-zerogem's 2-18, except
  01starvation (44, 42 to elks). The v6 problem (21-34 deaths per game to stun/dive teams) does
  not show here.
- **No freezes.** No lock stalls, no 0-gem games; idle time is near zero.
- **We capture as often but score half.** Over the 10 v7-line losses: our 364 captures gave
  5,411 gems; their 457 gave 9,673. `00expanse` vs DeepSleep: 98 captures for 537 gems vs their
  61 captures for 1,080.

### Cause 1: camp choice ignores value (all v7-line losses)

Our most-captured groups in these losses:

| group | our captures | gems |
|---|---|---|
| gold x2 | 66 | 0 |
| elk + gold x2 | 40 | 600 |
| gold x3 | 32 | 0 |
| wolf | 31 | 124 |
| gold + wolf | 26 | 104 |
| gold x2 + wolf x2 | 24 | 192 |

Theirs, by gems:

| group | their captures | gems |
|---|---|---|
| elk x2 + gem x2 + gold | 22 | 968 |
| elk x2 + gem x4 | 12 | 696 |
| elk x2 + gem x3 | 13 | 663 |
| gem x4 + gold x5 | 23 | 644 |
| elk x2 + gem + gold x2 + wolf | 14 | 574 |
| gem x4 + monolith | 2 | 456 |

Our goal is `closest(goals)` over every camp spawn except monoliths and golems, so we take
whatever is nearest: gold clusters (0 gems) and wolves (4). They go for groups with gem
clusters and elks (30-60 gems per capture). Gold-only captures are 27% of ours (98 of 364).
That is useful early, for items, but by mid-game it costs the race.

### Cause 2: monoliths, the other side of the coin (01big_world x2)

DeepSleep captured both monoliths on 01big_world (456 gems, the difference in a 784-1066
loss). We died 8 and 15 times to monoliths there: we fight near them without taking them. The
coordinator's private arena shows the same thing on contest (the house bot takes both
monoliths).

### Cause 3: map-specific leftovers

- `01the_farm` (third loss in a row on this map, 48-1023): 159 attacks on elks but only 4
  captures in 1,664 rounds, with most of our time around (15-19, 10-19). We hit elk groups
  without finishing them.
- `01starvation`: 42 elk deaths (v7-zerogem), as in every version so far.

## Opponents

| opponent | our W-L | their draft | deaths us/them per game | their median bag |
|---|---|---|---|---|
| DeepSleep | 1-4 | Vendetta, Vesper, Ryth (+ Marcella, Prism) | 11.0 / 4.8 | 39 |
| V4.1 Flash | 1-4 | Heart of Ruin, Ren, Ryth (+ Vesper, Marcella) | 18.0 / 4.2 | 29.5 |
| TrueCoders | 3-2 | Cassi, Stellar, Ren (+ Ryth) | 10.2 / 25.0 | 30 |

All three tribute bags 2-3x ours (median 14), and take the gem-rich groups.

## Suggestions

1. **Value-weighted camp choice.** Expressible now with the static tile sets: prefer
   `union(elk_tiles(), gem_cluster_tiles())` once a champion has a few items, and keep
   gold-only groups for the opening or a gold tiebreak. Better as a block:
   `group_value_tiles(min_gems) -> TileSet` (spawn tiles of groups worth >= N gems; the engine
   knows group rewards), or `best_goal(k)`: maximise gems per (travel + clear time).
2. **Bigger bags.** Ours median 14 vs their 29-44. Re-test a threshold of ~25 now that deaths
   are low (fs-2's >= 10 was chosen when we were still dying a lot).
3. **Monoliths with 3+ champions** on maps where they sit near our side (01big_world,
   contest), using `claim_count`. Opponents take them and it decides the race.
4. Check `01the_farm` in the simulator: why elk groups get hit but not captured.
