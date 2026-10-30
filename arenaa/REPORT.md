# Arena A: running report (Arena A lead)

Newest first. Scripts in arenaa/; data on remote/genome.

## 2026-10-30 06:25 UTC: v40m, a cheap mono_groups: 79/140 vs live v40

- Fuel's turn-1 measurements on the real bot: v39a/v40's first turn is >= 200k on 25/70 maps. The biggest item is
  mono_groups at 38k (a group_tiles scan of every group).
- v40m = v40 (x6-83, genome/v0 05a41d20) with gene m8 building mono_groups from the monolith spawns' groups only
  (`for t in type_spawns(MONOLITH): acc |= group_tiles(spawn_group(t))`). Same set, so no behaviour change;
  arenaa/candidates/v40m.genome.
- Real cambc 4.0.0, both built at 05a41d20, gate4 vs v40: **79/140, 0 crashes**. Turn-1 max median 178.7k -> 162.2k;
  maps with turn 1 capped 14 -> 4 (>= 175k: 40 -> 22); turn-2 caps 3 -> 0 of 350.
- The genome lead confirmed 79/140 (old maps 49, new maps 30). Intel uploads it after v40's b16 band (~06:50).
- Next target, ring (15k): v40r = v40m with m6 safe_altar_ring checking each altar's distances instead of building
  radius-5/6 reach sets (same set). Real gate4 vs v40m: 69/140, 0 crashes. Median turn 1 165k -> 159k, but the maps at
  the cap are unchanged (4). No gain: chaos, since behaviour is the same.
- Per-gene turn-1 profile (GENOME_PROF, real bot): 01big-world ring 34k / update 24k self / mono_groups 17k;
  01yellow-brick-road cast_value 108k over 188 calls (cast options scored on turn 1), ring 22k.
  Still at the 200k cap: 01big-world, adgato-gemcombat5, 01yellow-brick-road; most other maps end at 185-190k
  (the pass guard). Further turn-1 trimming has diminishing returns. The remaining big item is cast scoring on
  yellow-brick-road.

## 2026-10-30 06:03 UTC: arenaA-11 started in a fresh writer session

- session_01H75at7s2GPNPWtwopowYqq, mirror arenaa/a11-mirror. Set up on the genome lead's call: the A-10 session wanted
  Cham's own go, and Cham's standing instructions cover a new session writer.
- Setup:
  - arena code from genome/search; runtime and sim from genome/v0 dd28e2f3;
  - queue writer, no API, no own screening;
  - --births-in-flight 8, --cull legacy, 70 maps, 800 births;
  - anchors v38 + v33;
  - seeds v39a, v38, A-10 candidates and top members, with the w1 quarry fix grafted;
  - _INDEX_PRIMS += buff_turns, ring;
  - top 3 real-gated (cambc 4.0.0) vs live v39 every 100 births, logged to arenaA-11/candidates/REAL.md.
- Running since 06:06 UTC (setup 73d9268 on arenaa/a11-mirror).
  - Seeds: v39a + 21 A-10 genomes with the w1 graft. v38 + graft equals v39a, so v38 is not a separate seed.
  - Anchors: v33 (fixed at 25) and v38 (calibrated over 200 games, then frozen).
  - Sanity check: v39a vs v38 is 72/140 in the sim, the same as on real cambc.

## 2026-10-30 06:10 UTC: first-turn budget variants of v39a (real cambc 4.0.0, built at genome/v0 10d24fea)

Fuel found that v39a's first turn needs 201-206k, while 4.0.0 takes ~22k of the 200k first-turn budget for start-up,
so the real bot is cut off on turn 1. Variants (arenaa/candidates/), gate4 vs v39a (70 maps x 2):

| variant | change | vs v39a | turn-1 max (median of maps) | maps with turn 1 capped | turn-2 caps (of 350) |
| --- | --- | --- | --- | --- | --- |
| v39a | none | | 178.6k | 14/70 | 3 |
| v39b | turn 1 maps only the cheap sets; full map from turn 2 | **74/140**, 0 crashes | 141.7k | 1/70 | 86 |
| v39c | only mono_groups deferred to turn 2; rest recomputed then | 71/140, 0 crashes | 162.5k | 4/70 | 65 |

Read: freeing turn 1 helps (v39b +4 over even). But the deferred map then hits the 100k normal budget on turn 2,
because the cost is the group_tiles builds (~170 fuel per host bit set in the bot), not where they run. The cleaner fix is
a cheaper group_tiles build in the runtime (bitboard ops instead of per-bit host sets), or spreading mono_groups over
turns 2-4. Neither variant meets the 76 bar yet.
- Genome lead's gate setting (vs the live v39 build, v39a at runtime 35bcf691a; v39b built at dd28e2f3): v39b **70/140**,
  0 crashes. A fail: the 74 was chaos. A-11's runtime is genome/v0 dd28e2f3.

## 2026-10-30 05:30 UTC: the 2.0.0 sim's residual bias is fuel pricing; fixed in genome/v0 b9d2fae1

- One-map diff (real replays at arenaa/data/simdiff/): 01elk-arena A103823-w1 vs v39a is 0-1008 real, 900-468 sim.
- Fuel: no rule divergence. The games replay action for action on 6 maps at 1e8 fuel. The sim under-priced heavy turns
  by 2-4k, so heavy genomes hit the 100k cap less in the sim (6.5 vs 9.1 cap hits per game real).
- Fix: every extra() price x1.04 (genome/v0 b9d2fae1, fuel 4fee8e27). A103823-w1 sim 73 (real 68); mean bias +2.2/140.
- A-11, not yet started (waits on Cham's go), is to use b9d2fae1. The old runtime rewarded fuel-heavy genomes.
- 05:50, fuel: round-1 turns were 18-20k under real (an extra pass), fixed on genome/fuel 6c5b096e: start-up refit on
  70 maps, group_tiles priced. A103823-w1 vs v39a sim 67 (real 68); per-game agreement 93/140. A-11 brief moved to
  genome/v0 10d24fea (the merge of 6c5b096e).

## 2026-10-30 05:20 UTC: 2.0.0-sim gate passes don't reproduce on real cambc

- Search (gatekeeper-41, 2.0.0 sim) reports the A-10 genomes with the w1 bush fix grafted: A103823-w1 83/140 and
  A103930-w1 78/140 vs v39.
- Real cambc 4.0.0 (gate4 method, built at genome/v0 6fb46951) gives 68/140 (sha 35af880b) and 67/140 (sha 478dd015)
  vs v39a, 0 crashes; 68 and 66 on the old runtime build.
- A 10-15 game gap. Asked search to diff one map (sim vs cambc). Until it is resolved, uploads need a real gate4 pass.
- Resolved (search, genome/search regate40/BIAS.md): the cause is chaos plus winner's curse, not a setup bug.
  - The shas match.
  - A 2% fuel-multiplier change moves A103823-w1's h2h by up to 19 games (73/64/83/64/75 at 0.96-1.04; mean 71.8 vs
    real 68). Per-game sim-cambc agreement is ~64%.
  - The gatekeeper picked candidates on a lucky 1x draw (+9.8 offset on that draw, +5.3 on the 5-level mean).
  - Gatekeeper-43 now gates on the 5-level mean (bar 80).
  - Lesson for A-11: single-sample h2h selection on chaotic games overfits the draw; average over perturbations.

## 2026-10-30 05:00 UTC: v39a live as ladder v39; A-11 waits on Cham's go

- The genome lead uploaded v39a as ladder v39 (genome/v0 059731b87). Since then, on genome/v0: Arena B's solo bisection
  gives v38+v2 77/140 (not uploaded); the first new-item probe, v39a-prospector-first, is 69/140 vs live v39.
- A-11 has not started. The A-10 session (idle, 632k context) wants Cham's go typed in its own session before a new
  multi-hour run and an arena-code edit (_INDEX_PRIMS). Brief ready: arenaA-11/ on arenaa/a10-mirror.

## 2026-10-30 04:40 UTC: A-10 done; its best sim candidate fails on the real engine

