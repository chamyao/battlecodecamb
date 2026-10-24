# Rejected directed children (kept for the record; not for the arena)

Sim, side A, 400 games, all maps (seeds 92001 vs the original, 92002 vs commit, 92003 vs stress/lockall).

| child | gap | vs original | vs commit (parent) | vs lockall | why rejected |
|---|---|---|---|---|---|
| cashout | 2 gems lost on death | 0.443 | 0.312 | 0.575 (commit 0.725) | lost_to_champs 50 → 40, but retreats/recalls cost more than they save. Variants: recall only 0.450, recall at 30+ 0.450, retreat at 40+ 0.425 vs commit. The sim under-counts our deaths ~3x, so this lever needs real-game evidence first. |
| lockfree | 6 altar locks | 0.540 | 0.500 | 0.662 (commit 0.725) | neutral; commit's goal hysteresis already fixes most of the lock collapse (lockall on rushbait + broken-curve: commit 0.75). |

## Rerun against stress/hunter (runtime genome/v0 822dbbe; seeds 94010 vs hunter, 94011 vs the original)

| child | vs hunter | vs original | lost_to_champs vs hunter |
|---|---|---|---|
| commit (parent) | 0.637 | 0.547 | 96.5 |
| cashout (retreat + recall at 20+) | 0.525 | 0.475 | 75.5 |
| cashout, recall only | 0.613 | 0.532 | 93.6 |
| cashout, retreat at 40+ only | 0.650 | 0.500 | 94.0 |

None wins clearly against hunter while losing under 1 point against the original, so all stay rejected.

## yield-rr (gap 3, on commit-mono; runtime genome/v0 822dbbe; seed 95001 vs the original, 95002 vs commit-mono)

The camp group is chosen by reward rate and kept across turns: the current group plus 4 others are re-scored per turn
(round-robin), with a switch at +20%. Result: 0.375 vs the original (commit-mono 0.610) and 0.312 vs commit-mono.
Gems per capture rise to 21.4, but captures fall from 83 to 32 and camp deaths rise from 3.7 to 8.9 per game. Rate
variants (2x and 4x distance weight plus static camp strength) score 0.325 and 0.350 vs commit-mono. A sticky
nearest-gem rate scores 0.400, so the stickiness itself hurts. The stateless nearest-gem-group rule
(directed/gem-groups-cm) wins instead: 0.600.
