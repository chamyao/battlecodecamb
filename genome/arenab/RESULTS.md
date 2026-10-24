# Arena B lead: real-cambc gate runs (cambc 3.0.5 --release, 40 maps x both sides, vs v23 interpreted)

`genome/arenab/real_gate.sh CAND REF`. First turns have a 200k budget; normal turns 100k.

| date (UTC) | runtime | candidate | wins /80 | first turns at 200k cap | normal turns >= 100k (cand / v23) |
|---|---|---|---|---|---|
| Oct 24 19:50 | genome/v0 46f8c7a | seed v23.genome | 50 | 110 (5 champs x 11 maps x 2) | 831 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | seed v23.genome | 49 | 110 | 497 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | directed/commit-mono (intel b3ac967) | 51 | 110 | 482 / 0 |

Maps where the first turn hits the cap: 00ambush, 00corners, 00expanse, 00lanes, 00road-of-riches,
01big-world, 01boss-battle, 01fracture, 01islands, 01starvation, 01yellow-brick-road (v23's own
first turn is 154-188k on these).
