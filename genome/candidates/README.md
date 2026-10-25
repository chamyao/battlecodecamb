# Ladder candidates (genome line)

| genome | source | sim gate (vs live bot, 800 games) | real cambc vs live bot | status |
| --- | --- | --- | --- | --- |
| B318.genome (sha256 00e1711a5b5778c9...) | Arena B (arenaB-1, 20:00 UTC snapshot) | 0.647 at genome/v0 2356e26; anchors all up (+0.8..+10.3); 0.613 vs commit-mono | 53/80 vs interpreted v23 (style-gconv1), 0 crashes, built at genome/v0 (this commit); 110 first turns at the 200k cap, 647 capped normal turns (v23: 0), reported only | uploading Oct 24 ~20:30 UTC (Cham) |

Build: `genome/bot/sync.sh genome/candidates/B318.genome <bot dir>` at the commit that added the row.

## B318 vs the actual live bot (ladder version 24 = v22, tune-v20-L1c, ZIP sha256 d86fbda6)

v23 had been reverted at ~16:50 UTC, so the gate was re-run against the real live bot before the upload:
- Real cambc 3.0.5 --release vs the live ZIP (deploy/v0 ee85727 dist/deploy-v21b.zip), 40 maps x 2 sides: 46/80, 0 errors;
  B318 110 first turns at the 200k cap, 645 capped normal turns (live: 0).
- Sim at genome/v0 2013533, vs policies/candidates/tune-v20-L1c.policy: 0.603 (seed 95001) and 0.575 (95002), 0.589 over 800.
  Anchors over 400 (seed 95010), B318 / live: style-gconv1 0.667 / 0.542; v7 0.927 / 0.925; tune-v20-L1 0.585 / 0.502;
  rall2-ca4-lean-g 0.608 / 0.618 (-1.0); opp-tune5-metadraft 0.873 / 0.882 (-0.9). No drop > 3 points: passes.

## B318 is ladder version 25 (submitted Oct 24 20:40 UTC by intel; bundle sha256 548bb21d...)

Re-gate on the fuel runtime (genome/v0 77da39c: cheaper turn 1, reserve()), vs the v22 ZIP in real cambc 3.0.5 --release,
40 maps x 2 sides: 46/80, 0 crashes, the same as the 2013533 build, so no re-upload.
Note: with --bot-seeds (as deployed) a genome match does not depend on --seed: each pair has exactly 80 distinct games.
Deploy-faithful sim, B318 vs tune-v20-L1c: 38/80 (db3f945), 43/80 (77da39c). Earlier "800-game" gates at bot seeds
are these 80 games repeated; gates without bot seeds play the policy with random seeds, not as deployed.

## B792 (Arena B, arena run 13 lineage; candidate for ladder version 26)

genome/candidates/B792.genome, sha256 fa178e513757224a... (from remote/genome gatekeeper-api/candidates/run13-B792.genome).
Built on genome/v0 212a505 (fuel runtime + simspeed + deploy/v0 7ea42c7 interp).
- Sim, arena engine 212a505, bot seeds, 80 distinct games: 47/80 vs B318 (live v25). Anchors, B792 vs B318's own /80:
  tune-v20-L1c 52/45, style-gconv1 50/51, v7 78/76, tune-v20-L1 49/47, rall2 55/52, metadraft 72/69 (worst -1). Fuel x10: 44/80.
- Real cambc 3.0.5 --release vs the v25 build (genome/v0 2013533 B318), 40 maps x 2 sides: 43/80, 0 crashes either side.

## A61188 (Arena A, arenaA-6; candidate for the next ladder version, "upload first, validate later")

genome/candidates/A61188.genome, sha256 9abfbc94153db0ba... (from remote/genome arenaA-6/arena/genomes/A61188.genome).
Cham, Oct 25 ~01:50 UTC: upload first for variety on the real ladder, validate afterwards. Built on genome/v0 f23aaa0.
- Smoke test, real cambc 3.0.5 --release vs B792 (v26): 3/3 wins (00lanes, 01big-world, 00ambush), 0 crashes.
- Sim at f23aaa0, bot seeds, 80 distinct games vs B792: 49/80 (A61206 47, A61205 43).
- Arena A panel (648bafd, Arena A lead): 867/1040 over 13 opponents; vs B318 50/80, tune-v20-L1c 57/80, style-gconv1 60/80.
- Still to run after upload: anchor-drop check and the full real-cambc 80 vs B792.
