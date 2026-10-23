# v7zg-cast: 01the-farm, 01starvation, 01big-world (simulator diagnosis)

Requested from docs/LADDER_LOSSES_V7.md (analysis/sprint1). Policy `policies/v7zg-cast.policy`
(interp/v0 f848dcd). Tools:
- `GAME_EVENTS=1`: one `@@EV` line per champion death (with the killing camp type and group, or
  champion), camp kill, group capture (gems, gold) and champion hit on a camp. Simulator only.
- `INTERP_TRACE=1`: which `end_turn()` ended each turn (see FARM_DIAGNOSIS.md).

All runs: the simulator with fuel enforced. "vs base" = variant as A against v7zg-cast. Global
checks: 40 maps × 2 sides with `--bot-seeds` (what cambc will say), and 400 games with
per-game seeds (40 maps × 5 seeds × 2 sides).

## 01big-world: monolith deaths. Fixed.

A v7zg-cast mirror loses 10-16 champions per game to monoliths (40 and 63 over 4 games). The
hits show why. The groups `gem_cluster×4 + monolith` (16, 17) take 755-875 hits per side for
3-4 captures. Goals exclude only the monolith's own tile, so champions farm the gem clusters
inside its range-5 kill zone. The camp-attack branch also hits any camp in range. A group
cannot be captured without killing the monolith anyway.

Fix (`policies/v7zg-monozone.policy`): `keep monolith_zone = ring(monolith_tiles(), 5)`. Goals
exclude `monolith_zone` instead of just `monolith_tiles()`, and the camp-attack branch skips
camps standing in it.

| 01big-world, 20 games | wins | gems | captures | monolith deaths / game |
| --- | --- | --- | --- | --- |
| v7zg-monozone | 14/20 | 990 | 62.0 | 0.0 |
| v7zg-cast | 6/20 | 890 | 47.2 | 13.3 |

All maps: `--bot-seeds` 41/80, per-game seeds 208/400 (neutral elsewhere).

## 01starvation: the elk x4 group. Cause found; no clean fix yet.

In a mirror, 151 of the deaths over 4 games come from one group, `elk×4 + gem_cluster×4 +
gold_cluster×4` (group 2, 88 gems). It takes about 2,000 hits per side for 13-14 captures.
The victims' last three turns: they fight it (camp-attack branch), drop below 30%, then try
to walk home (retreat line) or start a recall. Four elks deal ~240 a turn at range 4. From
30% a champion cannot cover the 4 tiles out of range, and damage interrupts recalls.

Tried:

| variant | 01starvation vs base (20 games) | all maps: bot-seeds / per-game seeds |
| --- | --- | --- |
| skip groups worth >= 80 gems (`rich_spawns(80)`) | 10/20; gems 671 vs 578; captures 75.6 vs 37.6; elk deaths 9.8 vs 16.4 | 42/80, 194/400 |
| same, only when alone (no ally within 4) | 10/20; gems 685; elk deaths 15.2 | 39/80, 209/400 |
| monozone + skip >= 80 (`policies/v7zg-monozone-elkskip.policy`) | 10/20; gems 649; elk deaths 9.6, monolith 1.6 | 41/80, 188/400 |
| retreat at 50% when in danger | 9/20; elk deaths 19.1 | 17/80, 77/400 (much worse) |

Skipping the group roughly doubles captures on 01starvation and cuts elk deaths ~40%. But
`rich_spawns(80)` also drops valuable, safe groups on other maps (slightly negative overall).
Skipping alone also sends champions into monolith range here (in a skip-only mirror, monolith
deaths rose to 68 per 4 games), hence the combination with monozone. Better targeted would be a
block that rates a group by its threat (e.g. total camp strength / range of its living camps)
rather than its value. The low gold on the ladder (974 vs 6,166) does not reproduce in a
mirror (~3,000 gold per side per game), so it is probably the opponent outpacing us there.

## 01the-farm: the ladder failure does not reproduce in a mirror

After the fog-camps fix, a v7zg-cast mirror on 01the-farm captures normally (808/876 gems,
~58 captures per game). Over 10 games, 785 of 1,085 engagements on elk/wolf groups end in a
capture. The 300 abandoned ones break off mostly to tribute when the bag reaches 10 (70),
retreat at 30% (61), switch goal (53), attack another camp (39) or die (49). That is leakage,
not the ladder's 4 captures in 1,664 rounds.

Tried: finish a camp in range before leaving to tribute. It lost 0/20 to base on the farm.
Champions stayed in fights holding gems and died to enemies (7.7 per game).

So the 48-1023 loss looks like that opponent's pressure (V4.1 Flash: Heart of Ruin, Ren, Ryth),
which a mirror cannot show. With that game's replay (.repl26a) the same tools can locate it
turn by turn.

## Telling gold-rush from big-world (v8 follow-up)

v8 skips whole monolith groups (`group_tiles(monolith_tiles())`). Against v7zg-cast, 20 games
per map, its result tracks one static number: the share of the map's gems that sits in
monolith groups.

| map | share in monolith groups | v8 wins / 20 |
| --- | --- | --- |
| 01gold-rush, 00rows, 00monolith, 01starvation | 75-80% | 2, 4, 9, 10 |
| 00great-wall | 59% | 5 |
| 01big-world, 01corridors, 00split, 01fracture, 00lost-world | 38-57% | 11-20 |

Where monolith groups hold most of the gems, skipping them leaves too little to score. Whether
the group's other camps are in the monolith's range does not separate the maps (both kinds have
them in range). The share is computable today from static tile sets: per-type camp counts times
the type's gems (elk 15, gem cluster 7, wolf 4, golem 36, monolith 200), with intersections
`minus(A, minus(A, B))` against `group_tiles(monolith_tiles())`.

`policies/v8-adaptive.policy` skips whole monolith groups only when the share is under 60%,
and otherwise only the monolith tiles:

| vs v7zg-cast | v8 | v8-adaptive |
| --- | --- | --- |
| 01gold-rush (60 games) | 6/60 | 28/60 |
| 00rows (60 games) | 18/60 | 31/60 |
| 01big-world (20) | 14/20 | 15/20 |
| all maps, `--bot-seeds` | 42/80 | 43/80 |
| all maps, per-game seeds | 219/400 | 221/400 |

A block `group_gems(TileSet) -> Num` (total gems of the groups touching the set) would make
this one short line, and cheaper than the five counts.

## Proposed block for 01starvation: group threat

`group_threat(Tile) -> Num`: for the camp group with a spawn on that tile (0 if none), the summed
strength (damage per turn when awake) of its living camps. Living camps are those in vision
and alive; an unseen camp counts as alive at full strength, as in the fog-camps rule. Elk 60,
wolf 20, golem 120, monolith 200, clusters 0. The elk x4 group reads 240.

Companion: `group_hp(Tile) -> Num`, the summed health of the same camps. The policy can then
estimate the cost of a fight. Clearing takes about `group_hp / (our damage × helpers)` turns,
taking `group_threat` each turn. So it can skip a goal when
`group_threat(g) * group_hp(g) / (strength() * (1 + allies_within(4))) > health()`. Both are
static camp data plus the camp records the interpreter already reads (no new engine calls
beyond `camp()` per member).
