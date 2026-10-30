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
- Live as ladder version 36 (2026-10-25T14:56:30Z, bundle sha256 614be6e6...). Validation: intel batch 12, paired vs b10 and b11.
- Batch 12 (intel b12.md, bd7a24b): 31-19 vs b10's 32-18 (4 flipped to wins, 5 to losses), gems -42 +- 34; vs b11 28-22 -> 31-19.
  ahead4 is record-neutral but costs ~40 gems/game in both b11 and b12; cash3 alone added losses on packs, the_farm
  and lanes. Reverted: v33 re-submitted as ladder version 37 (2026-10-25T15:28:27Z, bundle 37e7be1a...).

**Upload bar (2026-10-25, after v34/v36):** a +3-4/80 local real-cambc edge from a constant tweak did not carry to the
band twice. A constant-only tweak now needs real cambc >= 46/80 vs live (0 crashes) for an upload; under that it is
screen-only. Structural edits keep the 43/80 bar.

## A93635-v33port (Arena A-9's A93635 + v33's fixes grafted in; arenaA-10)

genome/candidates/A93635-v33port.genome, sha256 67ea6f01adef2b58... (arenaa/a10-mirror 38f5ab8b,
arenaA-10/candidates/). Structural: ring small-spawn exclusion, farmable monolith rule, heal off-spawn, killshot 165,
hold 117, gem-groups after 6 buys, bossbush.
- Arena A writer, sim (ca5180b, 80 games, bot seeds): 46 vs v33 (unported A93635: 34), 67 vs B318, 67 vs A61188.
- My real cambc vs v33, 40 maps x 2 sides: 47/80, 0 crashes (12 maps 2-0, 23 1-1, 5 0-2: elkring, interlock,
  road-of-riches, fracture, starvation). GO to intel; validation band batch paired vs b10.
- Live as ladder version 38 (2026-10-30T02:06:53Z, bundle sha256 d54619f2...). Validation: intel batch 13, paired vs b10.
- Search gate (gatekeeper-30 rule, ca5180b): sim h2h 46/80 vs v33; anchors 0 blocks (gains vs A61188 66/56, B1873 45/39).
  Solo-farm blocks: total +339 rounds, driven by 01boss-battle +1382 (sim tribute lock) and 00contest +378; without
  boss-battle it is ~1,040 rounds better. Advisory under upload-first; watch contest and boss_battle in b13.
- Batch 13 (intel b13.md, 36a626a): 29-21 vs b10's 32-18, but the ladder engine is now 2.0.0 (pip cambc 4.0.0; b10 and
  earlier were 1.0.3), so the comparison is confounded. Local real gates (cambc 3.0.5) and the sim measure the old
  engine. Engine 2.0.0 adds 30 maps (70 in the pool), 8 item families (tribute, capture, prospector, hunter, skirmish,
  greed, collectors; shard/emblem of strength/focus/health) and camp_group_capture_state. Re-gating v38 vs v33 on
  cambc 4.0.0 (70 maps x 2 sides).
- Real cambc 4.0.0 (engine 2.0.0), 70 maps x 2 sides vs v33: 82/140, 0 crashes, 140/140 results; old 40 maps 47/80,
  30 new maps 35/60; 18 games reach round 2000. v38 is kept.

## arenaA-10 ports, gated on cambc 4.0.0 vs v38 (70 maps x 2 sides; bar 76/140, 0 crashes)

- A103646-v33port-kf (sha 38e8e2ff...): 63/140, 0 crashes. Fails.
- v33port-heal (sha 8fa74295...): 57/140, 0 crashes. Fails.
- v33port-h4 (sha 59a70f5e...): 57/140, 0 crashes. Fails.
- A103646-v33port (sha f74c7b9b...): 72/140, 0 crashes. Fails (bar 76).
- A103649-v33port (sha 8985a0bb...): 70/140, 0 crashes. Fails.
  None of the five arenaA-10 ports beats v38 on engine 2.0.0; the old-engine sim ranking (54/52/51 vs v33) did not
  carry over.

