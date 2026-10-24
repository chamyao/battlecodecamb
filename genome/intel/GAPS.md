# GAPS: our live bot's measurable weaknesses in real band games (Arena B evidence)

## v2: batch 2, B318 live (ladder v25), 24 Oct 2026, 20:47 UTC

Data: 50 unranked games of B318 on batch 1's exact plan (same 10 teams rated +55..+145, maps and sides), so every game pairs with a batch-1
game played by v22 (`paired.py`). The bot is confirmed by banking: 81% of tributes are under 25 gems (batch 1: 14%). Raw tables:
`batches/b2.md`. ± is one bootstrap SE over games.

**v22 → B318, paired (50 games):**
- Record 15-35 → 18-32: 8 flips to a win, 5 to a loss.
- Gems submitted 579 → 684 (+105 ± 49).
- Gems lost on death 155 → 93 (−63 ± 17).
- First tribute at round 230 → 112.
- Tributes 18.5 → 36.2.
- Stuck spells carrying gems 61 → 4.
- Unchanged: deaths to champions (10.2 → 9.7), to camps (4.0 → 3.9) and to monoliths (1.4 → 1.1), and gems per capture (10.2 → 10.2).

Adding X gems to every loss flips 1 game at +25, 4 at +100, 5 at +200 and 11 at +300.

