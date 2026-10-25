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
- Live as ladder version 27 (2026-10-25T01:54:54Z, bundle sha256 8f44d04a...).
- Post-upload: real cambc 3.0.5 --release vs B792 (v26), 40 maps x 2 sides: 47/80, 0 crashes either side. Anchor-drop check not yet run.

## a61188-mono (Arena B directed edit of A61188; candidate for v28, upload first)

genome/candidates/a61188-mono.genome, sha256 54e1275ad91bee73... (genome/intel 35046ccf directed/a61188-mono.genome).
A61188 + a farmable() gene: camp attacks only on farmable camps (no hits on monoliths), aimed at v27's monolith losses
(5 of its 18 ranked losses). Built on genome/v0 ca5180b.
- Arena B lead, real cambc: 42/80 vs A61188, 49/80 vs B792, 49/80 vs the v25 build, 0 crashes. Sim: all 15 anchors +0..+4.
- Smoke, real cambc vs A61188, both sides: 00great-wall 2-0 (deaths 16/19 vs 31/34), 01shortcut 1-1 (11/22 vs 27/26),
  00lanes identical games. 0 crashes.
- Live as ladder version 28 (2026-10-25T03:43:47Z, bundle sha256 8a921761...).
- Validation, intel batch 5 (the same 50 band matchups as batch 4): 18-32 vs v27's 13-37; 5 flips to a win, 0 to a loss
  (p ~0.03). Monolith deaths 1.86 -> 0.58 per game; gems submitted +39 +- 23 per game.

## v28-emblem (Arena B directed edit of v28; candidate for v29, upload first)

genome/candidates/v28-emblem.genome, sha256 781ad53eb6128223... (genome/intel 764a03b7 directed/v28-emblem.genome).
v28 + Treasure shards concentrated on one carrier until its emblem completes (early-gold gap). Built on genome/v0 ca5180b.
- Arena B lead: real cambc 45/80 vs the v28 build, 0 crashes; sim 52/80 vs v28; anchors A61188 +16, rushbank +7,
  hunter-carry +7, rall2 +3, metadraft/farmer/lockall -4 each.
- Smoke, real cambc vs v28: 00lanes, 01big-world, 01gold-rush 3/3 wins (close), 0 crashes.
- Live as ladder version 29 (2026-10-25T05:11:34Z, bundle sha256 61743fda...). Validation: intel batch 6, paired vs b5.

## A81582 (Arena A, arenaA-8 session-writer run; candidate)

genome/candidates/A81582.genome, sha256 0b367e241df6... (remote/genome fbf8ced5 gate-v29/A8-A81582.genome).
- Gatekeeper-19 vs v29 (v28-emblem), paired rule: h2h 50/80 (55/80 at fuel x10); no anchor block (closest:
  a61188-mono 44/52, p 0.128; A61188 48/55, p 0.162).
- Real cambc smoke vs v29: 1-3 (won 00lanes; lost 01big-world, 00great-wall, 01boss-battle), 0 crashes.
  Full real 80 vs v29 running; upload only if >= 42/80.
