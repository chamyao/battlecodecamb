# v21 (tune-v20-L1c) vs the top teams, against tune-5, v17, v19 and v20

v21 is v20 plus one altar lock per team. It went live around 12:40 UTC on 24 Oct.

The comparison:
- Same 10 unranked groups as before: same teams, maps and sides.
- The groups were created at 12:39:09 and finished by 12:39:34.
- They are v21: we placed altar locks in 40 of 50 games, and no earlier version ever placed one.
- Replays are in `data/top-teams-v21-2026-10-24/`. Tools: `analysis/top_compare.py`, `analysis/altar_locks.py`.

**Result: 1-49.** The win is vc? on 00eight, 1022-842.
- vc? on 00gemfight was close: 976-1076.
- Against the other nine teams v21 is 0-45.

## Per game

| per game | tune5 | v17 | v19 | v20 | v21 |
|---|---|---|---|---|---|
| games, W-L | 50, 0-50 | 50, 0-50 | 50, 4-46 | 50, 0-50 | 50, 1-49 |
| gems submitted us / them | 180 / 1038 | 206 / 1037 | 260 / 1003 | 189 / 1040 | 228 / 1024 |
| deaths us / them | 17.8 / 1.6 | 18.5 / 1.6 | 16.3 / 1.8 | 16.9 / 1.3 | 16.4 / 1.7 |
| kills us / them | 0.3 / 12.9 | 0.5 / 13.8 | 0.5 / 13.1 | 0.6 / 13.9 | 0.8 / 13.6 |
| champion damage us / them | 7.0k / 21.4k | 7.9k / 23.7k | 9.6k / 23.6k | 10.6k / 26.2k | 10.4k / 25.2k |
| gems per capture us / them | 11.8 / 21.5 | 11.1 / 21.9 | 11.7 / 21.8 | 11.6 / 21.4 | 11.5 / 20.7 |
| captures us / them | 37.4 / 54.4 | 39.7 / 54.2 | 43.9 / 52.8 | 41.3 / 53.6 | 42.4 / 55.2 |
| tributes us / them | 5.7 / 24.2 | 6.5 / 24.7 | 8.0 / 24.5 | 6.1 / 25.0 | 7.1 / 24.9 |
| median bag us / them | 28 / 36 | 27 / 36 | 28 / 34 | 28 / 34 | 28 / 36 |
| gems lost dying us / them | 140 / 11 | 135 / 18 | 133 / 25 | 148 / 18 | 132 / 28 |
| gold earned us / them | 3.0k / 8.3k | 3.1k / 8.5k | 3.5k / 8.2k | 3.2k / 8.3k | 3.3k / 8.4k |
| our deaths with 2+ of theirs within 5 | 69% of 645 | 70% of 688 | 71% of 656 | 69% of 697 | 69% of 680 |

| opponent | tune5 W-L (gems us-them) | v17 W-L (gems us-them) | v19 W-L (gems us-them) | v20 W-L (gems us-them) | v21 W-L (gems us-them) |
|---|---|---|---|---|---|
| :3 | 0-5 (241-1069) | 0-5 (312-1037) | 0-5 (302-1024) | 0-5 (305-1027) | 0-5 (316-1031) |
| Claudus Maximus | 0-5 (107-1048) | 0-5 (165-1058) | 0-5 (204-1046) | 0-5 (82-1050) | 0-5 (145-1012) |
| Intercontinental Fish | 0-5 (140-1014) | 0-5 (178-1014) | 0-5 (146-1018) | 0-5 (167-1019) | 0-5 (174-1014) |
| Mite | 0-5 (120-1022) | 0-5 (83-1010) | 0-5 (122-1037) | 0-5 (73-1039) | 0-5 (60-1019) |
| Univardisty of Shingtonwash | 0-5 (210-1009) | 0-5 (193-1022) | 0-5 (253-1016) | 0-5 (200-1036) | 0-5 (207-1011) |
| policy wonk | 0-5 (184-1136) | 0-5 (331-1120) | 0-5 (256-1041) | 0-5 (248-1028) | 0-5 (282-1028) |
| prism best girl | 0-5 (88-1037) | 0-5 (87-1044) | 1-4 (277-1061) | 0-5 (179-1097) | 0-5 (196-1058) |
| procless | 0-5 (289-1012) | 0-5 (305-1033) | 0-5 (260-1010) | 0-5 (319-1017) | 0-5 (321-1018) |
| vc? | 0-5 (246-1018) | 0-5 (298-1010) | 3-2 (693-745) | 0-5 (180-1055) | 1-4 (463-1025) |
| willow best girl | 0-5 (171-1015) | 0-5 (109-1018) | 0-5 (89-1032) | 0-5 (140-1033) | 0-5 (113-1022) |

