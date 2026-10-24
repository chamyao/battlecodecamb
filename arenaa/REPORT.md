# Arena A: running report (Arena A lead)

Newest first. Scripts in arenaa/; data on remote/genome.

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