Ranked for B318 (genes are B318's, same IDs as the seed):

1. **Capture yield**
   - Evidence: our captures pay 10.2 ± 0.9 gems, theirs 15.2 ± 1.1. 28.7 of our 76 captures per game pay 0 gems. Low yield is a cause in 50% ± 9 of losses.
   - Genes: `m11` camp_goal (still the nearest live spawn), `v2` CAMP_BASE.
   - Sim: B318 + gemgroups scores 14.4 gems per capture but loses to B318 0.450 (0.688 vs style-gconv1).
   - Deploy-faithful (--bot-seeds): every gem-group variant loses to B318, 33-38/80 (`rejected/README.md`). The sim
     does not reward richer groups. In real games yield barely separates our wins from our losses (11.3 vs 9.4), so
     it may follow from losing contested groups. Next test: real cambc with b318-gg6.
2. **Fights** (opponent patterns, real vs sim: `opp_patterns.py`; the sim side is B318 in local cambc, 3 games each)

   | our deaths to champions | real b2 losses | real b2 all | B318 vs hunter (sim) | B318 mirror (sim) |
   |---|---|---|---|---|
   | victim alone (no ally within 5) | 67% | 66% | 69% | 43% |
   | enemies within 5 at death (mean) | 2.00 | 2.11 | 2.17 | 1.96 |
   | pack grew in the last 10 rounds | 70% | 68% | 60% | 48% |
   | 2+ distinct hitters in the last 3 rounds | 42% | 47% | 63% | 52% |
   | killer closed 6+ tiles in 10 rounds (chase) | 48% | 45% | 37% | 39% |
   | killer / victim item points | 53 / 16 | 45 / 17 | 32 / 17 | 26 / 11 |
   | top killer's share of kills | — | 58% | 53% | 49% |
   | enemy time within 3 of an altar / within 6 of our spawn | 13% / 4% | 13% / 3% | 10% / 0% | 10% / 1% |

   The band opponents do not deathball (enemy champions average 13.5 tiles apart), camp altars or press our spawn.
   They converge on an isolated champion of ours and chase it. Hunter already reproduces that geometry. What it
   lacks is the fed carry: real killers carry 1.4-1.7x the item points of the sim's (53 vs 32 in losses).
   Stress opponent to build, "hunter-carry": hunter, plus one carry (its Vesper Vale; treasure passive) that takes
   the kills. Its allies leave low-HP enemies to it when it is within 4, and it buys only strength shards (the
   others keep the seed's split; making every champion all-strength was much weaker, see v1). Calibrate it until
   killer/victim item points reach about 50/16 against B318.

   Fights evidence: 
   - Evidence: 9.7 ± 1.3 deaths per game to champions, 11.0 in losses against 7.4 in wins. Fights are a cause in 44% ± 9 of losses.
   - Genes: `r7` / `s13` / `a3` / `a4` (B318 retuned `s13` and `a4`), and `s8` under_fire (B318 uses threat_eta <= 5).
   - Sim: `stress/hunter`; the sim under-counts these deaths, see gap 2 in v1.
   - **Mechanism (batch 2, 353 deaths in losses, 133 in wins): fed carries.** At our deaths in losses the killer carries
     53 item points against our victim's 16, with strength 259 against 92. In wins killer and victim are level (23 vs 21
     points). One enemy, usually Vesper Vale (133 of the 353 kills), snowballs. Burst deaths (dead within 2 rounds of dropping
     under half HP) are 20% of crossings in losses against 7% in wins. Conditions at the first hit do not separate
     outcomes (death rate about 50% outnumbered or not), but 51% of deaths end outnumbered by 2+.
   - Tried: avoid the fed carry when alone (`rejected/b318-fed18`, 40/80; fed14, 34/80). The sim has no fed carries
     (no band opponents), so it cannot price this. Levers worth a real test: our own item concentration (our victims
     carry 16 points), and denying the carry's kills. Both need a stress opponent that snowballs, or real games.
3. **Zero-gem maps: idle champions**
   - Evidence: 00contest submits 0 and 0 (they make 600). There, 3,529 champion-rounds over 2 games are spent standing idle with an empty bag. On 01elk_arena we submit 14 (they make 1008; our gems per capture there are 0.0, theirs 14.2).
   - On 00contest the only gems are in two monoliths (`docs/ZERO_GEM_MAPS.md`). B318's `r15` r_mono waits for round 1000, 3+ allies alive and team gems under 100.
   - Genes: `r15` r_mono, `m11` camp_goal / CAMP_BASE (excludes monolith and golem groups).
   - Sim: B318 on 00contest makes 100 to 200.
   - Tried: `rejected/b318-zerogem` (early r_mono) changes nothing on 00contest. In the sim, B318's champions sit near the
     spawn trading casts with enemies (395 moves in 2,000 rounds).
   - Traced (sim, B318 mirror, --bot-seeds; `tools/b318-rule-ping.genome` logs the rule of idle turns): 00contest has
     **0 captures all game**. From round ~1000 every champion holds a cleared gold-cluster spawn under `r16` r_hold.
     Both teams hold tiles of the same groups, so captures are contested forever. The edit "hold only when no enemy
     champion is on the group" (`rejected/b318-hold`) flips 00contest (2/2, tiebreak) but is neutral overall (40/80).
     The real 00contest idle spells were not on camp tiles, so the real cause may differ. 01elk_arena idles under
     rule 20 (no live camp goal) and 01shortcut under rule 12 (bank walk to monolith-guarded altars): three causes.
   - 01elk_arena: the idle rule-20 turns have a valid, open goal and a reachable field, yet no move. An unreachable-goal
     re-target (`rejected/b318-reach`, 39/80) never fires. The sim does not reproduce the real loss there either (B318
     beats L1c 16/20 on that map in the sim), so the next step is the real replays.
4. **Monolith deaths**
   - Evidence: 2.6 ± 1.0 per game on monolith maps (great_wall 17, boss_battle 11, contest 5, shortcut 4). A cause in 12% ± 6 of losses; it was 6% with v22.
   - Genes: `s14` / `r14` (B318: never wake a sleeping monolith, but a hit on another camp of its group still wakes it), `r13`, `a0`.
   - Sim: B318 + mono scores 0.512 vs B318.
5. **01shortcut: no bank** in both games (first tribute at round 1580, 80 gems submitted against 848). Both altars sit next to a monolith.
   - Genes: `m6` safe_altar_ring (B318: radius 6), `m12`-`m15`.
6. **Slow start: smaller now.** It is a cause in 19% of losses (was 29%). Our first tribute comes at round 112, theirs at 121, but they lead by round 500 in losses (245 vs 147).
7. **Stuck carriers: largely fixed in real games.** Spells carrying gems fell from 61 to 4. The remaining stuck rounds are the idle champions of gap 3. The sim still shows 43 stuck rounds per game for B318, and the commit graft that removes them loses (0.412).

---

## v1 (batch 1)


v1, batch 1 (24 Oct 2026). Data: 50 fresh unranked games of our live submission (v22 = tune-v20-L1c, see the correction below;
record 15-35) against 10 teams rated +55..+145 above us (1596),
all 40 maps. ± is one bootstrap SE over games. Raw tables: `batches/b1.md`. Sim numbers: seed genome vs the
compiled original (`python3 -m genome.intel.sim_metrics`, 400 games, all maps, unless noted).

**Correction (20:45 UTC): batch 1's bot was v22 (`policies/candidates/tune-v20-L1c.policy`, ladder v24), not v23.**
The coordinator reverted v23 at about 16:50 UTC. Both bots draft in the same order, but they bank differently: L1c
banks at 25+, v23 at 15 (or 10 near an altar or under threat). Of our 926 batch-1 tributes, 86% were 25+, 3% were
15-24 and 3% were 10-14, which is L1c. The gaps below are v22's gaps in real games. The gene mapping refers to
the seed genome (v23), which shares v22's rule structure except for banking; that covers r11 bag_ready (25 in
v22) and the r9/s11 sensors. The stuck-carrier and monolith mechanisms reproduce in the sim with the seed and with
v23.pol, so they hold for both. A paired batch 2 compares v22 to B318.

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
   - Stress opponent: `stress/hunter.genome` (commit, plus it chases visible carriers within 20 and fights carriers
     first). Commit loses 96.5 gems per game to it (48 against the original; real band 155), but champion deaths
     stay at 7.0 (real 10.2). No hunter knob moved deaths past about 7.4: pack-only chasing, altar ambush and
     strength stacking were all tried. The sim's fight model itself looks short of real kills, so the
     lever is likely in the simulator, not the opponent. Retreat/recall children all fail against hunter too
     (`rejected/README.md`).

