# arenaA-11 real-engine checks (cambc 4.0.0, engine 2.0.0; 70 maps x 2 sides vs live v39)

Bots built with genome/bot/sync.sh at genome/v0 dd28e2f3 (this checkout's genome/, sim/, bot/), run with
genome/bot/gate4.sh. The v39 opponent is genome/candidates/v39a.genome (sha 22ec24cf...) built the same way (dd28e2f3
runtime, not the live bundle's 35bcf691a runtime). Bar: >= 76/140, 0 crashes. Genomes in candidates/bNNN/.

## 100 births (checked at birth ~120; top 3 by mu at birth 117)

| genome | sha256 | arena mu at pick (games) | real vs v39 | crashes | result |
| --- | --- | --- | --- | --- | --- |
| A1182 | e37ad3287f7c9355... | 28.60 (440) | 74/140 | 0 | fail |
| A11106 | 99fa6598c6601355... | 28.58 (184) | 78/140 | 0 | PASS |
| A11101 | 36e0777d1c299953... | 28.51 (288) | 76/140 | 0 | PASS (at bar) |

Anchors at that point: v38 25.20 (frozen after calibration), v33 25.00 (fixed); v39a seed died at 25.72.
A11106 differs from v39a in 9 genes (a11 next_shard, a9 shop_value, a7, a12, c0 rule, c1 rule_goal (reads RULE),
r12, r14, r17); its next_shard is prospector-strength first (Arena B measured that alone at 76 and 69 vs v39a). Their arena mu fell after the pick (A11106 27.5 at 576 games; A11101 and A1182 culled at 26.9 / 27.6),
so the passes are within the mirror noise band (+-~8/140); a second real run would be needed before upload.