## Engine-2 probes on v38 (Arena B lead, cambc 4.0.0, 70 maps x 2 sides vs v38; genome/arenab ENGINE2.md)

- Shop order: Monster first 76, Jungle first 74, Monster for Treasure 72, no Treasure 68, Treasure third 66, no Jungle
  59. v38's Treasure -> Jungle -> Durability -> Bruiser holds.
- Draft: Marcella for Ren 71, HoR for Ren 69, Issac for VV 65, VV last 65, Marcella+HoR for Tavi+Ren 45, top-team core 28.
  v38's draft holds; Tavi's remote shop carries our banking logic.
- New item families: unbuyable until the runtime has kNumItems 84 (bot/src/cbs/core.h is 42); every probe 2/140.
  Fuel is doing "M0.5: bot constants" (items 42-83, 2.0.0 passives and champion stats) on genome/fuel.

## Search gate passes (engine-1.0.3 sim) re-checked on cambc 4.0.0 vs v38

- A103740 (arenaA-10, blob 3fde74c2; sim pass h2h 46/80, anchors clean): 61/140, 0 crashes. Fails.
- A103823 (sim 47/80, hunter-blocked): 69/140, 0 crashes. Fails.

## v38 on engine 2.0.0: batch 14 and the 00quarry freeze

- Batch 14 (intel b14.md, 17874bd): 24-26. Old-map part paired with b13: 19-11 vs 18-12 (1 flip). New maps: 5-15,
  with gems 638 vs 820 and deaths to champions 12.2 vs 8.2. New maps are 43% of the pool and the main weakness.
- Bug: v38 as team A on 00quarry freezes (0 gems, 60 gold; no actions from round 63). Confirmed in my gate4 log; v33
  wins that map. With the Arena A lead to fix. 02the-pack is 0-0 for every bot (gold tiebreak), not a regression.

## Engine-2 runtime on genome/v0 (merge 6fb46951 of genome/fuel f952d598)

- Sim exact vs cambc 4.0.0 (seed 70/70 maps), new item passives, capture_state/capture_timer prims; kNumItems 84.
- v38 rebuilt on it (same genome, new constants) vs the live v38 build: 69/140, 0 crashes; 00quarry-A still frozen.
  The constants alone are neutral, so no upload.

## v39a (v38 + quarry bush fix; Arena A lead, genome/arenaa 1fad7357e)

genome/candidates/v39a.genome, sha256 22ec24cf7b33d238... One gene: w1 unseen_camps subtracts near(here(), 1) instead
of near(here(), 0), so a camp spawn hidden in a bush (00quarry (6,10)) gets probed instead of treated as occupied forever.
- My gate4, built on the live bot's runtime (genome/v0 35bcf691a) vs live v38: 72/140 = mirror 70 + both 00quarry games;
  0 crashes. Arena A lead: vs v33 84/140 (v38 82), only 00quarry differs.