- A-10 finished at 4045 births (old 1.0.3 sim). My switch messages reached it only at 04:29, after the end.
- Its best sim candidate, v33port-spawnedge (sim 57/80 vs v33), on real cambc 4.0.0 gate4: 67/140 vs v38, 68/140 vs v33
  (v38 82, v39a 84), 0 crashes. That confirms again that the old sim's late refinements don't transfer.
- Writer lessons: the v33 graft gives the big jump (+8..+15); later single fixes are about +1 each, on a plateau;
  camp-targeting changes are fragile; the tuner perturbs index arguments of buff_turns and ring (not in _INDEX_PRIMS).
- A-11 is asked to run in the same session, mirrored under arenaA-11/ on arenaa/a10-mirror (its push scope).

## 2026-10-30 04:10 UTC: v38 00quarry freeze fixed (v39a)

- Root cause: a bush blind spot. On 00quarry, camp spawn (6,10) (group 6, with (5,10); mirror (28,10)) is a bush tile.
  Under 2.0.0 vision a bush cannot be seen from outside, so w1 unseen_camps ("camp spawns out of vision: assumed
  occupied") blocked it forever. Nobody stepped on it or attacked it, the group never cleared, and v38's camp walk
  kept its goal on (6,10). Champions parked around it from round ~12 (trace: rule 20, goal (6,10), goal in BLOCK
  via unseen_camps). v33 has the same w1 but its camp_goal wanders elsewhere.
- Fix (one gene, arenaa/candidates/v39a.genome, sha256 22ec24cf...0871): w1 subtracts near(here(), 1) instead of
  near(here(), 0). Per the rules, stepping onto an unseen occupied tile fails and reveals it for the round, so the
  champion probes the bush and attacks the camp the same turn (verified in trace).
- Real engine (cambc 4.0.0, deterministic), gate4: v39a vs v33 84/140 vs v38's 82/140. The only differences are
  00quarry A and B, both now wins (as A 1001-383; v38 had 0 gems). v39a vs v38 72/140, 0 crashes.
- How: per-turn RULE/GOAL/BLOCK trace printed from the generated C++ (genes.cpp), plus a camp/bush dump.
- The genome lead says the 2.0.0 sim is merged (genome/v0 6fb46951, exact vs cambc 4.0.0 on 70/70 maps). Next:
  arenaA-11 on it.
- arenaA-11 requested (04:06) from the A-10 session, which stops A-10 (its old-engine search never got to REAL.md):
  - same queue-writer arena, on 6fb46951, all 70 maps, fresh ratings, 800 births;
  - anchors v38 (live) + v33;
  - seeds v39a, v38, A103646/A103649-v33port and A-10's top 20;
  - no writer screening; mutations aimed at the new items and the champion rebalance;
  - gate4 vs v38 for the top 3 every 100 births (REAL.md).

## 2026-10-30 02:55 UTC: old sim misleads on engine 2.0.0; A-10 switches to real-engine search

- gate4 vs v38 (cambc 4.0.0, 70 maps x 2, bar 76/140), all 0 crashes: A103646-v33port 72, A103649-v33port 70,
  -kf 63, v33port-heal 57, h4 57. None passes. The old-sim ranking inverted: heal was best in the sim and worst for real.
  The search sim gate also had them all at 39-41/80 vs v38.
- Lesson: once the ladder engine changes, the old sim is not just noisy but misleading for fine-tuning. The coarse
  port (v38) carried over; the sim-tuned refinements did not.
- A-10 now: stop the old-sim arena and run a directed search on the real engine (gate4 vs v38, ~2 min per candidate),
  one structural change at a time from v38, logged in arenaA-10/candidates/REAL.md. Candidates >= 76/140 go to the
  genome lead. Intel's 2.0.0 notes: genome/intel/ENGINE2.md.
- 2.0.0 also rebalanced champions (Vesper Vale strength 55 -> 45; Issac and Varg 40 -> 45; Ren stun 0.75 -> 1.1; Tavi cc
  1.4 -> 1.6; Cassi and Willow focus up). Our draft was tuned on the old stats. The sim port to 2.0.0 is ~9-11 h away
  (fuel); until then, gate4 only. A re-tuned draft was suggested to the writer as the first real-engine try.

## 2026-10-30 02:46 UTC: engine change on the ladder

- The ladder now runs engine 2.0.0 (cambc 4.0.0): 30 new maps (70 total), ~48 new item types (tribute, capture,
  prospector, hunter, skirmish, greed, collectors families) and a new camp-capture state. Our sim and A-10 train on the
  old rules and maps. The genome lead is re-running v38 vs v33 on real 4.0.0 (140 games); intel is collecting the rule
  changes. A-10 keeps running for now, but its sim gains may not transfer until the sim is updated.
- v38 holds on the new engine: **82/140 vs v33 on cambc 4.0.0** (old maps 47/80, new 35/60), 0 crashes. New real gate:
  genome/bot/gate4.sh (cambc 4.0.0, 70 maps) vs live, structural bar >= 76/140, 0 crashes. The writer now screens vs v38;
  v33port-heal is queued first for gate4.
- A-10 candidates so far (sim vs v33, old engine): A103646-v33port 51, -kf 52, v33port-heal 54 (writer: plateau at 52-54).

## 2026-10-30 02:12 UTC: A93635-v33port live as ladder v38

- Uploaded as ladder v38 (02:06:53Z); intel band batch b13 at ~02:28Z. Search gate: sim h2h 46/80, anchors clean.
  Solo-farm vs idle is +339 rounds worse in total (01boss-battle +1382, the sim's tribute lock; 00contest +378).
  gatekeeper-31 now follows arenaA-10 vs v38. Next candidate in line: A103646-v33port (51/80 vs v33 in sim).
  The writer now screens against v38.

## 2026-10-30 02:05 UTC: first A-10 candidate

- A93635-v33port = A-9's A93635 with v33's fixes grafted (ring small-spawn exclusion, farmable monolith, heal
  off-spawn, killshot 165, hold 117, gem-groups after 6 buys, bossbush). Writer's sim screen (80 games, ca5180b):
  **46/80 vs v33** (unported 34/80), 67/80 vs B318, 67/80 vs A61188. The same port onto A93498 scored 43/80. Sent to
  the genome lead: **real cambc 47/80 vs v33, 0 crashes** (sha 67ea6f01...): PASS, intel has the GO (band batch paired vs
  b10). Per map: 12 at 2-0, 23 at 1-1, 5 at 0-2 (elkring, interlock, road-of-riches, fracture, starvation). Those maps
  were passed to the writer as the next target, along with screening vs v33port itself.

## 2026-10-30 01:55 UTC: back after the weekly-limit stop; strength run A-10

- What stopped: the account's weekly Claude Code limit was hit on Oct 25 (~16:00 UTC). Every session stopped,
  including the search session. Z-5's continuation never started (z5-mirror still at 477). Z-20a stopped at 361 births
  (last panel 499 at b211). Z-20b finished (481), but its final panel was never scored. No panels or gates ran since.
- Ladder: v33 (B1873-bossbush) is live as ladder v37 after v34/v36 tweaks were reverted. Upload bar: structural
  >= 43/80 vs live, constant-only >= 46/80 (real cambc).
- Cham: train a stronger bot. arenaA-10 (session_01H75at3niTDgEoHAS5fSoXn): resumes A-9's final population (3644)
  with live v33 as an anchor (weight 2). One Opus session writer, 8 in flight, allowed to read our own candidates and
  port their fixes (A-9 lacks v33's ring/heal/mono/bush fixes), and to screen candidates 80 games vs v33 (the upload
  test). Genomes >= 43/80 vs v33 are logged to arenaA-10/candidates. Mirror arenaa/a10-mirror, 3644 -> 4044 births.
  Only one session runs, to save the weekly limit.

## 2026-10-25 15:55 UTC: Z-5 continued by its original writer

- Per Cham: continue Z-5 rather than start fresh. Its writer session (session_01LXULJygQbjZz8b3EXxV3nT) was unarchived
  with its context (~695k tokens), so the same writer and memory carry on from 477 -> 875 births, same flags, mirror
  arenaa/z5-mirror. Rules: its original working method (it reports whether that included its own games), isolation
  from other genomes and runs. The panel is re-attached from m5. Measures how long the best unscreened, continuous-memory
  writer keeps climbing.

## 2026-10-25 15:40 UTC: best Z bots vs the A line (head to head, 80 games, ca5180b)

| opponent | Z462 (18b) | Z400 (18b) | Z407 (19b) |
| --- | --- | --- | --- |
| starter | 76 | 75 | 78 |
| seeds/v23 (A-line seed) | 23 | 26 | 13 |
| A61188 (v27) | 19 | 14 | 7 |
| A81582 (v30 base) | 13 | 16 | 3 |
| A93208 (A-9 best) | 14 | 15 | 10 |
| v33 (live) | 10 | 9 | 6 |

The best Z bots (~480 births from the starter) beat the starter ~95%, but lose to the A line's own seed (v23 wins
54-67/80) and to v33 (Z wins 8-12%; gems ~410 vs ~930 per game). The 648bafd results are within a few games of these.
The Z panel ranks Z407 (516) close to Z462 (610), but against the A line Z407 is weaker on every row.
Z-20b finished (481 births, 6h34; scripted replies from ~b140); its final panel is pending.

## 2026-10-25 15:17 UTC: A-9 stopped (plateau); Z-20 ahead of controls

- A-9 panel m28-m36: 1060, 1047, 1068 | 1061, 1054, 1069, 1059 (screening on from b3240). Flat: 1044-1069 since b2552
  (~1100 births), and leg 5's screening did not move it. RELAY_DONE pushed (c59aae2e); the final population is being
  scored. Best A-9 genome on the panel: A93536 / A93208 (1069 / 1068).
- Z-20 (screened from the start): 20a m2 499 (b211), 20b m3 504 (b323). Both are already above the controls' finals
  (371 / 335) at fewer births. Both sessions are running (not stalled).

## 2026-10-25 15:11 UTC

- Policy (Cham via the genome lead, genome/v0 c168b57a): no more API credits. All Arena A runs with LLM mutation use
  the file queue (--llm-queue) answered by Claude Code session writers; no runs on FUNSEARCH_API_KEY or --budget. All
  current runs (A-9, Z-20) already comply.

## 2026-10-25 13:21 UTC

- Controls done: Z-21a 371, Z-21b 335 (final populations, /880, 1.7 h each). Screened finals: 18b 610, 19a 346,
  19b 513, 19c 479. Z-20a/b still running (203/297 births); 20b m2 478 at b226. Details in SCREEN.md.
- A-9 leg 5 (screening) at 3381.

## 2026-10-25 12:19 UTC

- Births: Z-20a 173, 20b 209 (screened); Z-21a 291, 21b 283 (no-games controls, started 1h later but faster per
  birth); Z-19d 263; A-9 leg 5 at 3274.

## 2026-10-25 12:02 UTC

- A-9 m32 **1068/1200** (A93208, b3211): new high, from leg 4 (before screening started at b3240).
- Z-19 latest: 19a 355 (b393), 19b 516 (b416), 19c 479 (b475), 19d 230 (b209). The cull spread within each rule
  (~160-250) swamps the difference between rules; no cull effect readable.
- Z-20a/b m2 pending; Z-21a/b at 71/57 births.

## 2026-10-25 11:36 UTC: A-9 leg 4 done; leg 5 switches on writer screening

- Leg 4: births 2836 -> 3240; in-arena top about 49.5 (A93205, champ59-A92939). Panel m28 1060, m30 1047: roughly flat.
- Leg 5 (3240 -> 3640) allows writer-side screening with genome_eval (--threads 1, logged to screens.jsonl). This is a
  deliberate protocol change from b3240, on the strongest population we have. A-9 is a strength line, not a controlled
  arm. Readout: the panel slope after b3240 vs before.

## 2026-10-25 11:30 UTC: panel milestones

| run | treatment | m1 | m2 | m3 | m4 |
| --- | --- | --- | --- | --- | --- |
| Z-19a | screened, legacy | 246 (b110) | 330 (b229) | | |
| Z-19b | screened, legacy | 267 (b122) | 409 (b283) | | 516 (b416) |
| Z-19c | screened, min-mu | 341 (b116) | 465 (b282) | 472 (b341) | |
| Z-19d | screened, min-mu | 202 (b100) | queued | | |
| Z-20a | screening explicit, legacy | 365 (b112) | | | |
| Z-20b | screening explicit, legacy | 367 (b110) | | | |
| Z-21a/b | no own games (control) | not yet | | | |

- Z-20's m1 (365/367 at ~110 births) is the highest of any series, and both arms agree. The explicit screening
  instruction from the start seems to help over screening that a writer discovers on its own. All clean on the
  exact-table check.
- A-9 m30 1047 (b3042); m28 was 1060. B-14 m24 1085.

## 2026-10-25 11:17 UTC

- Births: Z-19a 332, 19c 405, 19d 199; Z-20a 127, 20b 128; Z-21a 31, 21b 24; A-9 leg 4 at 3150.

## 2026-10-25 11:05 UTC

- Z-19c also screened throughout (200+ evals, then scripted replies), so Z-19 is all screened runs (still a valid cull
  comparison). New unscreened controls Z-21a/b carry the no-games rule in the starting prompt (SCREEN.md).
- Finding about the setup itself: an Opus session writer with shell access will build its own evaluation loop (A/B
  games, traces, map tools, scripted replies) unless told otherwise from the start. That is most of what separates the
  ~400-600 runs from the ~300 ones.

## 2026-10-25 11:00 UTC

- Z-19b (screened from seq 11 although meant as a control; the no-games message reached it after the run ended):
  m4 **516/880 at b416** (top-3 509). With Z-18b 610 at b477 and Z-18c 384 at b331, all three screened, clean writers
  are above the best unscreened run (Z-5 394). The exact-table check is clean on all Z-19 panel genomes.
- Messages to sessions arrive up to ~1h45m late, so mid-run instructions are unreliable. Rules must be in the
  starting prompt (and enforced by the environment where possible).
- Z-20a/b past 100 births; Z-19a/c/d panels lag (match queue full). B-14 m23 1090/1280.

## 2026-10-25 10:27 UTC: Z-19 m1/m2

- Z-19 (isolated, no screening): m1 19a 246, 19b 267 (legacy); 19c 341, 19d 202 (min-mu). 19b m2 **409 at b283**,
  already above Z-5's 394 at b413. Within-pair spread is large; no cull read yet.
- Caveats on 19b: the no-own-games rule reached the Z-19 writers ~25 min after launch (08:55), so early screening is
  possible; their final reports will say. The fingerprint check runs at the end. If clean, an unscreened isolated
  writer with --births-in-flight 8 is already at Z-5's level by ~280 births.

## 2026-10-25 10:15 UTC

- Births: Z-19a 136, 19b 372, 19c 168, 19d 123; Z-20a 73, 20b 74 (screening runs are slower per birth); A-9 leg 4 at
  2857.

## 2026-10-25 10:00 UTC: A-9 leg 3 done; panel climbing, leg 4

- Leg 3: births 2430 -> 2836 in 80 min; in-arena top A92831 48.8. Panel (/1200): m17 1023, m20 1026, m23 1026, m24 999,
  m25 1044, m26 1045, **m28 1060 (A92792, b2809)**; top-3 mean 1015 -> 1046. A slow climb (+35-40 over 1000
  births, milestone noise +/-15-20), not a plateau.
- Gate: no A-9 passes vs v32/v33 (best 38/80 and 41/80; all solo-farm-blocked because they lack the live bots'
  ring/heal/mono fixes). Several A-9 genomes passed vs v29 earlier (A91634 55/80, A91678 54/80, A91651 51/80),
  moot now.
- Leg 4 (2836 -> 3236): session_01GC8PEa2spih1cDojyzb2gR; same protocol (no own games).
- Z-18c (clean, screened, min-mu, stopped b331): 384. With Z-18b 610 and Z-18d (unscreened) 301, screening points
  the same way twice. Z-20 vs Z-19 decides.

## 2026-10-25 09:13 UTC

- Births: Z-19a 51, 19b 122, 19c 27, 19d 59; Z-20a/b setting up; A-9 leg 3 at 2552.

## 2026-10-25 09:10 UTC: Z-18b is not overfitting

- On new game instances Z462/Z400 score 585/602 (vs 610 fixed); on 6 never-used opponents 180-186/480, vs Z-5's
  Z392 82, Z-18d 45, Z-15 25. The screened writer's gain holds and widens off-panel. Table in SCREEN.md. Z-20a/b
  (2 screened replicates) are running.

## 2026-10-25 09:05 UTC: writer-side screening is the biggest Z signal; Z-20 launched

- Final-population panels (477 births): Z-18b (writer screened children with its own 80-game genome_eval
  head-to-heads) **610/880** (Z462; top-3 mean 607). Z-18d (clean, no screening, min-mu) 301. For reference, Z-5
  394 (b413) and the API arms 190-207. None carry the A-line table.
- One uncontrolled run, but by far the largest Z gap seen. Z-20a/b test it (SCREEN.md): the Z-19 setup plus
  permission to screen with genome_eval (--threads 1, logged), against Z-19a/b as controls.
- Asked the search session to check whether Z462's map-specific tuning overfits the 40 panel maps (the panel holds
  out opponents, not maps).

