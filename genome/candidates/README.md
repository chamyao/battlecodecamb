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
- Real cambc 3.0.5 --release vs v29, 40 maps x 2 sides: 52/80, 0 crashes either side. Upload after batch 6 validates v29.

## A81582-ringgg (A81582 + Arena B's ring fix and weak-gem-groups-first; supersedes A81582 as the next upload)

genome/candidates/A81582-ringgg.genome, sha256 aa5e6aa743675e10... (genome/arenab 5e3aeef2 cand/A81582-ringgg.genome).
Needs the group gold/gems bot fix (genome/v0 fd778fc or later).
- Arena B lead, real cambc (built at fd778fc): 49/80 vs v29, 0 crashes; capped normal turns 473 vs 307 (watch).
  Solo vs a do-nothing bot, rounds to 1000 over 10 maps: 16,393 (A81582) -> 14,725.
- Sim: 45/80 vs v29, 39/80 vs A81582; solo total vs idle 100,601 -> 96,568.
- Smoke, real vs v29: 01elk-arena W 1014-84, 01broken-curve L 730-1001, 00great-wall W 1016-641; 0 crashes.
- WITHDRAWN (Arena B lead, 06:14 UTC): in real cambc it loses 01pilgrimage, 01gold-rush and 01broken-curve 0-2 each vs v29;
  gem-first starves gold against a real opponent.

## A81582-ringheal (A81582 + two solo-farming bug fixes, no gem-groups)

genome/candidates/A81582-ringheal.genome, sha256 9620bbfbce8afff4... (genome/arenab 7ac4808c cand/A81582-ringheal.genome).
(1) Altar rings exclude small-camp spawn tiles, so bank walks never target a tile a living camp blocks; (2) r2 ignores
enemies on their own spawn, so hurt carriers next to an enemy spawn can heal. Reads neither group_gems nor group_gold.
- Arena B lead, real cambc at fd778fc: 55/80 vs v29, 0 crashes (plain A81582: 50/80 on the same builds); capped turns 450 vs 301.
- Sim: 46/80 vs v29, 40/80 vs A81582; solo vs idle: games short of 1000 halved (10 -> 5).
- My smoke, real vs v29 (side A, hard maps): 3 losses. My full real cambc vs v29, 40 maps x 2 sides: 57/80, 0 crashes. Next upload.
- Live as ladder version 30 (2026-10-25T06:39:47Z, bundle sha256 90450da2...). Batch 7 vs b6 (v29): 21-29 vs 20-30, neutral;
  monolith deaths 2.28 vs 0.58 per game (lineage lacks the monolith fix); ranked 10-5 at 15 games.

## A81582-ringheal-mono (v30 + v28's monolith fix via graft.py mono; candidate for after v30)

genome/candidates/A81582-ringheal-mono.genome, sha256 9a566695b7b06184... (genome/arenab 5019e0cc).
The A-8/A-9 lineage never got intel's farmable-camps fix; solo on great-wall v30 loses 38-45 champions per game, v29 11-12.
- Arena B lead, real cambc: 45/80 vs v30 (ringheal), 57/80 vs v29, 0 crashes. Solo vs idle, all 80 games: deaths 356 (v30 522),
  rounds 98,956 (v30 99,212). Sim: 40/80 vs v30, 50/80 vs v29.
- My real cambc vs v30 (ringheal), 40 maps x 2 sides: 45/80, 0 crashes; wins both sides on 00great-wall and 01shortcut. v31 candidate.

## A81582-rh-mono-all (v30 + mono + intel's rhm contest rule + gg6 gem-first after 6 buys; supersedes rh-mono for v31)

genome/candidates/A81582-rh-mono-all.genome, sha256 f54246b181c6caa1... (genome/arenab 843629e0). Reads group_gems:
needs a build at or after genome/v0 fd778fc.
- Arena B lead, real cambc: 51/80 vs v30, 49/80 vs rh-mono, 62/80 vs v29, 0 crashes. Solo vs idle 97,417 rounds, 379 deaths
  (v30 99,212 / 522). Sim 42/80 vs v30.