- Built on the engine-2 runtime (671ac45b) vs live v38: 71/140 (the runtime change reshuffles chaotic games).
- Uploaded as a pure bugfix (exception to the 76 bar: every other game is unchanged), built on 35bcf691a's runtime.
- Arena B solo-cluster bisection (stampede, starvation, gold-rush, boss-battle): only v33's v2 and m11 help all four.
  v38 + v33 v2 (sha 437b3b49): 77/140 vs v38, 79 vs v33 (v38 itself 82), solo 79,348 vs 83,068. Within mirror noise,
  not uploaded. (Arena B's earlier old/new splits counted the ten new 00-maps as old; totals were right.)
- v39a live as ladder version 39 (submitted 2026-10-30T04:11:26Z, bundle sha256 97492ba3...). Validation: band_v2
  (intel b99c234), old maps paired with b13, new maps with b14.

## New-item probes on v39a (Arena B lead, runtime 671ac45b, cambc 4.0.0, /140 vs v39a)

- Str emblem first: Prospector 76, Hunter 66, Capture 62, Skirmish 61, Tribute 51. In place of Jungle: all <= 65.
- v39a-prospector-first (sha ca9c2a42...): my gate4 vs the live v39 build is 69/140 (old 35/80, new 34/60), 0 crashes.
  Fails (a shop-order change, bar 81). The new-map gain (+3-4) is consistent but is paid back on the old maps.

## Search gatekeeper-41 (engine-2 sim) near-misses, real-checked vs live v39

- All regate40 and A-10 genomes fail the sim solo check on 00quarry (no w1 fix). With v39a's w1 fix grafted:
  - A103823-w1 (sha 35af880b): sim h2h 83/140, real 66/140, 0 crashes.
  - A103930-w1 (sha 478dd015): sim h2h 78/140, real 63/140, 0 crashes.
  The 2.0.0 sim head-to-head overrates these A-10 genomes by ~15/140 against v39a.
- Batch 15 (intel b15.md, bb35d7d), 60 games: v39 31-29 vs v38 30-30 on the same games. Old maps 18-12 vs 19-11 (the
  one flip is vs JOHN_BANEGA_DON, which changed its bot); b14 new maps 7-13 vs 5-15; 10 extra new maps 6-4 = 6-4.
  The fix also unfroze 02harvest (L -> W 1027-481) and 00quarry (0 -> 865 gems). Nothing regressed; v39 kept.
  b15 is the band baseline from now on.
- Sim fixes merged (fuel 4fee8e27 extra x1.04, then 6c5b096e start-up refit + group_tiles priced; genome/v0 10d24fea):
  A103823-w1 sim 83 -> 73 -> 67 (real 68). Gatekeeper-44's only clean near-miss, A103746-w1 (sha cec021bf, sim
  ensemble 74): real 70/140 vs live v39, 0 crashes. Fails.

## exploit-6 structural edits on v39a (Arena B lead, queue writer, runtime 671ac45b)

- x6-83 (sha 823f1ca37244526a): contest a gem group an enemy is farming, with the healthiest fighter first; hold on
  contested captures. My gate4 vs live v39: 79/140 (old 46/80, new 33/60), 0 crashes. Arena B hold-outs: 80 vs v38,
  75 vs v33 (v39a on this runtime: 71 / 78). GO as v40, built on genome/v0 HEAD runtime (engine-2 tables).
- x6-61 (sha 513f4ef13f29c7b7): every ally on a contested capture holds. My gate4: 77/140 (old 43, new 34), 0 crashes.
  Passes too; held back in favour of x6-83.
- x6-83 live as ladder version 40 (submitted 2026-10-30T06:08:08Z, bundle sha256 7317ef88..., built with cambc 4.0.0
  on the engine-2 runtime). Validation: b16 = band_v2 paired with b15. Revert target v39 (bundle 97492ba3...).
- Batch 16 (intel b16.md): v40 31-29, same as b15's v39 on the same 60 games (6 flips each way). Old maps 16-14 vs
  18-12; b14 new maps 9-11 vs 7-13 (gems +93); saved new maps 6-4 = 6-4. Neutral on the ladder despite 79/140 locally;
  kept (no revert).

## v40m (v40 + cheap mono_groups; Arena A lead, genome/arenaa 0695713f3)

