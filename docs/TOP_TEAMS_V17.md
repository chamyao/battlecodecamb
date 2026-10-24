# v17 (tune5-campreset) vs the top teams: before/after against tune-5

v17 adds attack → reset → attack, against both champions and camps. It went live at ~07:08 UTC on 24 Oct.

The comparison:
- Same 10 unranked groups as `docs/TOP_TEAMS.md`: same teams, maps and sides, 50 games each.
- Replays are in `data/top-teams-v17-2026-10-24/`.
- Tool: `analysis/top_compare.py`. Fight aggregates come from `analysis/fight_dump.py`.

**Result: 0-50 again.** Every metric moved by less than its game-to-game noise.

## Per game

| per game | tune-5 (v16) | v17 |
|---|---|---|
| W-L | 0-50 | 0-50 |
| gems submitted, us / them | 180 / 1038 | 206 / 1037 |
| deaths, us / them | 17.8 / 1.6 | 18.5 / 1.6 |
| kills, us / them | 0.3 / 12.9 | 0.5 / 13.8 |
| champion damage, us / them (official summaries) | 7.0k / 21.4k | 7.9k / 23.7k |
| gems per capture, us / them | 11.8 / 21.5 | 11.1 / 21.9 |
| captures, us / them | 37.4 / 54.4 | 39.7 / 54.2 |
| tributes, us / them | 5.7 / 24.2 | 6.5 / 24.7 |
| median bag, us / them | 28 / 36 | 27 / 36 |
| gems lost dying, us / them | 140 / 11 | 135 / 18 |
| gold earned, us / them | 3.0k / 8.3k | 3.1k / 8.5k |
| our deaths with 2+ of theirs within 5 tiles | 69% of 645 | 70% of 688 |

| opponent | tune-5 W-L (gems us-them) | v17 W-L (gems us-them) |
|---|---|---|
| :3 | 0-5 (241-1069) | 0-5 (312-1037) |
| Claudus Maximus | 0-5 (107-1048) | 0-5 (165-1058) |
| Intercontinental Fish | 0-5 (140-1014) | 0-5 (178-1014) |
| Mite | 0-5 (120-1022) | 0-5 (83-1010) |
| Univardisty of Shingtonwash | 0-5 (210-1009) | 0-5 (193-1022) |
| policy wonk | 0-5 (184-1136) | 0-5 (331-1120) |
| prism best girl | 0-5 (88-1037) | 0-5 (87-1044) |
| procless | 0-5 (289-1012) | 0-5 (305-1033) |
| vc? | 0-5 (246-1018) | 0-5 (298-1010) |
| willow best girl | 0-5 (171-1015) | 0-5 (109-1018) |

## Did the combo fire?

Yes. Per game, rounds in which one champion did attack > reset > attack:

| | tune-5: us | v17: us | top teams |
|---|---|---|---|
| against champions | 0 | 14.5 | 15.6 |
| against camps | 0 | 88.8 | 96 |
| reset casts | 0 | 128 | 131 |
| rounds attacking a champion | 79 | 76 | 121 |

So v17 uses the reset as often as the top teams do. The extra damage shows up: our champion damage rose 13% (7.0k to 7.9k). Their damage also rose, from 21.4k to 23.7k.

Two things are unchanged:
- We still spend fewer rounds attacking champions than they do (76 vs 121).
- We still die outnumbered (70% of our deaths have 2+ of theirs within 5 tiles).

## Decisive fights (our champion dies, no kill back within 10 rounds)

| | tune-5 (634) | v17 (671) |
|---|---|---|
| first champion damage by them | 77% | 81% |
| their champions damaging the victim, 2+ | 67% | 66% |
| rounds from first hit to death (median) | 10 | 9 |
| stat gap after round 400 (strength / focus / max HP) | +68 / +80 / +800 | +105 / +80 / +900 |
| item points after round 400 (killer vs victim) | 58 vs 12 | 66 vs 11 |
| fights before round 150: 2+ hitters | 89% | 85% |

## Reading

The reset was one of the seven rules in `docs/TOP_TEAMS_FIGHTS.md`, and the least important one. The combo now matches theirs. But the fights are still lost to the other rules:
- **Numbers.** 85% of early deaths are to 2 or more of their champions, at 0 item points each.
- **Staying in visible fights.** 29% of victims were hitting a camp in the 5 rounds before the first hit.
- **Targeting.** We hit the closest enemy, often the shielded HoR.
- **The item snowball** that follows.

A 13% damage gain doesn't change a 3:1 damage ratio.

Next candidates, in order:
1. Count enemies within 8 against allies within 5, and leave early when outnumbered.
2. A visible enemy pre-empts camp attacks.
3. Target the enemy that is damaging us, then ranged carries.
4. Group the team so that the 2v1s go our way.

## Ranked

v18 (tune-r-all-v2) was submitted at ~07:27 UTC, so only the ranked groups created at 07:10 and 07:20 are v17:
- **v17: 7-3** (Rataturing 4-1, octo's odyssey 3-2).
- The 07:30 group is ambiguous: Lucky Boy 4-1.
- The 07:40 group onward is v18: JBG fam 2-3.

The top-team groups above all finished by 07:20:40, so they are all v17.
