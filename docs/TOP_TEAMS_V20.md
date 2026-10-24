# v20 (tune-fight-2s) vs the top teams, against tune-5, v17 and v19

v20 is v19 plus one change: ward our own bush tile when no enemy is visible. It went live at ~11:35 UTC on 24 Oct.

The comparison:
- Same 10 unranked groups as before: same teams, maps and sides.
- The groups were created at 11:34 and finished between 11:34:48 and 11:36:43.
- They are all v20. v19 never placed a ward in its 50 games, while v20 placed wards in 44 of 50 from the first finished game on. The 6 games without a ward are on maps where the condition never triggered.
- Replays are in `data/top-teams-v20-2026-10-24/`. Tool: `analysis/top_compare.py`.

**Result: 0-50.** v19's 4 wins (vc? 3, prism best girl 1) are gone.

## Per game

| per game | tune5 | v17 | v19 | v20 |
|---|---|---|---|---|
| games, W-L | 50, 0-50 | 50, 0-50 | 50, 4-46 | 50, 0-50 |
| gems submitted us / them | 180 / 1038 | 206 / 1037 | 260 / 1003 | 189 / 1040 |
| deaths us / them | 17.8 / 1.6 | 18.5 / 1.6 | 16.3 / 1.8 | 16.9 / 1.3 |
| kills us / them | 0.3 / 12.9 | 0.5 / 13.8 | 0.5 / 13.1 | 0.6 / 13.9 |
| champion damage us / them | 7.0k / 21.4k | 7.9k / 23.7k | 9.6k / 23.6k | 10.6k / 26.2k |
| gems per capture us / them | 11.8 / 21.5 | 11.1 / 21.9 | 11.7 / 21.8 | 11.6 / 21.4 |
| captures us / them | 37.4 / 54.4 | 39.7 / 54.2 | 43.9 / 52.8 | 41.3 / 53.6 |
| tributes us / them | 5.7 / 24.2 | 6.5 / 24.7 | 8.0 / 24.5 | 6.1 / 25.0 |
| median bag us / them | 28 / 36 | 27 / 36 | 28 / 34 | 28 / 34 |
| gems lost dying us / them | 140 / 11 | 135 / 18 | 133 / 25 | 148 / 18 |
| gold earned us / them | 3.0k / 8.3k | 3.1k / 8.5k | 3.5k / 8.2k | 3.2k / 8.3k |
| our deaths with 2+ of theirs within 5 | 69% of 645 | 70% of 688 | 71% of 656 | 69% of 697 |

| opponent | tune5 W-L (gems us-them) | v17 W-L (gems us-them) | v19 W-L (gems us-them) | v20 W-L (gems us-them) |
|---|---|---|---|---|
| :3 | 0-5 (241-1069) | 0-5 (312-1037) | 0-5 (302-1024) | 0-5 (305-1027) |
| Claudus Maximus | 0-5 (107-1048) | 0-5 (165-1058) | 0-5 (204-1046) | 0-5 (82-1050) |
| Intercontinental Fish | 0-5 (140-1014) | 0-5 (178-1014) | 0-5 (146-1018) | 0-5 (167-1019) |
| Mite | 0-5 (120-1022) | 0-5 (83-1010) | 0-5 (122-1037) | 0-5 (73-1039) |
| Univardisty of Shingtonwash | 0-5 (210-1009) | 0-5 (193-1022) | 0-5 (253-1016) | 0-5 (200-1036) |
| policy wonk | 0-5 (184-1136) | 0-5 (331-1120) | 0-5 (256-1041) | 0-5 (248-1028) |
| prism best girl | 0-5 (88-1037) | 0-5 (87-1044) | 1-4 (277-1061) | 0-5 (179-1097) |
| procless | 0-5 (289-1012) | 0-5 (305-1033) | 0-5 (260-1010) | 0-5 (319-1017) |
| vc? | 0-5 (246-1018) | 0-5 (298-1010) | 3-2 (693-745) | 0-5 (180-1055) |
| willow best girl | 0-5 (171-1015) | 0-5 (109-1018) | 0-5 (89-1032) | 0-5 (140-1033) |

## Why v19's wins disappeared: vc? changed its bot; the prism win may be the ward

The engine is deterministic, and so are most of these bots. So a v19 game and its v20 rerun are identical unless one side's behaviour changed. For each pair I found the first event that differs, and whose action it is:

| first divergence | games | opponents |
|---|---|---|
| identical game (same score and round count) | 7 | :3, Fish 2, Univardisty 2, policy wonk, prism |
| our action first (the ward rule) | 20 | most teams |
| *their* action first | 8 | **vc? 3**, Mite 3, willow 2 |
| both in the same event slot (order within the round; can't tell) | 15 | |

- **vc? changed its bot between 08:30 and 11:35.** Its first differing action comes at round 2 on 01the_farm and 01starvation, before any ward of ours. On 01the_farm our v20 placed no ward at all. Its other two games are ambiguous at rounds 1 and 9.
  - So v19's 3-2 against vc? was against an older vc?, and v20's 0-5 doesn't show that the ward rule is worse there.
  - Mite and willow also updated, which doesn't matter here (0-5 throughout).
- **prism best girl did not visibly change.** Its games diverge on our action first (wards from round 12-20). The 00quadrants win (1023-845 under v19, 472-1053 under v20) diverges at round 19, when our first ward goes down. **The ward rule may have cost that game.**
- To settle the vc? part, someone would need to rerun v19 against the current vc?. I can't do that from the analysis line.

## Decisive fights (our champion dies, no kill back within 10 rounds)

| | tune-5 (634) | v17 (671) | v19 (646) | v20 (675) |
|---|---|---|---|---|
| first champion damage by us | 23% | 19% | 32% | 33% |
| victim damaged one of theirs before dying | 65% | 67% | 73% | **76%** |
| killer unseen in the 3 rounds before the first hit | 26% | 26% | 30% | 33% |
| their champions damaging the victim, 2+ | 67% | 66% | 67% | 67% |
| victim hitting a camp in the 5 rounds before | 31% | 29% | 30% | 27% |
| item points after round 400, killer vs victim | 58 vs 12 | 66 vs 11 | 59 vs 11 | 52 vs 11 |

## Reading

- Fighting quality keeps its v19 gains: we land the first damage 33% of the time and hit back before dying 76%. Champion damage is up again, to 10.6k from 9.6k.
- The ward doesn't reduce surprise deaths. Kills by a champion unseen for 3 rounds rose slightly, from 30% to 33%.
- Gems are back to v17 levels (189 vs v19's 260), with 6.1 tributes per game. Most of that drop is the lost vc? and prism games.
- The structural gaps are unchanged: 69% of our deaths come with 2+ of theirs within 5 tiles, and the item snowball is about 5:1.

## Ranked

- **v19 final** (groups 08:30-11:30): **55-40**.
  - The 11:30 group, Wildest_Peace 4-1, is probably still v19. Without it, v19 is 51-39.
  - Best: Arasaka 5-0, MFF - Policka 5-0.
  - Worst: Index[0] 0-5, `-` 1-4, Quantum Lock Pickers 1-4, Silent Gem Thieves 1-4.
- **v20** (groups from 11:40): the record follows at about 20 games.