3. **Capture yield: gold-only and poor groups.**
   - Evidence: our captures pay 10.2 ± 1.1 gems, theirs 15.3 ± 1.2. We make more captures (75 against 55),
     but 31 ± 7 per game pay 0 gems. Low yield (under 70% of theirs) is in 49% ± 8 of losses.
   - Genes: `m11` camp_goal (nearest live spawn), `v2` CAMP_BASE, `s12` group_threat, `r17` r_bankgroup.
   - Sim metric: `per_capture`; the seed scores 10.9.
   - Tried: a gem-groups child (14.4 per capture, 61 captures, neutral win rate in the sim); dropped.
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
   - Finding: the lock collapse is mostly gap 1. `commit`'s goal hysteresis alone takes lockall from a 0/10
     collapse on rushbait to 0.75 on rushbait + broken-curve, and to 0.725 over all maps. A lock-specific child
     (`rejected/lockfree`) adds nothing on top.

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
| `commit-mono` | 1 + 7 | commit + mono-spare (disjoint genes) | 0.577 (800, seeds 91001-2) | 0.550 | gate set below |
| `firstbank` | 4 slow first bank | commit + r11 (bank 8+ while the team has banked nothing) | 0.565 (seed 92001; commit 0.537 on the same games) | 0.475 vs commit | tributes 41.9 → 42.6 |

Dropped: `gem-groups` (gap 3; neutral, 0.492 / 0.487, fuel risk). Rejected after testing (in `rejected/`): `cashout`
(gap 2, −19 points vs commit) and `lockfree` (gap 6, neutral; commit already scores 0.725 vs stress/lockall).

Reference: the seed itself scores 0.507 against the original.

### Gate set for `commit-mono` (sim, normal fuel unless noted; fresh seeds)

