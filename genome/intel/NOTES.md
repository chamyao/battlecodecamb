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
