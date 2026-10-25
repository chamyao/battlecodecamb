# Arena A: running report (Arena A lead)

Newest first. Scripts in arenaa/; data on remote/genome.

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