| opponent | commit-mono | original (style-gconv1) | change |
|---|---|---|---|
| original, 800 games (seeds 91001 / 91002) | 0.577 (0.593 / 0.560), SE ≈ 0.018 | — | — |
| original, 10x fuel both, 400 (seed 91003) | 0.593 | (seed genome: 0.537) | — |
| seed genome, 400 (seed 91004) | 0.550 | — | — |
| v7, 400 (seed 91005) | 0.940 | 0.920 | +2.0 |
| tune-v20-L1 | 0.588 | 0.537 | +5.1 |
| rall2-ca4-lean-g | 0.588 | 0.517 | +7.1 |
| opp-tune5-metadraft | 0.877 | 0.873 | +0.4 |

## Children on commit-mono (the upload candidate; runtime genome/v0 822dbbe; seeds 95001 vs the original, 95002 head to head)

commit-mono itself scores 0.610 vs the original on these games (susp 2.7).

| child | gap | edits on commit-mono | vs original | vs commit-mono | gap metric |
|---|---|---|---|---|---|
| `gem-groups-cm` | 3 yield | v2, m11 (i5; gem set at round 3) | 0.610 (susp 2.2) | **0.600** | per capture 10.6 → 14.2, captures 83 → 62 |
| `firstbank-cm` | 4 first bank | r11 | 0.610 (susp 2.9) | **0.637** | tributes 42.1 → 43.0 |
| `yield-rr` (rejected) | 3 yield | v2, m11 (i8) | 0.375 | 0.312 | per capture 21.4, captures 32 |


## cm-gf and grafts onto B318 (Arena B; uploaded as ladder v25). Seeds: 96001 vs style-gconv1, 96002 head to head

Baselines here are against style-gconv1 (v23). The live bot before v25 was tune-v20-L1c, so these runs still need redoing on that basis.

| genome | vs style-gconv1 | head to head |
|---|---|---|
| B318 | 0.670 | — |
| `cm-gf` (commit-mono + gem-groups-cm + firstbank-cm) | 0.573 | 0.650 vs commit-mono, 0.450 vs B318 |
| commit-mono | — | 0.388 vs B318 |
| B318 + commit (`tools/graft.py`) | 0.637 | 0.412 vs B318 (stuck 43.0 → 0.6) |
| B318 + mono | 0.675 | 0.512 |
| B318 + gemgroups | 0.688 | 0.450 |
| B318 + firstbank | 0.620 | **0.575** |
| B318 + commit_bank only | — | 0.487 (stuck 18.1) |
| B318 + commit_live only | — | 0.438 (stuck 14.0) |
| B318 + commit_live + firstbank | — | **0.588** (stuck 11.4) |
| B318 + commit + mono (+ gemgroups, + firstbank) | 0.645 / 0.680 / 0.637 | 0.438 / 0.425 / 0.450 |

On B318 the stuck fix removes the stuck rounds but costs win rate, since B318's evolved rules depend on the
old flip behaviour. Only firstbank, alone or with commit_live, beats B318 at >= 0.53. Both lose to it against
style-gconv1 (0.620 vs 0.670), so they wait for the rerun against tune-v20-L1c.

### B318 as the base (ladder v25); anchors tune-v20-L1c (v22) and style-gconv1 (v23); seeds 97001 / 97002

| genome | vs B318 | vs L1c | vs gconv1 |
|---|---|---|---|
| B318 | — | 0.608 | 0.672 |
| `directed/b318-firstbank` | 0.575 | 0.573 (−3.5) | 0.600 (−7.2) |
| `directed/b318-live-firstbank` (commit_live + firstbank) | 0.588 | 0.575 (−3.3) | 0.625 (−4.7) |
| `directed/cm-gf` | 0.450 | 0.547 | 0.547 |

Both B318 grafts beat B318 head to head but lose 3-7 points against the anchors, so they fail the upload gate's
"no drop > 3" rule. They go to Arena B for selection, not upload.