genome/candidates/v40m.genome, sha256 8e8c265af954d456... One gene: m8 mono_groups is built from type_spawns(MONOLITH)
groups only (same set, so fuel only). Turn-1 median max 178.7k -> 162.2k; turn-1 cap maps 14 -> 4.
- Arena A lead, real vs v40: 79/140. My gate4 vs v40 (both built at genome/v0 HEAD): 79/140 (old 49/80, new 30/60),
  0 crashes. GO, queued after b16 (v40's band) finishes, so the two batches stay clean.
- v40m live as ladder version 41 (submitted 2026-10-30T06:33:54Z, bundle sha256 7cd1e540...). Validation: b17 paired
  with b16. Revert target v40 (7317ef88...).

## arenaA-11 (engine-2 sim, writer session_01H75at7s2GPNPWtwopowYqq), 100-birth check

- A11106 (sha 99fa6598): writer's real vs v39a 78/140; my gate4 vs live v41 71/140, 0 crashes. Fails.
- A11101 (sha 36e0777d): writer's real vs v39a 76/140; my gate4 vs live v41 73/140, 0 crashes. Fails.
- A11159 (200-birth check, sha a4ed9139): writer's real vs v39a 76/140; my gate4 vs live v41 73/140, 0 crashes. Fails.

## exploit-7 (Arena B lead, vs v40)

- x7-125 (sha 4afcd1b6): v40 + hold through threat with 3 allies, focus fire, no monoliths with an enemy within 6,
  later cash-out (0.4 + gems/60, cap 0.7), stop piling on held captures. Arena B real: 77 vs v40, 80 vs v38, 76 vs v33,
  79 vs x6-61.
- x7-125m = x7-125 + v41's cheap mono_groups (sha 1dbbde1f): my gate4 vs live v41 70/140 (old 37, new 33), 0 crashes.
  Fails (mirror level).
- Retracted by the Arena B lead: its v38/v33 hold-outs used reference bots on older runtimes. With v38 rebuilt on 671ac45b, x7-125 is 68 vs v38 (v40: 84); the later cash-out overfits v40. Hold-outs must use the candidate's runtime.
- Batch 17 (intel b17.md): v41 28-32 vs b16's v40 31-29 on the same 60 games; gems -38 +- 18; 2 flips to a win, 5
  to a loss (old maps 14-16, b14 new maps 8-12). Against v39's b15: flat. Reverted to v40 (bundle 7317ef88...), since
  the ladder band measures real opponents and the local 79/140 self-play edge did not transfer (as with x6-83 in b16).
- Reverted: v40 re-submitted as ladder version 42 (2026-10-30T07:36:04Z, same bundle 7317ef88...). b16 stays the band baseline.
- A11393 (400-birth check, sha b749078f): writer's real vs v39a 77/140; my gate4 vs live v40 71/140, 0 crashes. Fails.
- 500-birth check: A11476 (sha 361c3c1b; 77 vs v39a) is 70/140 vs live v40; A11501 (sha fb1b19cd; 76 vs v39a) is 75/140 vs v40. 0 crashes. Both fail.

## exploit-8 (Arena B lead, multi-opponent fitness, vs v40)

- x8-140 (sha e3217087cf823457): v40 + break enemy captures before the timer ends, hit the champion over camps in a
  fight, lock the altar nearest an enemy gem carrier. Arena B (all on 671ac45b): 81 vs v40, 80 vs v38 (v40: 84),
  72 vs v33 (v40: 65); kills/deaths 10.0/6.9 vs the mirror's 8.75/8.75.
- My gate4 vs live v40: 81/140 (old 48, new 33), 0 crashes. GO as v43; band paired with b16.
- x8-140 live as ladder version 43 (submitted 2026-10-30T09:57:53Z, bundle sha256 ed994fd9...). Intel re-ran v40's band first (b18base, same hour) to control for opponent updates; v43's band is b18, paired with b18base.
- Bug: v43 (x8-140) stalls in solo vs the genome idle bot on 00quarry side A (1699 rounds; v40 861, v39a 891), the same in sim and real. It's a genome trait from an x8 edit; the Arena B lead is bisecting. (A starter-based idle drafts differently and hides it.)
- v43-fix (sha 6f21c5c82d7d7b2c, genome/arenab ad002963f): Zb's champion-over-camp rule ignores enemies on their own
  spawn (and near-dead enemies without gems). Quarry A solo 1699 -> 861; 70-map solo total 159,965 -> 159,048.
  My gate4 vs live v43: 71/140, 0 crashes (bugfix level). GO after v43's band (b18) is in.
- Batch 18 (intel b18.md): v43 30-30 vs v40's same-hour re-run (b18base) 33-27; gems -18 +- 26; flips 4 up / 7 down.
  Reverted to v40; the queued v43-fix upload is cancelled. Pattern: gate4 edges of 79-84/140 (v40, v41, v43) have
  not moved the band, so the ladder band decides and gate4 is only a pre-filter.
- v43-fix3 (sha 6760603a, genome/arenab 7bb80059e): v43-fix + m11 contest help only with a real off-spawn contester; fixes the boss-battle B, famine B and expanse A stalls; 75/140 vs v43; stalactites A 429 -> 2000. On file only, since the v43 line was dropped after b18.
- Reverted: v40 re-submitted as ladder version 44 (2026-10-30T10:32:02Z, bundle 7317ef88...). Band baseline for the next candidate: b18base (v40, 33-27).

## Ladder screen policy (2026-10-30, from intel's SCREEN.md)

Quota is 50 groups per rolling hour, so ladder testing is cheap: ~15-20 min of live time per candidate. screen_v1 =
6 groups / 30 games (17 of 22 historic swing games + 8 close ones; it reproduced the verdicts for v39, v40, v41, v43).
- Pre-filter: real gate4 vs live >= 72/140, 0 crashes, no new solo stall vs the genome idle bot.
- Screen: upload, run screen_v1 paired with the live bot's screen; revert at once if it's clearly down.
- Promote: if it's up on flips and gems, run the full 60-game band; keep it only if the band agrees.

## arenaA-11 tops for the ladder screen (Arena A lead; real gate4 vs v40 / v41)

A11501 75/76 (fb1b19cd), A11696 74/72 (380b8b4b), A11663 73/72 (c63d0c9b), A11599 73/74 (068e7c98).
Solo vs genome idle, cambc 4.0.0, 70 maps x 2 (genome/bot/solo4.sh), total rounds: v40 158,785; A11501 154,576;
A11696 153,283; A11663 156,109; A11599 153,786. Stalls (>300 rounds slower than v40): all four on 01boss-battle B
except A11501; A11501 on 02stalactites A+B and 02gift-wrapping B; A11663 on 02stalactites B.
Screen order: A11696, A11599 (one stall each), then v43-fix3, A11501, x6-61.
- Arena B pre-filter (vs v40, solo vs genome idle): x7-125 77 (boss-battle A+B stall), x7-149 76, x8-36 75, x8-36f 71. x7-125 is added at the end of the screen queue. Note: 01boss-battle B stalls are common across lineages (v40 1498 is the outlier).
- A11791 (sha 0859ce55, carries v40's v2): writer's gate4 73 vs v40 / 74 vs v41; solo total 154,628, one stall (boss-battle A). Screen queue #3.

## Ladder screens (screen_v1, 30 games, paired with v40's same games; intel batches/SCREENS.md)

| # | candidate | ladder version | screen | v40 same games | flips (to W / to L) | gems | verdict |
|---|---|---|---|---|---|---|---|
| s1 | A11501 | v45 | 10-20 | 13-17 | 2 / 5 | +2.5 +- 35.5 | down, not promoted |
- v40-join3 (Arena B fight cohesion, sha 538a1b4cee533829): rescue an ally below half health within 6 of the foe; 72/140 vs v40; solo stalls on boss-battle A and stalactites A (both known fragile). Screen queue last, to let the ladder decide.
| s2 | A11696 | v46 | 12-18 | 13-17 | 7 / 8 | -32.7 +- 52.2 | neutral, not promoted |
| s3 | A11599 | v47 | 11-19 | 13-17 | 4 / 6 | -55.3 +- 52.6 | down, not promoted |
| s4 | A11791 | v48 | 9-21 | 13-17 | 4 / 8 | -54.2 +- 47.7 | clearly down |
| s5 | v43-fix3 | v49 | 10-20 | 13-17 | 3 / 6 | -12.9 +- 36.1 | not promoted (baseline drift check pending) |
| s6 | x6-61 | v50 | 13-17 | 13-17 | 3 / 3 | +24.5 +- 26.4 | level, not promoted |
| s7 | x7-125 | v51 | 7-23 | 13-17 | 2 / 8 | -48.5 +- 36.4 | clearly down; reverted to v40 (v52) |
| s8 | v40 control | v52 | 13-17 | 13-17 | 3 / 3 | +10 +- 22 | drift control: noise floor about +-3 flips |
| s9 | A11976 | v53 | 10-20 | 13-17 (s8) | 3 / 6 | -65.7 +- 42.1 | down: deaths fixed (+0.6) but captures -7.6 |
| s10 | v40-join3 | v54 | 8-22 | 13-17 (s8) | 1 / 6 | -74 +- 38 | clearly down (captures -5.1); v40 live again as v55 |
| s11 | d-out2b | v56 | 12-18 | 10-20 (s11c) | 4 / 2 | +1.1 +- 28.2 | up on flips, gems level; deaths -0.8, captures level: promoted to band b19 |
- A11774 (sha a66b6b33, older A-11 lineage): 76 vs v40 / 69 vs v41; solo total 157,114, stalls on stalactites A and B. Screen queue last.
- All four A-lineage screens are below v40 with +1.7 to +3.0 deaths to champions per game; A11774 dropped from the queue.
- A11976 (sha 7a753124, A-11 b1000 after the survival-first course): my gate4 vs v40 78/140, 0 crashes, deaths 1551 vs v40's 1728; vs x6-61 76, vs x8-140 75 (Arena A lead). Screen queue: right after the v40 control.
- Screens finding (intel SCREENS.md): every candidate below the noise has +1.2 to +3.1 deaths to champions per game
  vs real opponents (control +0.7). Fight-seeking edits (exploit-7/8, the A lineage) lose champions on the ladder;
  gate4 and solo checks can't see it. v40-join3 dropped. Next: survival-first candidates (A11976).
- s9: survival-first removes the excess deaths but farms less (captures -7.6, gems captured -54). v40 sits between the two failure modes; the A lineage is dropped from the screen queue.
- Arena A stat-fitness check (arenaa/REPORT.md, data/fitcheck): over the 9 screened genomes, no local metric vs
  v40/x6-61/x8-140 in the 2.0.0 sim ranks the ladder screens (Spearman: wins -0.31, captures +0.05, deaths -0.29).
  Our anchors don't behave like ladder teams; every genome dies 8.0-8.8 times a game against them. No A-12. Until we
  have ladder-like local opponents (e.g. policies distilled from ladder replays), the ladder screen is the only
  reliable fitness. Also: A11976 drafts Varg instead of Ryth (d1), a plausible cause of its capture deficit.
- Coordinator: analysis/sprint1 Fish-clone study (Oct 24): Fish champions die 6% of the time after falling below half HP, ours 88%. Low-HP retreat is the Arena B lead's next directed edit on v40.
- d-out2b (Arena B, sha b072d8bc): v40 + dx1 retreat to spawn when outnumbered by 2+ live enemy champions within 6. Arena B: 72/140, deaths 1080 vs 1139, captures level, no new solo stall. My gate4 vs v40: 72/140, 0 crashes, deaths 1585 vs 1683. To the ladder screen (s11).
- Control s11c (v40, 16:20Z): 10-20 vs s8's 13-17; flips 2 up / 5 down, gems -55, deaths +1.2. Opponents strengthened over ~3 h with no change on our side, comparable to some earlier 'down' verdicts (A11501, v43-fix3 at 10-20). Rule: a fresh control at the start of each screen session.
- d2-tout (Arena B, sha 404637c9): d-out2b + Tavi retreats when outnumbered at all within 6. My gate4 vs v40 76/140, 0 crashes, deaths 1476 vs 1682 (-12%). Solo: stalactites A stall (resource exhaustion, 10 gems short). Screen queue after b19/b19base, against the same-hour v40 control.
- Batch 19: d-out2b 31-29 vs same-hour v40 (b19base) 30-30; flips 6 up / 5 down; gems -7 +- 25; deaths -0.8 +- 0.6;
  gems lost on death -14.5 +- 6.9; captures -1.1 +- 1.5. Adopted: the first bot since v40 with ladder evidence of
  not being worse (fewer deaths, farming level). d2-tout is screening (s12) vs both; the better of the two goes live.
- Arena B follow-ups that failed vs v40: d2-th (Tavi half-HP disengage) 62, d3-ven 65, d3-vv 60. The strict
  outnumbered trigger only pays for Tavi.