## 2026-10-25 08:55 UTC

- Correction: only Z-18a copied the A-line table; Z-18b's draft is its own (I had counted VESPER_VALE mentions).
- Z-18b finished (477 births) with its writer screening children by its own 80-game head-to-heads, which is an
  uncontrolled extra. Z-19 writers were told not to run their own games, so the arms stay comparable.
  Writer-side screening is a candidate experiment.
- The 0-0 maps (00road-of-riches, 01shortcut), corrected 09:35: they are NOT a runtime gap. Z470 (Z-18a) farms both
  on 648bafd. It is a goal-selection blind spot of the starter lineage, fixed by "goals that track dead camp spawns".
  The tiebreak in 0-0 games is not side-fixed either, so it adds up to about +/-22/880 of genome-dependent noise to
  Z-vs-Z comparisons. That is small next to the gaps seen (610 vs 394), and genomes that learn these maps gain up
  to 4 games per opponent on merit.
- Z-18b's final population (477 births, writer screened with its own games) will be scored once for reference.

## 2026-10-25 08:40 UTC: A-9 leg 2 done

- Leg 2: births 2026 -> 2430 in 71 min. 303 accepted, 94 twins (24%, down from 44%), 0 invalid. In-arena top
  A92352 47.8 (A92428 48.5 over only 80 games). Panel flat at ~1020 since b1777 (m17 1023, m20 1026,
  m21 1019): in-arena gains are not reaching the held-out panel, so it may be overfitting the pool / anchors.
