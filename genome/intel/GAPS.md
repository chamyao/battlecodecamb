# GAPS: our live bot's measurable weaknesses in real band games (Arena B evidence)

v1, batch 1 (24 Oct 2026). Data: 50 fresh unranked games of our live submission (the seed v23's draft order;
same record as v23's earlier band run, 15-35 vs 14-36) against 10 teams rated +55..+145 above us (1596),
all 40 maps. ± is one bootstrap SE over games. Raw tables: `batches/b1.md`. Sim numbers: seed genome vs the
compiled original (`python3 -m genome.intel.sim_metrics`, 400 games, all maps, unless noted).

Cost scale: in our losses they finish at 993 while we have 425. Adding X gems to every loss flips 1 game at
+100, 3 at +200, 10 at +300, so single small gains rarely flip a band game. The gaps below that cost 150+ gems
per affected game are the ones that move wins.

Each item is written so a mutation prompt can quote it: `gap | evidence | genes | sim metric`.

## Ranked

1. **Stuck carriers: 2-cycle walking with a bag.**
   - Evidence: a champion steps back and forth between two tiles for 20+ rounds, acting on nothing else.
     It happens in 14 of 50 games: 12 of 35 losses (109 champion-rounds per loss) against 2 of 15 wins.
     61 of 65 spells carry gems (mean bag 31), mostly 3-4 or 8-9 tiles from an altar.
     Games with a spell: win 14%, 447 ± 92 gems submitted; games without: win 36%, 630 ± 61.
     It caused 3 of the 9 games where we submitted under 100 (01broken_curve twice, 00rushbait_v2).
   - Cause (sim traces): the bank walk's goal flips as the carrier moves (rule 12 with itself; 00corners,
     00pilgrimage, 00fragment, 00split, 00quadrants). Or the rule alternates with the tile: bank/camp walk
     12↔20 (01corridors) when the bag threshold flips, and live camp/camp walk 19↔20 (01yellow_brick_road).
   - Genes: `v2` update (GOAL), `c1` rule_goal, `m12` bank_goal / `m13`-`m15` bank_t1-3, `w4` closest,
     `r10` bank_on, `r11` bag_ready, `r18` r_live.
   - Sim metric: `python3 -m genome.intel.sim_stuck GENOME OPP --games 2`, in stuck champion-rounds per game.
     The seed scores 66.7 against real 77, on the same maps (00corners 1216 sim / 1125 real), so the sim
     reproduces this one.
   - Directed child: `directed/commit.genome` (0.0 stuck; +3 points vs the seed).

2. **Gems lost on death.**
   - Evidence: 155 ± 24 gems per game (184 in losses, 88 in wins). 59% ± 6 of our champion deaths happen while
     carrying, at a median of 6 tiles from an altar. We submit 65% ± 4 of what we capture in losses, 92% in wins.
   - Genes: `r11` bag_ready, `r9` r_prefight, `r3`/`r4`/`r5` run, recall and cash out, `s10` threat_eta,
     `s11` altar_eta.
   - Sim metric: `lost_to_champs`; the seed scores 55, about 3x below real (sim opponents kill less).

3. **Capture yield: gold-only and poor groups.**
   - Evidence: our captures pay 10.2 ± 1.1 gems, theirs 15.3 ± 1.2. We make more captures (75 against 55),
     but 31 ± 7 per game pay 0 gems. Low yield (under 70% of theirs) is in 49% ± 8 of losses.
   - Genes: `m11` camp_goal (nearest live spawn), `v2` CAMP_BASE, `s12` group_threat, `r17` r_bankgroup.
   - Sim metric: `per_capture`; the seed scores 10.9.
   - Directed child: `directed/gem-groups.genome` (14.4 per capture, 61 captures, neutral win rate in the sim).
   - A reward-per-turn group choice costs too much fuel if it scans every group each turn: 1,300-2,300
     suspensions per game, measured.

