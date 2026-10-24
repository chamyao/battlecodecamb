# Arena A: running report (Arena A lead)

Newest first. Scripts in arenaa/; data on remote/genome.

## 2026-10-24 23:55 UTC

- promptexp-1 tail children on the 13-opponent panel (1,040 games): 11 of 13 keep their gain. Best: A1 T1
  c45 782 vs parent 746 (+36; anchors +30), above arenaA-3's best A723 (780); A0 c87 +26, c64 +23, c28 +20.
  So the tail is real, both arms produce it; A1's single best is the largest single-mutation gain seen.
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
