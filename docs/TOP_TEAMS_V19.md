# v19 (rall2-ca4-lean-g) vs the top teams, against tune-5 and v17

v19 is v18 plus two changes: cast-ahead, and a fuel gate on the retreat dash. It went live at ~08:26 UTC on 24 Oct.

The comparison:
- Same 10 unranked groups as `docs/TOP_TEAMS.md` and `docs/TOP_TEAMS_V17.md`: same teams, maps and sides, 50 games each.
- The v19 groups were created at 08:29 and finished between 08:29 and 08:31, so they are all v19.
- Replays are in `data/top-teams-v19-2026-10-24/`. Tool: `analysis/top_compare.py`.

**Result: 4-46, our first wins against the top teams.**
- vc? 3-2: 00eight 1021-516, 00gemfight 1021-331, 01the_farm 1008-785.
- prism best girl 1-4: 00quadrants 1023-845.
- Against the other eight teams nothing changed (0-40).

## Per game

| per game | tune5 | v17 | v19 |
|---|---|---|---|
| games, W-L | 50, 0-50 | 50, 0-50 | 50, 4-46 |
| gems submitted us / them | 180 / 1038 | 206 / 1037 | 260 / 1003 |
| deaths us / them | 17.8 / 1.6 | 18.5 / 1.6 | 16.3 / 1.8 |
| kills us / them | 0.3 / 12.9 | 0.5 / 13.8 | 0.5 / 13.1 |
| champion damage us / them | 7.0k / 21.4k | 7.9k / 23.7k | 9.6k / 23.6k |
| gems per capture us / them | 11.8 / 21.5 | 11.1 / 21.9 | 11.7 / 21.8 |
| captures us / them | 37.4 / 54.4 | 39.7 / 54.2 | 43.9 / 52.8 |
| tributes us / them | 5.7 / 24.2 | 6.5 / 24.7 | 8.0 / 24.5 |
| median bag us / them | 28 / 36 | 27 / 36 | 28 / 34 |
| gems lost dying us / them | 140 / 11 | 135 / 18 | 133 / 25 |
| gold earned us / them | 3.0k / 8.3k | 3.1k / 8.5k | 3.5k / 8.2k |
| our deaths with 2+ of theirs within 5 | 69% of 645 | 70% of 688 | 71% of 656 |

| opponent | tune5 W-L (gems us-them) | v17 W-L (gems us-them) | v19 W-L (gems us-them) |
|---|---|---|---|
| :3 | 0-5 (241-1069) | 0-5 (312-1037) | 0-5 (302-1024) |
| Claudus Maximus | 0-5 (107-1048) | 0-5 (165-1058) | 0-5 (204-1046) |
| Intercontinental Fish | 0-5 (140-1014) | 0-5 (178-1014) | 0-5 (146-1018) |
| Mite | 0-5 (120-1022) | 0-5 (83-1010) | 0-5 (122-1037) |
| Univardisty of Shingtonwash | 0-5 (210-1009) | 0-5 (193-1022) | 0-5 (253-1016) |
| policy wonk | 0-5 (184-1136) | 0-5 (331-1120) | 0-5 (256-1041) |
| prism best girl | 0-5 (88-1037) | 0-5 (87-1044) | 1-4 (277-1061) |
| procless | 0-5 (289-1012) | 0-5 (305-1033) | 0-5 (260-1010) |
| vc? | 0-5 (246-1018) | 0-5 (298-1010) | 3-2 (693-745) |
| willow best girl | 0-5 (171-1015) | 0-5 (109-1018) | 0-5 (89-1032) |

## Decisive fights (our champion dies, no kill back within 10 rounds)

| | tune-5 (634) | v17 (671) | v19 (646) |
|---|---|---|---|
| first champion damage by us | 23% | 19% | **32%** |
| victim damaged one of theirs before dying | 65% | 67% | **73%** |
| their side acted first in the round of the first hit | 47% | 47% | 50% |
| their champions damaging the victim, 2+ | 67% | 66% | 67% |
| fights before round 150: 2+ hitters | 89% | 85% | 80% |
| item points after round 400, killer vs victim | 58 vs 12 | 66 vs 11 | 59 vs 11 |
| victim hitting a camp in the 5 rounds before | 31% | 29% | 30% |

## Reading

What improved:
- v19 strikes first more often (32% vs 19-23%) and hits back more often before dying (73%). This is consistent with cast-ahead.
- Champion damage is up 22% on v17 (9.6k vs 7.9k), and tributes are up to 8.0 from 6.5.

What didn't change:
- Deaths are 16.3 against their 1.8, and 71% of our deaths still come with 2+ of theirs within 5 tiles.
- They still get the item snowball after round 400.
- The rules from `docs/TOP_TEAMS_FIGHTS.md` that aren't implemented yet are still open: leave when outnumbered, a visible enemy pre-empts camp attacks, target the damage dealer, group up.

The wins:
- vc?: on 00eight our deaths fell from 52 to 18 while theirs rose to 11; on 00gemfight from 33 to 7 (theirs 8).
- In the 4 wins we tributed 27-30 times; in the v17 losses on the same maps, 0-23 times.
- These are vc?'s maps where fights stay small: vc? drafts 3-4 champions on 00gemfight and 01the_farm.

## Ranked

- **v18 final** (groups 07:40-08:20): 11-14.
  - JBG fam 2-3, LigaSiur 2-3, Silent Pathfinders 5-0, newtern 1-4, Gobfrey 1-4.
- **v19** (groups from 08:30): 2-8 so far.
  - TEST-DUMMIES 2-3, Index[0] 0-5.
  - The full record follows at about 20 games.
