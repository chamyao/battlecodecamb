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

## Fuel ensemble (same genomes, sim h2h at fuel x0.96 / 0.98 / 1.0 / 1.02 / 1.04)

| genome | real | 0.96 | 0.98 | 1.0 | 1.02 | 1.04 | mean |
|---|---|---|---|---|---|---|---|
| A103740 | 61 | 69 | 68 | 70 | 64 | 68 | 67.8 |
| A103823 | 69 | 72 | 64 | 83 | 64 | 75 | 71.6 |
| A103646-v33port | 72 | 72 | 70 | 74 | 71 | 66 | 70.6 |
| A103649-v33port | 70 | 70 | 70 | 74 | 67 | 65 | 69.2 |
| A103646-v33port-kf | 63 | 69 | 70 | 73 | 69 | 67 | 69.6 |
| v33port-heal | 57 | 73 | 66 | 66 | 61 | 71 | 67.4 |
| v33port-h4 | 57 | 73 | 65 | 65 | 59 | 70 | 66.4 |
| A103823-w1 (vs v39a) | 66 | 73 | 64 | 83 | 64 | 75 | 71.8 |
| A103930-w1 (vs v39a) | 63 | 71 | 69 | 78 | 63 | 73 | 70.8 |

A 2% fuel change moves one genome's h2h by up to 19 games (A103823: 83 at 1.0, 64 at 0.98 and 1.02): the 1x sample
is one draw from chaotic games, and the gate picked the genomes whose 1x draw was high (winner's curse). Ensemble
mean - real: mean +5.3 (1x: +9.8). Every genome here is within noise of even with the live bot in the sim.
gatekeeper-43: h2h = ensemble mean (--fuel-ensemble), bar 80.
