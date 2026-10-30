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

## 200 births (top 3 by mu at birth 202, A11106 already checked)

| genome | sha256 | arena mu at pick (games) | real vs v39 | crashes | result |
| --- | --- | --- | --- | --- | --- |
| A11172 | 9e9d64a7422d9f80... | 28.37 (344) | 73/140 | 0 | fail |
| A11159 | a4ed9139d971bc34... | 27.99 (328) | 76/140 | 0 | PASS (at bar) |
| A11150 | 7b46dd9559a72a08... | 27.96 (456) | 71/140 | 0 | fail |

A11106 (78 at the 100 check) was second by mu (28.08, 1048 games). Real scores of arena tops cluster at 71-78,
i.e. v39a +- noise; nothing yet clears the bar by a margin.

## 300 births (top 3 by mu at birth 299)

| genome | sha256 | arena mu at pick (games) | real vs v39 | crashes | result |
| --- | --- | --- | --- | --- | --- |
| A11297 | f80702b1513da018... | 29.35 (88) | 74/140 | 0 | fail |
| A11261 | 10199f2cb514975a... | 29.35 (504) | 74/140 | 0 | fail |
| A11296 | 40bc2cedd6aea978... | 29.07 (72) | 73/140 | 0 | fail |

## 400 births (top 3 by mu at birth 400)

| genome | sha256 | arena mu at pick (games) | real vs v39 | crashes | result |
| --- | --- | --- | --- | --- | --- |
| A11393 | b749078fd1012bec... | 29.17 (128) | 77/140 | 0 | PASS |
| A11368 | cde3a51093cdd652... | 28.82 (592) | 72/140 | 0 | fail |
| A11358 | 698000c8b9c04812... | 28.76 (712) | 71/140 | 0 | fail |

## 500 births (top 3 by mu at birth 507)

| genome | sha256 | arena mu at pick (games) | real vs v39 | crashes | result |
| --- | --- | --- | --- | --- | --- |
| A11453 | e7a3145adf73f62a... | 28.60 (1080) | 72/140 | 0 | fail |
| A11501 | fb1b19cd2bbc3c70... | 28.46 (96) | 76/140 | 0 | PASS (at bar) |
| A11476 | 361c3c1bc3a8a25b... | 28.24 (872) | 77/140 | 0 | PASS |

## 600 births vs v39a (last check against the old reference)

| genome | sha256 | arena mu at pick (games) | real vs v39a | crashes |
| --- | --- | --- | --- | --- |
| A11584 | fcab5c3306d23873... | 28.74 (440) | 78/140 | 0 |
| A11594 | 55fa6b28b2824ff0... | 28.11 (136) | 80/140 | 0 |
| A11599 | 068e7c98f8713cfc... | 28.11 (80) | 79/140 | 0 |

## Restart at 618 births (09:23 UTC): gate reference is now the live v40

Leads' re-gates vs live v40 (real cambc, 0 crashes): A11106 69, A11393 71, A11261 71, A11476 70, A11501 75 (76 vs v41);
vs v41: A11106 71, A11101 73, A11159 73. So no v39a pass holds vs v40.
From here a pass needs >= 76/140 vs v40 (genome/v0 8e6dfb46c v39a-x6-83, sha 823f1ca3) AND >= 76 vs v41
(v40m, sha 8e8c265a), 0 crashes. Both opponent bots are built on this checkout's runtime (dd28e2f3).
Restart: genome/search 60a2da208 cherry-picked (tuner skips pick/top), rule picks restored in A11391/A11497, anchors
v40 (weight 4), v41 (2), v28-emblem, B318 added (calibrating 200 games), v40 ingested as a seed, max births 1200.

600-birth trio re-gated vs v40 / v41: A11594 70 / 73, A11599 73 / 74, A11584 69 / 71 (0 crashes). All fail.

## 700 births (top 3 by mu at birth ~703), vs v40 / v41

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A11663 | c63d0c9b77e2c3a4... | 28.35 (536) | 73/140 | 72/140 | 0 | fail |
| A11696 | 380b8b4b431b90ed... | 28.16 (160) | 74/140 | 72/140 | 0 | fail |
| A11691 | 73c216b628e704ec... | 28.00 (248) | 68/140 | 68/140 | 0 | fail |

Arena anchors after calibration: v40 26.94, v41 27.02, v38 25.20, v33 25.00, v28-emblem 23.45, B318 22.81. The v40
seed (A11619) died at 26.1. Sim rates the tops ~+1.4 mu over v40; real says they are about even or below.

## 800 births (top 3 by mu at birth ~808), vs v40 / v41

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A11791 | 0859ce55158cc1d5... | 29.29 (296) | 73/140 | 74/140 | 0 | fail |
| A11807 | 5ea058fb703ef7c2... | 28.13 (96) | 61/140 | 67/140 | 0 | fail |
| A11806 | d2641d3aec87cc5b... | 27.84 (80) | 71/140 | 66/140 | 0 | fail |