- Leg 3 (2430 -> 2830): session_01WfP3GtjhyTfUz5i7JyRDDa, told about the plateau and to favour robustness
  (worst maps). If the panel is still flat at the end of leg 3, RELAY_DONE and stop A-9.

## 2026-10-25 08:30 UTC: Z-18 contaminated, cancelled; Z-19 isolated restart

- Z-18a m1 517 at b112 looked too good. Its writer had copied A61188's exact draft table (and shop items) from the
  repo at Z15; 18b is contaminated too (34/40), 18c/18d barely or not. Cancelled; Z-19a-d restart with an
  isolation rule (CULL.md). Z-5 and the relay show no such copy.
- The search session checked all 270 Z panel snapshot genomes (Z-1x, Z-2 to Z-17): the A-line table appears only in
  Z-18a (Z105 / Z107 / Z109). Earlier Z results stand. Z-18 scores are void; Z-19 panels are attached.
- Lesson for the training setup: session writers can read the whole repo, so "from the starter" must be enforced
  (instruction + fingerprint check, ideally a checkout without evolved genomes).
- A-9 panel: m20 1026 (b2026), m21 1019 (b2187). Flat at ~1020 since b1777. v32 (B1873) is now live; nothing
  passes vs it yet (solo-farm block).

## 2026-10-25 08:12 UTC

- A-9 leg 2 at 2243 births. Z-18 births: a 134, b 215 (legacy); c 88, d 253 (min-mu). All four mirrors are pushing.

## 2026-10-25 07:25 UTC: A-9 leg 1 done

- Leg 1: births 1626 -> 2026 in 82 min (A-8: 401 in 2h03), restarted at 1652 with --births-in-flight 8. 263 accepted,
  203 twins (44%), 0 invalid. In-arena top A91942 47.9 (A-8 top was 47.0). Panel m17 1023 (b1777), m18 1019.
  Fix needed: state.json anchor paths point at /root/a8w; leg 1 symlinked it (in the leg template now).
- Leg 2 (2026 -> 2425): session_01TLRWfAgjA9xmPaaofZLJgT.

## 2026-10-25 07:25 UTC: Z-17 result (cull fix)

- Final panel at the stop: legacy 200 (17a), 207 (Z-15); min-mu 190 (17b), 194 (17c). The decision rule is not
  met, so there is no measurable strength effect at ~400 births. The mechanism works: the top-3 members culled drop
  from 33 to 8-12, species grow, and gene-ID crossovers appear (0 -> 9 / 27). Details in CULL.md. Z-18 (session
  writers) continues the test. A-9 stays on legacy.

## 2026-10-25 07:10 UTC: API credits out; Z-17 stopped; Z-18 on sessions

- API credits ran out at 06:50 (account balance). Z-17a/b/c were stopped at 357 / 351 / 415 births; final
  milestones are pending. So far: 17a legacy 112 / 107; 17b min-mu 112 / 141; 17c min-mu 104 / 113 (m1 / m2,
  17c m2 / m3). Mixed.
- A-9 is unaffected (session writer): m17 1023/1200 at b1777, m18 1019 (partial). Already above A-8's 1006.
- Z-18a-d: the cull test on 4 session writers (2 legacy, 2 min-mu), no API spend. See CULL.md.

## 2026-10-25 06:45 UTC

- A-8 final: 1006/1200 (m16, A81604), top-3 999.7. A-8c final 946 (peak 966). Session writer +40-60.
- A-9 leg 1 is at ~1777 births about 40 min after start (A-8 did 401 in 2h03); --births-in-flight 8 roughly
  doubles session throughput. m17 is being scored.
- Z-17 m1 (partial): 17a legacy 106 (b127), 17b min-mu 112 (b109), 17c min-mu 85 (b112); Z-15 had 83 at
  b118. Too early.
- v30 (A81582-ringheal) is live on the ladder. A81615 and A91640 passed vs v29 (50/80) but trail ringheal
  in the sim; they are being re-gated vs v30.

## 2026-10-25 06:20 UTC: relay final; Z-17 queued

- Z-10 relay final (476 births): panel best 85 / 96 / 107 / 145 (Z400, b405). Z-5 (same writer and feedback, one
  continuous session) had 394 at ~b413. Both used the legacy cull, so the cull does not explain the gap.
  What differs is the writer's memory (reset every 50 births vs continuous), so continuous context is
  most of Z-5's edge. Caveat: one run each, and Z-5 has no replicate. This supports long legs for
  session relays (arenaA-9 uses ~400-birth legs).
- Z-17a/b/c queued on EC2 (jobs/genome 64a22ea8), exactly as designed in CULL.md; panels panelZ-17a/b/c.
- A81582 is being uploaded by the genome lead (it passed vs v29 at 50/80; the solo-farm check warned on one
  map, but the total is faster).

## 2026-10-25 06:15 UTC: arenaA-9 overnight

- Strongest A line: arenaA-8 (Opus session writer + feedback, from arenaA-6). Panel 1006/1200 vs A-8c's
  966; A81582 passed the gate vs v29.
- arenaA-9 continues it overnight as a relay of ~400-birth session legs (each writer keeps a long
  context; A-8 did 401 births in 2h03 in one session). State on arenaa/a9-relay, arenaA-9/arena. Same
  flags as A-8 (legacy cull, so it is a clean continuation; switch to min-mu only if Z-17 says so). Leg 1
  (1626 -> 2025): session_011vcVLjPXnSVBsiyD5jtCUG, with --births-in-flight 8 (default 3), so the session
  writer works in batches of up to 8, as Z-15 batching did for the API writer. Panel + gatekeeper on the branch were requested from the
  search session. RELAY_DONE only at the end of the night.

