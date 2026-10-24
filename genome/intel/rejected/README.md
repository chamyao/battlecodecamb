# Rejected directed children (kept for the record; not for the arena)

Sim, side A, 400 games, all maps (seeds 92001 vs the original, 92002 vs commit, 92003 vs stress/lockall).

| child | gap | vs original | vs commit (parent) | vs lockall | why rejected |
|---|---|---|---|---|---|
| cashout | 2 gems lost on death | 0.443 | 0.312 | 0.575 (commit 0.725) | lost_to_champs 50 → 40, but retreats/recalls cost more than they save. Variants: recall only 0.450, recall at 30+ 0.450, retreat at 40+ 0.425 vs commit. The sim under-counts our deaths ~3x, so this lever needs real-game evidence first. |
| lockfree | 6 altar locks | 0.540 | 0.500 | 0.662 (commit 0.725) | neutral; commit's goal hysteresis already fixes most of the lock collapse (lockall on rushbait + broken-curve: commit 0.75). |
