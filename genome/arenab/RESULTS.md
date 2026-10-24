# Arena B lead: real-cambc gate runs (cambc 3.0.5 --release, 40 maps x both sides, vs v23 interpreted)

`genome/arenab/real_gate.sh CAND REF`. First turns have a 200k budget; normal turns 100k. Bar since ~20:00 Oct 24: wins >= 42/80 and no crashes (fuel numbers reported only). All three runs: 0 crashes.

| date (UTC) | runtime | candidate | wins /80 | first turns at 200k cap | normal turns >= 100k (cand / v23) |
|---|---|---|---|---|---|
| Oct 24 19:50 | genome/v0 46f8c7a | seed v23.genome | 50 | 110 (5 champs x 11 maps x 2) | 831 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | seed v23.genome | 49 | 110 | 497 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | directed/commit-mono (intel b3ac967) | 51 | 110 | 482 / 0 |

Maps where the first turn hits the cap: 00ambush, 00corners, 00expanse, 00lanes, 00road-of-riches,
01big-world, 01boss-battle, 01fracture, 01islands, 01starvation, 01yellow-brick-road (v23's own
first turn is 154-188k on these).
| Oct 24 20:35 | genome/v0 2356e26 | Arena B B318 (20:00 snapshot) | 49 | 110 | 583 / 0 |
| Oct 24 20:40 | genome/v0 2356e26 | Arena B B279 (20:00 snapshot) | 50 | 110 | 652 / 0 |
| Oct 24 20:45 | genome/v0 2356e26 (both builds) | B318 vs commit-mono (not v23) | 45 | — | — |
| Oct 24 20:50 | genome/v0 2356e26 | commit-mono (rebuilt) | 51 | 110 | 482 / 0 |

## Sim gate (a), `python3 -m genome.arenab.sim_gate` at genome/v0 2356e26 (seeds 94001-94013)

| genome | vs style-gconv1 (800) | vs seed | anchors (change vs the original on the same games) | vs commit-mono (400, seed 95001) |
|---|---|---|---|---|
| commit-mono | 0.566 | 0.562 | v7 +1.8, tune-v20-L1 +9.3, rall2 +5.5, metadraft +5.5 | — |
| B279 | 0.649 | 0.525 | +2.5, +10.3, +7.7, +6.8 | 0.562 |
| B318 | 0.647 | 0.637 | +0.8, +10.3, +8.2, +4.8 | 0.613 |
| B263 | 0.641 | 0.588 | +2.5, +12.0, +8.5, +6.5 | 0.512 |

## Runtime genome/fuel 82b5dcb (cheaper first turn, reserve() pass guard), vs v23 interpreted, 3 jobs

| candidate | wins /80 | first turns at 200k cap | normal turns >= 100k (cand / v23) |
|---|---|---|---|
| seed (genome/seed f739709) | 41 | 6 | 226 / 0 |
| B318 | 56 | 9 | 224 / 0 |

## Sim gate (a) vs the actual live bot before v25, tune-v20-L1c (genome/v0 2356e26 runtime, seeds 96001-96013)

| genome | vs tune-v20-L1c (800) | anchors (change vs L1c's own rate) |
|---|---|---|
| B318 (uploaded as v25) | 0.606 | v7 -0.7, tune-v20-L1 +11.5, rall2 +7.3, metadraft -1.7 -> PASS |
| B279 | 0.610 | +0.5, +11.0, +6.0, -0.7 -> PASS |
| B263 | 0.595 | -0.2, +6.8, +5.2, -2.0 -> PASS |
| commit-mono | 0.570 | +1.3, +4.7, +5.5, -1.5 -> PASS |

**Caveat (genome lead, 20:48):** the seeded runs above give the policy bots random seeds; deployed bots play
fixed seeds, so a deploy-faithful pairing has only 80 distinct games. With `--bot-seeds`
(`python3 -m genome.arenab.sim_gate ... --bot-seeds`), B318 vs tune-v20-L1c at 2356e26 is **38/80 (0.475)**:
anchors v7 +1.3, tune-v20-L1 +2.5, rall2 +3.7, metadraft -1.3. The arena gives 38/80 at db3f945 and 43/80 at
77da39c. Real cambc vs the v22 ZIP (old build): 46/80.

## B792 (Arena B run 13, gatekeeper pass) vs the live v25 build

| date (UTC) | build | vs | wins /80 | first turns at 200k cap (cand / ref) | normal turns >= 100k (cand / ref) |
|---|---|---|---|---|---|
| Oct 24 21:25 | B792 at genome/v0 212a505 | v25 = genome/v0 2013533 genome/candidates/B318.genome | 43 | 11 / 110 | 279 / 692 |

Gatekeeper (arena, 212a505, bot seeds): 47/80 vs B318 built at 212a505; anchors L1c +7, gconv1 -1, v7 +2, L1 +2, rall2 +3, metadraft +3.