## 2026-10-25 06:12 UTC: A81582 passes the gate

- The genome lead reports that A81582 (arenaA-8, the session-writer run) passed the gate vs v29: 50/80 head to head,
  55/80 at 10x fuel, no anchor blocks. It is the first Arena A genome to pass since v27, and the next upload
  candidate (upload handled by the lead / Arena B).
- The lead also relays that Cham is asleep and wants the work to continue without waiting on approvals,
  within the approved spend. Z-17 proceeds as designed.

## 2026-10-25 06:10 UTC: cull fix, arenaZ-17 launched

- Fix: genome/search e837b50e, `--cull min-mu` (default legacy unchanged) + patches/cull-minmu.patch for
  7e40b6f, with a unit test. Design arenaa/CULL.md.
- Runs (Z-15 setup, batched Opus API): Z-17a legacy salt 1 (control replicate), Z-17b min-mu salt 0, Z-17c
  min-mu salt 1; Z-15 is the salt-0 control. Handed to the search session for EC2.

## 2026-10-25 05:55 UTC

- Haiku dropped as a writer (Cham OK'd stopping unpromising runs). Z-1x stopped at 1444 births, $14.34. Best
  257 (b1206); curve since m6: 228 231 234 256 253 245 257 255. Z-14 (Haiku session) cancelled.
- Shared memory: A genomes use 1 byte (byte 7: lock bought/placed flags, so only one champion buys the
  altar lock); Z genomes use none (0 of the last 60 relay genomes). Vision is not shared, so ally
  coordination is unexplored. That is a candidate seeded experiment after the cull fix.
- Still running: A-8 panel, Z-10 relay panel, Z-15/Z-16 last milestones, gatekeeper-19.

## 2026-10-25 05:50 UTC: A-8 done

- A-8 (session writer + feedback, from arenaA-6) finished: 1626 births (+401) in 2h03, $0. Mirror
  arenaa/a8-mirror 1eac94c. 504 requests: 264 accepted, 215 twins (43%), 0 invalid. In-arena top A81622
  47.0; champion anchors climbed from 44.4 to ~46.8 (arenaA-6 population was 43-44). Panel: 1006 at m15
  vs A-8c's final peak 966; the last milestone follows.
- Training finding from the writer: most twins come from links that cannot change behaviour in the
  fingerprint games (here, at_spawn, lock genes, blocked). Excluding such links from the link draw (as
  PROMPT_EXP's A1 did) would save about 40% of session time. That is a candidate change for a later run.
- The writer also reports that small crosses adding 1-3 proven genes beat crosses stacking every winner.

## 2026-10-25 05:45 UTC: relay done; cull bug found (affects every run)

- Relay Z-10 finished: 476 births, sha b692581. RELAY_DONE pushed (3b33b304), so the panel can finish. In-arena
  top: Z469 / Z471 at 37.85. Panel comparison with Z-5 to follow.
- **Cull bug** (found by leg 10, checked in genome/search arena.py cull(); the same line has been there since
  7e40b6f, so every A and Z run so far is affected):
  `pool = strict or [species with > 1 member] or ok`. With 24 members in about 24 species, the strict pool
  (species with more than min_species = 2 members) is almost always empty. A newborn joins its parent's
  species, making that the only species with 2 members; the newborn has fewer than min_games games, so
  the parent is the only candidate and dies whatever its rating.
  - Relay deaths: 442 of 453 used the relaxed rule. 152 of 453 were the parent of the newest birth in the
    same species. In the second half the median victim had mu 34.7 while the top was about 37; 53 victims
    had mu >= 36 and 14 had mu >= 37 (Z410 37.5, Z427 37.6, Z449, the leaders at the time).
  - Effect: selection is mostly "a child that founds no new species replaces its parent" rather than "the
    worst dies". This may explain the compressed ratings and the plateaus (Z-1x flat at ~250).
  - Not changed: the arena code is fixed per run. Proposal for Cham: a controlled pair on Z with the
    candidate fix (when the strict pool is empty, cull the lowest mu among all ok members; species
    protection only via min_species) vs the current rule, same everything else, with a replicate.

## 2026-10-25 05:35 UTC: Z-15 and Z-16 done

- Z-15 (batched Opus via API) done at 475 births, $17.75. Panel best 176 (b290), 185 (b320), 207 (b405);
  Z-8x had 207 at b402. Same quality per birth, about 2x births per hour, $0.037/birth vs $0.050 (~25%
  cheaper). Verdict: adopt batching for API runs. This corrects my 05:10 note ("slightly worse per birth").
- Z-16 (Opus splits) done at 557 births, $6.58 ($3.58 of it splits). Panel best 117 (b303), 139 (b423), 199
  (b532). It beats Z-11r (Haiku splits: 131 at b622), but the no-split baseline Z-1 had 212 at b500. So
  splitting raised gene counts (median 8 vs 6) without a measurable panel gain. Verdict: not adopted.
- A-8 m15: 1006 (b1528). A-8c final: 966 (m15), 946 (m16). Session writer ahead at every milestone.
- Z-1x: 255 at m13 (b1309), flat since ~b900.
- Gate: new paired rule (h2h vs v29 >= 43/80; an anchor blocks only on a sign test p < 0.1).
  A-8c's near-misses, re-gated: 6 of 11 done, none pass.

## 2026-10-25 05:25 UTC

- Relay Z-10 leg 9 done: births 401 -> 452 in ~18 min, sha 5a5df8f, 49 requests, all validated. Ratings are
  compressed at 36-37: Z449 36.7 (cross with "banking": go to the altar only with 20+ gems, below 50%
  health or late), Z451 36.6. The best-rated member, Z410 (37.47 after 496 games, cast at the most wounded
  champion), died during the leg; leg 10 is asked to find out why the culling removed it. Two replies were
  rewritten after the arena had already consumed them; leg 10's template says to write each reply once.
- Leg 10 (452 -> 475, final) started: session_01QXK7C75sssPH4DsRAq9RMY. RELAY_DONE after it reports.

## 2026-10-25 05:10 UTC: A-8c done; Z-15 / Z-16 m2

- A-8 (session writer) vs A-8c (API writer), panel /1200, best (top-3 mean):

  | milestone | A-8 | A-8c |
  | --- | --- | --- |
  | m13 | 1003 (991.7) at b1324 | 930 (917.3) at b1332 |
  | m14 | 1010 (988.7) at b1401 | 958 (941.3) at b1442 |
  | m15 | running | 966 (948.3) at b1509 |
  | m16 | | 933 (partial) at b1600 |

  A-8c finished at 1626 births (+$3.39). The session writer is ahead by about 45-70 at matched births,
  and A-8c's peak (966) is below A-8's m13. This is one pair; it agrees with Z-5 vs Z-8x.
- Z-15 (batched Opus via API): m2 176 at b290 (Z-8x: 190 at b207, 218 at b318). Slightly worse per birth,
  but 459 births/h against ~180 typical for Z-8x. Batching buys speed, not quality per birth.
- Z-16 (Opus splits): m2 114 at b270 (Z-11r: 83 at b219); inside the API-baseline spread so far.
  Splits at b423: 40 attempted, 12 accepted; all 40 first tries failed the twin check, so every
  accepted split passed on the retry. All 12 split cast_value. Split cost $2.91 of Opus on top of the $3 for
  births. Genes per live genome: median 8 / max 9, against Z-1's 6 / 7 at the same birth count. Splitting
  grows structure; whether that buys strength is not visible yet.
- Z-1x: 257 at m12 (b1206). Flat around 250.
- gatekeeper-16 (v28): no passes from any arenaA run. A-8c's best is 47/80 but drops vs B318, hunter,
  deathball and v7. gatekeeper-17 now gates A-8 (arenaa/a8-mirror) and the Arena B relay.

## 2026-10-25 05:05 UTC

- Relay Z-10 leg 8 done: births 350 -> 401 in ~25 min including setup, sha 22af5eb. The in-arena top
  stayed at about 37 (Z400 37.2, Z377 37.0, Z394 36.9); it did not rise above leg 7's 37.5. New pieces
  in the leaders: "ready goals" (a cleared group within 5 is the goal even when carrying gems), and,
  when hurt with no gems, dropping goal camps near enemy champions. Porting the recall-48 change into
  older lineages gained about +1 to +2 each. Edits gated on rare conditions mostly come back as twins.
- Leg 9 (401 -> 450) started: session_01UUrEjtf9MFE4pGZhEf2uvB. Leg 10 (450 -> 475) is the last; RELAY_DONE
  follows it.

## 2026-10-25 04:50 UTC: panel milestones

The A panel now has 15 opponents (adds B318, B1145 and A61188), so A scores are out of 1200 and are not
comparable with the earlier /1040 numbers.

- A-8 (session writer) vs A-8c (API writer), same start (arenaA-6), best / top-3 mean:

  | run | m13 | m14 |
  | --- | --- | --- |
  | A-8 | 1003 (A81303) / 991.7 at b1324 | queued |
  | A-8c | 930 / 917.3 at b1332 | 958 / 941.3 at b1442 |

  The session writer leads by about 70 at m13. One pair, no replicate yet.
- Z-15 (batched Opus via API): 290 births, $9.30 in about 45 min. That is about 2x Z-8x's births per hour,
  at the same $/birth. m1 at b118: 83 (Z-8x: 130 at the same point).
- Z-16 (Opus-written splits): 270 births, $1.32. m1 at b104: 93 (Z-11r: 83 at b113).
- Z-1x: about 250 since m9 (256 at b923; 245 at b1108). Flat.
- Z-10 relay: 85 / 96 / 107 at b301. Z-5 had 246 at b325, so the relay is far behind. That points to the
  continuous context (or the feedback history it carries) being most of Z-5's edge. The in-arena jump
  in leg 7 (Z350 at 37.5) is not on the panel yet.
- gatekeeper-16 (vs v28): no passes. The closest is A8C1270 at 43/80, but it loses more than 3 wins to
  farmer, exploit-353 and tune-v20-L1.

## 2026-10-25 04:45 UTC

- Relay Z-10 leg 7 done: births 301 -> 350 in ~22 min including setup, sha cc901b0. 43 requests answered,
  0 invalid (the session validated every reply locally). The in-arena top jumped to Z350 at 37.5, Z347 37.2
  and Z349 37.0; the new champion anchor is champ7-Z347 at 36.0. All three leaders inherit one tune
  child, Z343, which drops the below-35% recall score from 90 to 48 (below progress moves), so a hurt
  champion keeps farming. This rating is relative to the arena's own anchors; the panel decides.
- Leg 8 (350 -> 400) started: session_01BX1bFdzg3N4WjVKzkM5et3.

## 2026-10-25 04:25 UTC

- Relay Z-10 leg 6 done: births 252 -> 301 in ~24 min, sha 821678f on arenaa/z10-relay. Mutations
  32 accepted / 3 twins / 1 invalid; llm_cross 10 / 1 / 1; tune 7 / 5 twins / 0. Both invalids came from
  placeholder replies to the re-waited seqs; that gotcha is now in the leg template. In-arena top: champ5
  anchor Z239 at 35.27, then Z262 34.81, Z285 34.69, Z297 34.64. Their shared traits: champion-targeted
  casts scored above the 90 low-health recall, and a "step away from enemy champions when carrying gems"
  MOVE rule.
- Leg 7 (301 -> 350) started: session_01J5wZp78NVLDdB8UzDAm3TT.
- No new panel leaders. Z-5 is still the best loop (394/880) and A61188 the best bot. A-8, A-8c, Z-15 and
  Z-16 have no milestone yet.

## 2026-10-25 04:05 UTC

- Genes per genome in final populations: Haiku runs stay at 6 (Z-1 6-7; Z-1x 6-8 after ~1,000 births;
  Z-11r 6-7). Opus runs grow genes unprompted: Z-8x 10-15 (median 284 lines), Z-5 8-9 (median 167 lines:
  the leanest and the strongest). The stuck gene count was a property of the writer.
- Z-11r (Haiku splits): only 3 of 62 splits passed the behaviour-identical check; final panel best 131
  (b622): the idea was not really tested. Z-16 = Z-11r with Opus-written splits, queued.
- Z-9 (55/30/15 mix) done: 170 only by ~800 births; not adopted.
- Started: A-8 (Opus session from arenaA-6) and A-8c (API control); Z-15 (batched Opus mutations, 8 per
  call), Z-16 (Opus splits). Relay Z-10 at 252 births (leg 6 running).
- API spend in the Arena A ledger: $59.21 (past the $40 reserve; Cham: credits are not the constraint).

## 2026-10-25 03:45 UTC: what drives Z-5's edge (model vs feedback)

- Z-8x (all Opus via API, no feedback) finished: 402 births, $20.08. Panel best 130 (b119), 190 (b207),
  218 (b318), 207 (b393). Z-5 (Opus session + feedback + continuous context): 226 (b261), 246 (b325),
  394 (b413). Haiku baselines: 104-130 at ~400.
- Reading: Opus alone helps early and plateaus near Z-1's final level (~215); the feedback/continuous
  context roughly doubles it by ~400 births. Z-8x is also slow per hour (~90 births/h).
- Running: A-8 (Opus session + feedback from arenaA-6) vs A-8c (API control, EC2), same code 051b4954
  (runtime ca5180b), panels incl. B1145/A61188 rows. Z-10 relay leg 5 (to 250). Z-15 (batched Opus API
  mutations, 8 per call) specified. Strength/ladder work (monolith fix) moved to Arena B (Cham); B may
  train on A's genomes and use Opus. CORRECTION earlier in this file: A61188 beat B1145 48/80, not the reverse.

## 2026-10-25 03:10 UTC: Z series status (best / mean top 3 of 880)

- Z-5 final population: Z392 394, Z430 371, Z477 357, Z452 347, Z458 336 (top-5 mean 361); Z477 h2h:
  55/80 vs Z-1's best Z449, 53/80 vs Z-1x's top Z657 (663 births). ~1.7-1.8x Z-1's final at matched births.
- Z-8/Z-8x (all Opus, API, no feedback): 130/118 (b119), 190/176 (b207); second to Z-5 (226 at b261).
- Z-1x (Z-1 continued): 212/187 (b500), 228/218 (b617), 231/226 (b731): flattening after the b475 jump.
- Z-11r (splits): 83, 83, 107, 121 (b415): baseline range so far.
- Z-9 (55/30/15 mix): 90, 88, 107, 114 (b617): baseline-like. Z-6 (no ladder notes) final 96 (b514):
  lowest baseline-like. Z-4 final 56. Z-10 relay m1 (b102) 85: replicate range so far.
- Relay legs 1-3 done (152 births); per leg ~20-28 min and $3.5-6.3 of Claude Code usage. Leg 4 running.
  Finding from the relay: the draft picks one champion every game, so ability branches for other
  champions never run; many heal/shield/cast edits are twins for that reason.
- New calibrated runtime genome/v0 ca5180b (sim = real on 3 matchups); next series pins genome/search e3ac822a.
  CORRECTION: B1145 (Arena B's #1) vs A61188 (v27): B1145 won 32/80, A61188 won 48/80 (60%), sim and real alike. A61188 is the stronger bot.

## 2026-10-25 02:50 UTC

- Z-5 finished: 477 births in ~2 h (one container restart, resumed). Final in-arena top Z477 41.93, Z458
  41.60, Z392 41.47 (starter 25). Replies: 424 accepted, 65 twins, 3 invalid. Its own lessons from the
  feedback: shard build order (treasure -> durability -> monster -> power; durability first +1.5), recall
  ever later (0.35 -> 0.05), ally beacons on casts and on nearby enemy champions, walk home only below 30%
  with no gems, escape dash. Final panel + head-to-heads vs Z-1/Z-1x requested.
- Z-10 relay: legs 1-2 done (102 births, ~35 min, ~$3.5-4.6 of Claude Code usage per leg); leg 3 running.
  Hand-off gotchas fixed in the leg template: remove the restored queue/DONE; answer re-issued in-flight
  requests; reset to the remote tip before committing.
- A61188 = ladder v27; real cambc vs B792 (v26): 47/80, 0 crashes. Gatekeeper vs v27: 14 gates, none pass
  (A-6 genomes 35-42/80, Arena B 30-38/80).

## 2026-10-25 02:25 UTC: Z series panel table (best / mean top 3 of 880; starter 46)

| run | change | ~b100 | ~b200 | ~b300 | ~b400-450 | ~b500+ |
| --- | --- | --- | --- | --- | --- | --- |
| Z-1 | baseline | 45/40 | 65/58 | 93/76 | 104/83 | 215/196 (475) |
| Z-2 | replicate | 79/70 | 99/92 | 91/86 | 126/111 | 145/136 (537) |
| Z-7 | replicate | 110/105 (155) | 116/107 | 130/122 (442) | | 126/121 (514) |
| Z-3 | distinct games | 69/60 | 72/69 | 101/76 | 96/93 (485) | 125/105 (527) |
| Z-4 | A1 typed prompt | 49/47 | 50/47 | 56/50 | | |
| Z-6 | no ladder notes | 70/58 | 65/63 | 71/65 | 75/73 | |
| Z-8 | all Opus (API) | 130/118 (119) | | | | |
| Z-9 | mix 55/30/15 | 57/46 (133) | 58/52 | | | |
| **Z-5** | **Claude Code session mutator, continuous context + feedback** | | 226/217 (261) | 246/237 (325) | **394/359 (413)** | |

- Z-5 is ~3x the baselines at matched births (394 vs 104-130 at ~410-440). Strongest result in the project.
  Z-8 (all Opus, no feedback, API) is also high early (130 at b119): part of Z-5's edge may be the model.
  Z-8x (Opus to ~475 births) and Z-10 (session-written, memory reset every 50 births) separate model,
  feedback and continuous context.
- Z-6 (ladder notes removed) is below every baseline: the ladder hints help Z.
- Z-4 flat (A1 operator), Z-9 low so far (more crossover), Z-3 within/below the baseline range.
- Costs: Z-5 is ~2.5x slower per birth and the session uses far more Claude Code usage per birth than the API.

## 2026-10-25 01:56 UTC: first Arena A genome on the ladder

- Workflow change (Cham): upload first, validate later (variety on the real ladder).
- A61188 (arenaA-6, panel 867/1040 vs v23 723; 50/80 vs B318, 57/80 vs v22) passed the real-cambc smoke
  test (3/3 vs B792, no crashes) and is live as ladder version 27 (01:54:54Z). Sim vs B792 on f23aaa0:
  A61188 49/80, A61206 47, A61205 43. Post-upload validation (anchors + 80 real games vs B792) running
  (genome lead).

## 2026-10-25 01:50 UTC: evaluation change verdict (final populations)

- Final populations on the 13-opponent panel (1,040 games each; seed v23 723), arenaA-6 (control, old
  evaluation) vs arenaA-5 (distinct games + bot-seeded anchors), both arenaA-3 + $3.53:
  mean 837.0 vs 792.6; held-out (8 opponents, 640) 515.0 vs 487.1; anchors 322.1 vs 305.5; best 867 vs 818.
  The control wins on every measure: the evaluation change is not adopted (n = 1 per arm).
  Best genome so far: arenaA-6's at 867 (+144 over v23, about +14 points). Data: arenaa/data/.
- Z-4 (A1 operator): panel best 49/50/53 at b100/200/300: nearly flat (baselines +50-60 over the same span).
- Approved and specified: arenaZ-1x (Z-1 resumed to ~2,000+ births, the reference curve), arenaZ-11
  (in-place gene splitting, arenaa/SPLIT.md), arenaZ-10 relay (arenaa/RELAY.md; leg 1 running).

## 2026-10-25 01:45 UTC

- Z-5 (Claude Code session mutator with feedback, M2): birth 254/475 at 01:39 (~70 min; ~2.5x slower per
  birth than API runs; one container restart, resumed from checkpoint). In-arena champion ratings (common
  frozen starter anchor at 25) at ~birth 240-250: Z-5 39.0 vs Z-1 36.1, Z-2 35.4, Z-3 34.6, Z-7 33.6,
  Z-4 31.6; Z-5 ahead at every champion so far. Not yet panel-measured: its mirror pushes only the log
  (gitignored arena files); fix re-requested. Z-8 (all Opus, no feedback) separates feedback from model.
- Cloud-session reliability: short shards (~8 min) finish cleanly; long-lived containers get recycled
  (Z-5 once; the search session every 15-20 min). Use sessions for short resumable shards; long arenas on
  EC2/service, or with checkpoint + frequent mirror.
- Queued/started: Z-8 (all Opus, --budget 20), Z-9 (mix 55/30/15) on EC2; arenaA-6 final-population
  panel on 2 cloud workers.

## 2026-10-25 01:35 UTC: first controlled verdicts (one replicate per arm)

- Evaluation change (arenaA-5 distinct games + bot-seeded anchors vs control arenaA-6, same +$3.53 from
  arenaA-3): panel top 3 at m11 A-6 826/812/806 vs A-5 801/761/761; m12 A-6 855/850/846 vs A-5
  802/793/790. The control is ~+50 ahead: the evaluation change looks neutral to harmful. A-5's gain over
  arenaA-3 came from more births, not the change. (n = 1 per arm; A-6's last milestones still playing.)
- A1 operator for every mutation (arenaZ-4) vs replicate baseline arenaZ-2 (880 games): m2 50/47/44 vs
  99/89/89; m3 53/46 vs 91/87/79; Z-2 m4 126/107/99. Z-4 at about half the baseline: worse, consistent
  with promptexp-1. (Z-1 m2 53-65, so Z-4 sits at the bottom of the baseline range.)
- Ended: arenaA-6 ($7.80 total), Z-2 ($3.11), Z-4 ($3.00). Running: Z-3 (480 births), Z-6 (120), Z-7
  (430, service). Z-5 mirror only pushed the log (gitignore); fix requested.
- Next: arenaZ-8 = Z-1 with Opus for every Claude call (API credits are free per Cham); one EC2 slot
  offered to Arena B.

## 2026-10-25 00:55 UTC

- promptexp-1 corrected (T4/T5 prune bug fixed, 14 cells re-generated): A1 valid 78 -> 89, but 7 of the 11
  recovered children are behavioural twins. A1 better 22/120 vs A0 39/120; paired p = 0.998. Verdict unchanged.
- arenaA-5 final: +574 births, +$3.53; panel top 795-802 from birth ~1,100 (arenaA-3 best 780). Control
  arenaA-6 still running.
- Runs: EC2 arenaA-6, Z-2, Z-3, Z-4 (Z-6 queued); arena service Z-7 (service run 23, pinned commit 1ea78e2b,
  3 threads; box has 4 cores); cloud session Z-5 (M2 mutator, session_01LXULJygQbjZz8b3EXxV3nT).
- Runtime: genome/v0 8296d5d is the new calibrated runtime; this series stays on 648bafd; the next
  series starts on 8296d5d with its own baseline + replicate.

## 2026-10-25 00:15 UTC

- arenaA-5 final population (24 genomes, 13-opponent panel, played by 2 cloud worker sessions): mean 793
  (held-out 487/640, anchors 305/400), best A1300 818; arenaA-3 final: mean 756 (held-out 467), best 780.
  Control arenaA-6 (same $3.50, old evaluation) running; verdict when it ends.
- arenaZ-1 final top 3 on its 11-opponent panel: Z449 215, Z474 194, Z468 180 of 880 (m4 104, v1 66,
  starter 46). Z474: fs-1 47/80, fs-p1 14, fs-p2 7, fs-p3 6. Genes 4 -> 6 by birth ~100, then flat;
  code 45 -> ~210 lines, keeps 0 -> 7.
- Cloud sessions as compute: 86-106k games/hour per session (4 cores), ~0.6 Claude-$ of session usage
  per ~8-min shard (mostly cache reads).
- Queued/running: arenaZ-4 (A1 prompt), arenaZ-2 (replicate), arenaZ-3 (distinct games) on EC2;
  arenaZ-5 (Claude Code session mutator with feedback, M2) being built; arenaZ-6 (no ladder notes),
  arenaZ-7 (replicate) wait on the arena service's Claude cap ($60, ~$59 committed): needs Cham.

## 2026-10-25 00:05 UTC: Arena Z becomes the testbed (Cham)

- Why: from the starter, progress is large and fast (46 -> 104/880 in 400 births), and Z trains only on
  itself (starter + its own frozen champions), so the held-out panel measures pure generalisation.
- Cost framing (Cham): Claude API credits come with the subscription; the real cost is EC2 hours. Judge
  setups per CPU-hour / per million games; spend API to save CPU. Run until the Claude credits run out.
- Design: every change = treatment vs control from the starter at equal budget, judged on the 11-opponent
  graded panel; replicates to measure run-to-run variance. Winners are later checked from v23 (Arena A).
- Queued: arenaZ-2 (replicate of Z-1, new RNG stream), arenaZ-3 (Z-1 + distinct games/bot-seeded anchors).
- Cloud-session compute test running: 2 worker sessions panel arenaA-5's final population (shards).

## 2026-10-24 23:55 UTC

- promptexp-1 tail children on the 13-opponent panel (1,040 games): 11 of 13 keep their gain. Best: A1 T1
  c45 782 vs parent 746 (+36; anchors +30), above arenaA-3's best A723 (780); A0 c87 +26, c64 +23, c28 +20.
  CORRECTION (00:00): on the 7 held-out opponents alone (560 games) the big anchor gains mostly vanish:
  c45 (A1, anchors +30) +6, c87 (+24) +2, c82 (+20) -5; 7 of 13 gain, 6 lose; only A0 c64 +16 clearly
  exceeds noise. The tail gains are largely specific to the anchors (also Arena A's training anchors).
- arenaA-5 (distinct games + bot-seeded anchors): panel top 3 per milestone m9 786/779/772, m10 782/774/770,
  m11 801/761/761, m12 (birth 1201) 802/793/790 vs arenaA-3's final 780/774/772 (+~20). No control yet:
  queued arenaA-6 = arenaA-3 resumed with its own evaluation for the same $3.50 (control arm).
- arenaZ-1 final top Z474/Z449/Z468 being panel-scored.

## 2026-10-24 23:50 UTC: Arena Z vs PURE per dollar

- arenaZ-1 done ($3.07, 475 births). Panel (11 graded opponents, 880 games): starter 46 -> best 104 at
  birth 403 (fs-1 6 -> 32/80, v4 8 -> 17, v5 8 -> 17). 262 species; 86 LLM crossovers; Z398 grew from
  4 to 6 genes (cached fields, retreat-to-heal, targeted casting, capture-ready camp goals).
- v1 (PURE's seed) on the same panel: 66/880; v1 beats the starter 66/80; Z398 beats v1 55/80.
- Per dollar, one run each: Arena Z passed v1's panel level at ~birth 300 (~$1.5); from there ~$1.1 more
  reached 69% vs v1. PURE's pilot went v1 -> fs-1 for $0.66, and fs-1 beats v1 76% (61/80). So in the
  matched stretch PURE was ~1.5-2x more efficient. Caveats: PURE's old build under-priced fuel; PURE's
  policies start with hypothesis blocks the genome must invent; n = 1 run each.

## 2026-10-24 23:35 UTC: prompt experiment 1 final

Verdict (pre-registered rule): A1 (minimal typed explicit prompt) does NOT beat A0 (today's prompt).
- "Better" (anchor diff > null p95; the 648bafd null is tight, p95 = 0): A0 39/120, A1 21/120. Paired:
  A1-only 11, A0-only 29, one-sided p = 0.999. At fixed bars: > +5 A0 10 / A1 3; > +10 3 / 2; > +20 1 / 1.
- A1 did make structural changes (58 new genes in 78 valid children vs 0 in A0) but they were more
  harmful on average (mean -23.7 vs -16.4), and 42/120 cells produced no valid child (30 type-check
  rejections after the retry, 12 invalid). By type: T3 helper least harmful (mean -4.4), T4 replace
  worst (-44.8, half rejected).
- Cost $0.263. The best children (A1 T1 +30, A0 +24, +20, +13, A1 T2 +12) are being panel-scored.
- Reading: with Haiku, asking for larger structural edits buys variance mostly on the downside; the
  wider-variance arm does not produce more children above the null. Next arena run keeps today's prompt.

## 2026-10-24 23:30 UTC

- arenaA-5 (arenaA-3 + distinct games/bot-seeded anchors), birth 1061, $6.25 of 7.77. Panel (13 opp,
  1040 games; seed 723; arenaA-3 final top 3: 780/774/772, mean 775): milestone 8 (birth 810) 777/759/756,
  m9 (906) 786/779/772, m10 (1002) 782/774/770. Flat so far: best single genome A890 786 (+63 vs seed,
  highest yet) but top-3 means 764/779/775 vs 775.
- arenaZ-1 (from starter), birth 410, $2.33 of 3. Panel (11 graded opp, 880 games): seed 46; best per
  milestone 45 (b100), 65 (b208), 93 (b306), 104 (b403). Rising steadily (+6.6 points in 400 births).
- promptexp-1 partial (A0 56 scored, A1 31 + 42 generation failures). Null on 648bafd is tight: p95 +2,
  max +5 of 480 (17/40 exactly 0). A0 mean -5.1, max +13; A1 mean -20.5, max +30 (T1). Paired so far:
  A1-only better 5, A0-only 9, p = 0.91. A1 has wider variance both ways. Children > +5 to be
  panel-scored (requested).

## 2026-10-24 22:45 UTC: state when Cham left

Findings
- arenaA-1+3 (737 births, $4.44, default prompt) improved on v23. panel-A3-db2 (648bafd = Arena A's
  runtime, 13 opponents x 80 distinct games, bot seeds): all 24 final genomes beat the seed on the 8
  held-out opponents (+9..+38 of 640, mean +3.7 points); +2.2 points on the 5 anchors.
- Lineage (lineage-A, A659's main line, 30 steps): 14 steps up, 14 down, 2 zero; steps of +-5..30 wins
  of 1040, the size of the null's spread. Gain arrives late (A509, A514) and through one crossover (A137,
  +50). Selection accepts harmful steps as often as helpful ones.
- Ablation: reverting r5 (r_cashout: seed "recall with any gems below 50%" -> "recall with 5+ gems below
  70%") costs -43 (A659, gain +47) and -54 (A711, gain +51): one threshold-level rule change carries
  ~all of the gain. Single-gene losses sum to more than the gain (-87, -180): genes interact.
- Null (40 sigma-0.02 constant tweaks, 480 anchor games): 16 exact zeros, 5 broken (< -50), rest
  -40..+23; p95 = +23. Bench children (creative, missing) never exceed it.
- Prompt bench round 1 (8 task paragraphs, 3 replicate benches): no prompt separates; 5 prodigies
  (>= 48/80 vs parent) in ~900 children, clustered on links, not prompts; none gains vs anchors.
- Typical mutations: one local refinement of one gene (88% of one-link mutations change one gene).
- Determinism: within a runtime every (pair, map, side) game is fixed (80 distinct games per pair).
  4b60b58 differs from db3f945; 648bafd == db3f945 (65/65 cells).

Running
- promptexp-1: A0 (today's prompt) vs A1 (minimal typed explicit prompt, T1-T5), 120 paired cells.
  Generation done ($0.27): A1 78/120 valid, all change both genes or add genes (58 new genes) vs A0 3/119.
  Scoring on the arena service; report ~00:30-01:00.
- arenaZ-1: from the starter genome, starter as only fixed anchor, champions every 50 births, $3;
  panelZ-1 measures it vs 11 graded held-out opponents every 100 births.
- arenaA-5 (requested): arenaA-3 + deterministic-aware evaluation (distinct games, bot-seeded anchors),
  the one change; panel checkpoints every 100 births.

Budget ($40 reserve): see BUDGET.md.