## Altar locks and altar fights

| per game, us / them | tune5 | v17 | v19 | v20 | v21 |
|---|---|---|---|---|---|
| locks placed | 0.0 / 1.3 | 0.0 / 1.1 | 0.0 / 1.1 | 0.0 / 1.6 | 0.8 / 1.7 |
| basic attacks on altar locks | 1.3 / 0.0 | 1.2 / 0.0 | 1.1 / 0.0 | 2.1 / 0.0 | 2.9 / 1.8 |
| tribute starts | 6.0 / 24.5 | 6.7 / 25.0 | 8.3 / 25.1 | 6.4 / 25.7 | 7.3 / 25.4 |
| tributes completed | 5.7 / 24.2 | 6.5 / 24.7 | 8.0 / 24.5 | 6.1 / 25.0 | 7.1 / 24.9 |
| champion deaths within 6 of an altar | 5.7 / 0.1 | 5.9 / 0.3 | 5.7 / 0.4 | 6.6 / 0.4 | 6.1 / 0.5 |
| tribute starts not completed | 4% / 1% | 4% / 1% | 4% / 2% | 5% / 2% | 3% / 2% |
| games with a lock, us / them; median first-lock round | 0 / 23; 0 / 186 | 0 / 21; 0 / 137 | 0 / 22; 0 / 138 | 0 / 27; 0 / 177 | 40 / 27; 234 / 143 |

How each of our 40 locks played out:
- **Placement.** The median first lock comes at round 234; theirs at round 143.
- **Cancelled tributes.** Only 1 of our 40 locks went down within 12 rounds of an enemy tribute start at that altar. So the lock almost never cancels a tribute in progress.
- **Their tributes at the locked altar** barely change: 14 starts in the 100 rounds before the lock, 12 in the 100 rounds after. Over the whole game their tributes are 24.9 per game (v20 25.0), and their share of tribute starts not completed is 2% (v20 2%).
- **Clearing.** They cleared 16 of our 40 locks with 5 basic attacks, a median of 106 rounds after placement. That is 1.8 attacks on locks per game for them; before v21 they never attacked one, because we had none.
- **Our own tributes at that altar fall after we lock it**: 55 starts before, 21 after. The lock seems to go down when we are about to leave the altar, not to hold it.
- **Altar fights barely move.** Our champion deaths within 6 tiles of an altar are 6.1 per game, against v20's 6.6 and tune-5's 5.7. Theirs are 0.5.

**Verdict:** our altar lock doesn't affect the altar fights against these teams. It doesn't deny their banking, and it doesn't change where or how often we die.
- To matter, the lock would have to go down on an altar they are about to use. For example, when an enemy carrier with gems is within ~6 tiles of an altar, or right after an enemy tribute starts, which cancels it.
- They lock at round ~140, earlier than our ~234.

## Decisive fights (our champion dies, no kill back within 10 rounds)

| | v19 (646) | v20 (675) | v21 (655) |
|---|---|---|---|
| first champion damage by us | 32% | 33% | 34% |
| victim damaged one of theirs before dying | 73% | 76% | 76% |
| killer unseen in the 3 rounds before the first hit | 30% | 33% | 27% |
| their champions damaging the victim, 2+ | 67% | 67% | 63% |
| victim hitting a camp in the 5 rounds before | 30% | 27% | 25% |
| item points after round 400, killer vs victim | 59 vs 11 | 52 vs 11 | 60 vs 11 |

Fights look the same as in v19 and v20. The early fights (before round 150) are still 90% two or more of theirs against one of ours.

The vc? result: v21 beat the current vc? on 00eight, which v20 lost 506-1008. So part of what v19 had against vc? survives the vc? update.

## Ranked

- **v20 final** (groups 11:40-12:30): **23-7**.
  - newtern 5-0, Quantcoders 2-3, Unharmful 4-1, Apex Gamma 4-1, ESILV - Hidden Wolves 4-1, Narla's Gang 4-1.
- **v21** (groups from 12:40): the record follows at about 20 games.
