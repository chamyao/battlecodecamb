Sim (engine-2.0.0 runtime, genome/search e824a66) vs real (cambc 4.0.0, genome lead's gate4) head to head, /140,
genomes from genome/v0 genome/candidates (real numbers from its README):

| genome | vs | sim | real | sim - real |
|---|---|---|---|---|
| A103740 | v38 | 70 | 61 | +9 |
| A103823 | v38 | 83 | 69 | +14 |
| A103646-v33port | v38 | 74 | 72 | +2 |
| A103649-v33port | v38 | 74 | 70 | +4 |
| A103646-v33port-kf | v38 | 73 | 63 | +10 |
| v33port-heal | v38 | 66 | 57 | +9 |
| v33port-h4 | v38 | 65 | 57 | +8 |
| A103823-w1 | v39a | 83 | 66 | +17 |
| A103930-w1 | v39a | 78 | 63 | +15 |

Mean +9.8, median +9, sd 4.9, all 9 positive. Least squares: real = 64.2 + 0.56 (sim - 74), r = 0.67.
The sample is gate-selected (high sim h2h), so part of the offset is selection (winner's curse); for a gate that is
the offset that matters. Sim mirror v38 vs v38 = 70/140 (deterministic). Pass bar raised 76 -> 86 (gatekeeper-42).