v40's v2 (contest edit, healthiest-fighter-first) is now spreading in the population, through update-link replies and
v40-graft cross replies (tools/xv40.py). A11791 carries it.

## 900 births (top 3 by mu at birth ~904), vs v40 / v41

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A11893 | 3cddc03d3d9c7b24... | 29.07 (136) | 70/140 | 67/140 | 0 | fail |
| A11876 | ed5f792f015ef0bc... | 28.09 (440) | 69/140 | 71/140 | 0 | fail |
| A11774 | a66b6b335b49abf2... | 28.05 (1872) | 76/140 | 69/140 | 0 | fail (76 vs v40 only) |

## 1000 births (top 3 by mu at birth 1004), vs v40 / v41

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A111001 | c92dea629146afae... | 28.19 (104) | 78/140 | 66/140 | 0 | fail (v40 only) |
| A11976 | 7a7531247d3ffc6c... | 27.94 (440) | 78/140 | 70/140 | 0 | fail (v40 only) |
| A111000 | d54770a37db25995... | 27.83 (56) | 77/140 | 71/140 | 0 | fail (v40 only) |

First batch where all three clear 76 vs v40 (v40-weighted selection since the restart; earlier batches 61-74 vs v40),
but v41 (v40m) scores 66-71 vs the same genomes. Since v40 and v41 differ only in fuel (m8), the v40/v41 gap per genome
(8-12 games) is the noise of one 140-game sample.

## 1100 births (top 3 by mu at birth ~1102), vs v40 / v41

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A111088 | eaf7e43f95878285... | 27.89 (384) | 66/140 | 58/140 | 0 | fail |
| A111026 | 681a49b0404bf824... | 27.82 (1152) | 69/140 | 71/140 | 0 | fail |
| A111099 | ca4e952f05a21bbf... | 27.51 (112) | 67/140 | 73/140 | 0 | fail |

The 1000-birth 77-78 vs v40 did not repeat; the arena's tops stay in the 58-78 band against the live bots.

## 1200 births (top 3 by mu at birth 1206), vs v40 / v41 (deaths = total deaths of the candidate over 140 games)

| genome | sha256 | arena mu at pick (games) | vs v40 | vs v41 | crashes | result |
| --- | --- | --- | --- | --- | --- | --- |
| A111203 | cf341f32bb0913ad... | 27.99 (168) | 62/140 | 64/140 | 0 | fail |
| A111175 | 689b5f2cad4e70fa... | 27.85 (536) | 62/140 | 62/140 (deaths 1748) | 0 | fail |
| A111195 | 18501c0924946d1b... | 27.85 (216) | 73/140 (deaths 1638) | 68/140 (deaths 1612) | 0 | fail |

## Boss-battle stall (01boss-battle solo vs idle, sim)

A11976: both sides stall at round 2000 with 681/724 gems, 23-28 deaths (v40: A 1000 gems at round 1294). Of 27
single-gene swaps of v40's version into A11976, only a9 (shop_value) fixes both sides (1000 gems at rounds 1375-1622);
a11 (no prospector) fixes 3 of 4 games. Cause: my "below 60% health buy a jungle health shard first" a9 edit, together
with prospector-first a11, swaps the wanted item while shop_pending still blocks every other option, so a hurt
champion parks on spawn. Fixes: candidates/A11976-a9.genome, A111001-a9.genome (= parent + v40's a9), ingested in
leg 3 and real-gated below.

| genome | sha256 | vs v40 (deaths) | vs v41 (deaths) | crashes |
| --- | --- | --- | --- | --- |
| A11976-a9 | 8fb2a7dd674765c0... | 74/140 (1766) | 64/140 (1837) | 0 |
| A111001-a9 | a729c43420109a65... | 74/140 (1765) | 64/140 (1814) | 0 |

On 01boss-battle team B vs v40, A11976 had 0 gems (lost); A11976-a9 won with 1003 gems. A11976's draft is Vendetta,
Vesper Vale, Tavi, Ren, Varg (my d1 edit), not v40's Ryth/Ren.

## 1300 births (leg 3, top 3 by mu at birth ~1300): wins / total deaths (camps included), 140 games each

| genome | sha256 | mu (games) | vs v40 | vs x6-61 | vs x8-140 |
| --- | --- | --- | --- | --- | --- |
| v40 (baseline) | 823f1ca37244526a... | 26.94 | (lead: deaths 1728) | 66 / 1746 | 59 / 1938 |
| A111286 | 5f4d86ddf758f43d... | 27.68 (248) | 63 / 1633 | 67 / 1612 | 69 / 1601 |
| A111169 | ee7a8bef5a1b4a90... | 27.33 (1664) | 69 / 2243 | 71 / 2208 | 69 / 2231 |
| A111227 | b14c3db9efee4bf9... | 27.20 (936) | 64 / 1622 | 64 / 1624 | 70 / 1602 |

None reaches 72 vs v40. A111286 and A111227 die less than v40 vs the stress anchors (and beat v40's record vs
x8-140: 69-70 vs 59), but lose to v40 itself.