4. **Slow first bank.**
   - Evidence: our first tribute comes at round 230 (median), theirs at 127. By round 500 they have
     submitted 245 against our 153. Slow start (their first tribute 60+ rounds earlier, and they lead at
     r500) is in 29% ± 8 of losses.
   - Genes: `r11` bag_ready (15 / 10 thresholds), `r6` r_pass, `m11` camp_goal.
   - Sim metric: none in `--details` yet. Proxy: tributes per game; the seed makes 40.

5. **Fights lost.**
   - Evidence: we die 10.2 ± 1.4 times per game to champions (11.1 in losses, 8.0 in wins), and fights are in
     46% ± 9 of losses. Being outnumbered at the first hit no longer separates outcomes (death rate 40% vs 39%;
     it did for v21).
   - Genes: `r7` r_fight, `s13` fight_foe, `a3`/`a5` cast-ahead, `s7` in_danger.
   - Sim metric: `deaths_champ`; the seed scores 6.3. The sim under-counts this too.

6. **Enemy altar locks.**
   - Evidence: band opponents placed locks in 23 of 50 games, 3.2 per game in those games, often one on every
     altar. In those games we win 26% and submit 489; in games without locks we win 33% and submit 656.
   - Seed behaviour: it hits a lock once it is adjacent. But a re-lock cancels the tribute channel, and
     `s11` altar_eta / `m13` bank_t1 skip locked altars.
   - Genes: `m13` bank_t1, `s11` altar_eta, `r6` r_pass, `a0` (TRIBUTE at a locked altar = attack the lock).
   - Sim stress opponent: `stress/lockall.genome` (the seed, plus it locks every altar). The seed loses 0/10
     to it on 00rushbait-v2 (168 to 1014 gems).

7. **Monolith wake-ups.**
   - Evidence: we die to monoliths 3.1 ± 1.3 times per game on monolith maps (great_wall 23 in one game,
     boss_battle 11, contest 9, shortcut 4). This batch has it as a loss cause in only 2 of 35 losses. In
     earlier ranked games (v21-v24) it was 19%.
   - Cause (sim): hitting any camp of a monolith's group wakes the monolith. Rule 20's camp attack takes
     `reach_camp()` even when that camp is a monolith.
   - Genes: `s14` reach_camp, `r14` r_camp, `r13` bank_blocked, `a0`.
   - Sim metric: camp deaths on 00great-wall / 01shortcut / 01boss-battle, with `GAME_EVENTS=1` ("by=camp
     monolith"). The seed has 31.6 camp deaths per game on great-wall in the sim.
   - Directed children: `directed/mono-spare.genome`, `directed/mono-pack.genome`.

## Directed children (batch 1)

All compile (`python3 -m genome.build`) and run (`genome_eval`). Win rate is side A over 400 games, all maps.

| child | gap | genes edited (new) | vs original | vs seed | gap metric (seed → child) |
|---|---|---|---|---|---|
| `commit` | 1 stuck | v2, r10, r18 (keeps LAST_RULE, LAST_GOAL, BANKING) | 0.545 | 0.537 | stuck 66.7 → 0.0 per game; 00corners 0.60 → 0.85, rushbait 0.55 → 0.95 (20 games each) |
| `mono-spare` | 7 monolith | s14, r14, r13, a0 (i1) | 0.540 | 0.537 | great-wall camp deaths 31.6 → 20.1, self-play monolith deaths 52 → 6; boss-battle worse (0.45 → 0.35, 20 games) |
| `mono-pack` | 7 monolith | s14, r14, r13, a0 (i2) | 0.542 | 0.500 | as mono-spare, but monolith groups are allowed with both allies within 5 (boss-battle 0.50) |
| `gem-groups` | 3 yield | v2, m11 (i5, keep GEM_BASE) | 0.492 | 0.487 | per capture 10.9 → 14.4, captures 81 → 61 |

Reference: the seed itself scores 0.507 against the original.
