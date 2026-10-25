# Intel batch notes (what changed in the gaps)

## Batch 1: 24 Oct 2026, 19:02 UTC, 50 games, 15-35

Correction: the live bot was v22 (tune-v20-L1c), not v23; see GAPS.md. The comparison below against the earlier
v23 band run is therefore v22 vs v23 on different teams, and v22's 25-gem banking explains the bags of 29.

The first batch for Arena B. Compared with the earlier v23 band run (`docs/GAP_LIST.md` on analysis/sprint1;
same bot, other band teams):
- **Same overall.** Record 15-35 (was 14-36); gems lost on death 155 (130); gems per capture 10.2 (10.8);
  deaths to champions 10.2 (12.3).
- **Banking looks different.** Tributes 18.5 per game with a median bag of 29, against the earlier run's 28.3
  and 18. These band teams lock altars (23 of 50 games) and our carriers get stuck.
- **New: stuck carriers** (2-cycle walking) is the top gap. It is in 12 of 35 losses and drives 3 of the 9
  near-zero games. The sim reproduces it (66.7 champion-rounds per game, real 77), so Arena A can find
  it too, but only if its fitness reaches those maps and states.
- **New: enemy altar locks** are frequent at this tier. The lockall stress opponent reproduces the
  00rushbait_v2 collapse in the sim.
- **Fights:** being outnumbered at the first hit no longer separates outcomes (40% vs 39%).
- **Monoliths:** a smaller cause than in the ranked v21-v24 games (2 of 35 losses), but the sim shows the
  mechanism, and the fix is cheap.

Directed children pushed: commit, mono-spare, mono-pack, gem-groups (see GAPS.md).

## Batch 2: 24 Oct 2026, 20:47 UTC, 50 games, 18-32 (B318 live, ladder v25)

This batch reruns batch 1's exact plan, so the games pair one to one: v22 → B318.
- Better: gems submitted +105 ± 49 per game, gems lost on death −63, first tribute at round 112 (was 230),
  twice the tributes, and carrier stuck spells 61 → 4.
- Unchanged: deaths to champions, camps and monoliths, and gems per capture (10.2 vs their 15.2).
- New: zero-gem maps. On 00contest we submit 0 and stand idle; its gems are only in monoliths, and B318's
  r_mono waits for round 1000. On 01elk_arena we submit 14.
- Top gaps for B318: yield (50% of losses), fights (44%), zero-gem maps, monoliths (12%), 01shortcut.

## Batch 3: 24 Oct 2026, 21:28 UTC, 50 games, 17-33 (v26 = B792 live; b1's exact plan)

This is a paired comparison with b2 (v25, B318) on the same 50 matchups. Record 18-32 → 17-33 (7 flips to a win,
8 to a loss). Gems submitted 684 → 646 (−38 ± 39), deaths to champions 9.7 → 11.3 (+1.5 ± 1.1), gems captured
−59 ± 36. All within noise: v26 is no better than v25 against the band (sim: 47/80 vs B318; real cambc 43/80 vs
the v25 build). Against v22 (b1) both are ahead: 15-35 → 17-33, gems +68 ± 52.

## Batch 4: 25 Oct 2026, ~01:58 UTC, 50 games, 13-37 (v27 = A61188, Arena A; b1's exact plan)

Paired with b3 (v26): 4 flips to a win, 8 to a loss. Gems −13 ± 46, gems lost on death +15 ± 12. This is the
lowest record of the four batches, though not significant alone. The losses concentrate on early bankers (GLM5.3
3-2 → 0-5), which matches the sim: v27 is weaker than B792 against stress/rushbank (50 vs 59 of 80).
