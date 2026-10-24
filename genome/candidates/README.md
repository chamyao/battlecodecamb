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