- My real cambc vs v30 (ringheal), 40 maps x 2 sides: 51/80, 0 crashes. v31 pick.
- Live as ladder version 31 (2026-10-25T07:16:11Z, bundle sha256 e4932580...). Batch 8 vs b7 (v30): 27-23 vs 21-29, 6 flips to a win,
  0 to a loss (p ~0.03), gems +39 +- 20; great_wall monolith deaths 35 -> 1, shortcut 12 -> 0.

## B1873 (Arena B relay leg 6; v32 candidate)

genome/candidates/B1873.genome, sha256 20a329ce544e9707... (genome/arenab 42275ee7). B-line with the monolith fix,
ring/heal and gg6; new: a kill-shot fight outranks the pass-through bank (rule 165 + r_killshot).
- Arena B lead, real cambc: 47/80 vs v31, 49/80 vs v30, 56/80 vs v29, 0 crashes. Solo vs idle 95,846 rounds, 362 deaths
  (v31 97,417 / 379). Sim 37/80 vs v31.
- My real cambc vs v31, 40 maps x 2 sides: 47/80, 0 crashes. Carries the rmab boss-battle exemption (relay auto-ingest).
- Live as ladder version 32 (2026-10-25T07:50:23Z, bundle sha256 52a3fb56...). Batch 9 vs b8 (v31): 31-19 vs 27-23 (6 up, 2 down),
  gems +87 +- 39; stuck champion-rounds 31.5 -> 4.0; elk_arena vs NotSoLonely W 936-720 (was L 18-1008); boss_battle still 0-1.

## B1873-bossbush (v32 + no bush move bonus on the boss-battle layout; v33)

genome/candidates/B1873-bossbush.genome, sha256 7ff741cbb0826666... (genome/arenab a52d986d). One edit: the a8 bush move
bonus is skipped when some altar-ring tile is a monolith-group spawn (ALTAR_MONO, set once in v2).
- Arena B lead, real cambc vs v32: 40/80 = 01boss-battle 2-0 + 1-1 on each other map (identical play), 0 crashes.
- My check, real vs v32: 01boss-battle 2-0; 00lanes and 01big-world mirror v32 exactly (same rounds, side wins).
- Live as ladder version 33 (2026-10-25T08:36:16Z, bundle sha256 37e7be1a...). Validation: intel batch 10, paired vs b9.

## v33-cash3-ahead4 (tune-B on v33; v34 candidate)

genome/candidates/v33-cash3-ahead4.genome, sha256 6ca9e9e63bced4a1... (genome/arenab d0351648; genome/tuneb 579c317).
Two constants: a5 ahead_on d <= 5 -> 4; r5 cash-out g < 5 -> 3.
- tune-B and Arena B lead, real cambc: 44 vs v33, 44 vs v32, 46 vs v31, 59 vs farmer, 65 vs rushbank (v33's row: 40/40/44/50/66).
  Capped turns 364-381 (v33 411-450). Solo vs idle 95,088 rounds, 352 deaths.
- My real cambc vs v33, 40 maps x 2 sides: 44/80, 0 crashes. v34 pick.
- Live as ladder version 34 (2026-10-25T14:18:21Z, bundle sha256 9842ac5c...). Validation: intel batch 11, paired vs b10.
- Batch 11 (intel b11.md, 4639d9f): 28-22 vs b10's 32-18 on the same 50 matchups, 3 flipped to wins and 7 to losses
  (sign test p ~0.34). Gems -41, gems captured -56, gems lost on death +44. The earlier cash-out puts carriers on the
  road more often and they lose bags. Nothing favours v34, so it is reverted: v33 bundle 37e7be1a... re-uploaded.
- Reverted: v33 re-submitted as ladder version 35 (2026-10-25T14:54:24Z, same bundle sha256 37e7be1a...).

## v33-ahead4 (v33 + a5 ahead_on d <= 5 -> 4 only; v34 without cash3)

genome/candidates/v33-ahead4.genome, sha256 7bead1581516d949... (genome/arenab). Splits v34's two edits.
- tune-B real cambc: 43 vs v33, 44 vs v32, 46 vs v31, 58 vs farmer, 68 vs rushbank. Solo identical to v33.
- My real cambc vs v33, 40 maps x 2 sides: 44/80, 0 crashes. GO to intel as v36; validation b12 paired vs b10 and b11.
