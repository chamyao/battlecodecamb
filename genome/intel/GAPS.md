# GAPS: our live bot's measurable weaknesses in real band games (Arena B evidence)

## v4: batch 5, v28 = a61188-mono live (25 Oct, ~03:45 UTC)

Gap "monolith wake-ups" is closed in real games. Paired v27 → v28 on b1's plan:
- 13-37 → 18-32, with 5 flips to a win and 0 to a loss.
- Deaths to monoliths 1.86 → 0.58 per game.

What remains on monolith maps:
- 01boss_battle: the r15 monolith push, which is deliberate.
- 01shortcut: still unbankable for us (gems 27-497).

The other gaps stand as in v2/v3: capture yield, fights and kill bounties, early bankers (GLM5.3, noobers), and
the zero-gem maps 00contest and 01elk_arena.

## v3: batch 4, v27 = A61188 live (25 Oct, ~01:58 UTC; b1's exact plan, paired)

| batch (bot) | record | win rate | submitted by r500, us / them |
|---|---|---|---|
| b1 (v22) | 15-35 | 30% ± 6 | 153 / 245 |
| b2 (v25 B318) | 18-32 | 36% ± 7 | 179 / 227 |
| b3 (v26 B792) | 17-33 | 34% ± 7 | 180 / 235 |
| **b4 (v27 A61188)** | **13-37** | **26% ± 6** | 187 / 226 |

**v26 → v27, paired:**
- 4 flips to a win and 8 to a loss: not significant alone (sign test p ≈ 0.4), but the worst of the four batches.
- Gems submitted −13 ± 46; gems lost on death +15 ± 12; deaths to champions −0.2 ± 1.0; stuck rounds −58 ± 66.
- Economy in losses: they earn 8,768 to our 5,820. Their kill bounties are 1,506 (b2: 1,358) and they lead by 1,017 gold at r500.

**v27 vs the stress styles** (sim, --bot-seeds /80, runtime genome/v0 0372259; B792 in brackets):
- farmer 50 (44), deathball 55 (54), **rushbank 50 (59)**, hunter 57 (56), hunter-carry 64 (57); vs B792 itself 49.
- v27 is weaker than B792 only against the rush banker. In real games it lost the most against early bankers:
  GLM5.3 (first tribute about r93) went 3-2 → 0-5, and noobers (the rush banker, first tribute r37) stayed 0-5.
  Anime girls went 3-2 → 1-4.

**v27's 5 worst real matchups** (b4, with b3 in brackets):
- GLM5.3 0-5 (3-2)
- noobers 0-5 (0-5)
- NotSoLonely 1-4 (0-5)
- CompetitiveBasmaga 1-4 (2-3)
- lETHal 1-4 (1-4)

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
   - **Economy behind the fed carry** (`economy.py`, b2 / B318; b1 / v22 the same within noise). In our losses they earn
     8,146 gold to our 6,103 (−2,043). The gap splits about evenly:
     - **Kill bounties:** 1,358 against 261 (11 kills to our 2), −1,097.
     - **Gem-group capture gold:** 5,542 against 4,448 from a similar capture count (61 vs 67), −1,094.
     - Gold-only groups favour us (+386). Their other income (camp kills, passives) is about 240.
     - In our wins the picture reverses: we earn 9,773 to their 5,542, mainly from gem-group captures, 7,273 against 3,761.
     - Timing: the gap is −280 by round 250, −755 by 500, −1,256 by 750 and −1,638 by 1000, so it opens from the start
       and grows steadily, with no single swing.
     - So the levers are dying less early (each death pays them 100+ gold and feeds the carry) and holding the rich
       gem groups. A champion pick is not indicated: their "other" income is only about 240 per game.
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

## Fitness vs the band (pooled b1-b3: 150 games, bots v22 / B318 / B792; `predictors.py`)

| feature (ours minus theirs where d_) | AUC for a win | win rate, top / bottom third |
|---|---|---|
| d_submitted by r500 | 0.75 | 54% / 14% |
| d_gold earned by r500 | 0.74 | 54% / 14% |
| d_gold by r250 | 0.65 | 48% / 20% |
| d_gem-group captures by r500 | 0.64 | 42% / 22% |
| their deaths by r500 | 0.61 | 46% / 28% |
| our deaths by r500 | 0.45 | 28% / 38% |
| d_first tribute (ours minus theirs) | 0.34 | 22% / 48% |

Logistic regression on the r500 features with batch dummies, so each term is independent of which bot played:
- d_first_tribute −1.71 ± 0.59, the strongest term: bank before they do.
- their deaths by r500 +0.85 ± 0.31.
- d_gold by r500 +0.82 ± 0.37.
- d_submitted by r500 +0.65 ± 0.38.
- our deaths by r500 −0.00 ± 0.39.
- d_gem-group captures −0.08 ± 0.29.
- batch b2 −0.07, b3 −0.29: the bot adds nothing once these are known.

So a fitness term vs the band should reward an early gold and submission lead by r500, banking first, and kills.
Our own early deaths add nothing once those are known.

Caveat: the 150 games are 50 matchups × 3 bots. 17 maps were lost in every game and 3 won in every game, so the
matchup (opponent and map) dominates; treat the coefficients as directions, not sizes.

### The 5 band teams we lose to most (b1-b3), and how

| team | W-L | tributes / median bag / first tribute | gems per capture | kills on us | gold | their spread | type |
|---|---|---|---|---|---|---|---|
| NotSoLonely | 1-14 | 34 / 45 / r103 | 30.4 | 6.7 | 4,581 | 15.0 | **rich farmer**: richest groups, big bags, few fights, spread out |
| Sloppy Joe Pirates | 3-12 | 11 / 88 / r130 | 17.6 | 18.6 | 8,448 | 7.9 | **deathball fighter**: a tight pack that kills, banks rarely and big |
| noobers | 4-11 | 28 / 34 / r37 | 20.7 | 12.3 | 6,937 | 10.5 | **rush banker**: first tribute at r37, then fights |
| lETHal | 4-11 | 30 / 30 / r111 | 13.0 | 11.2 | 7,021 | 13.1 | balanced |
| Tozo's Disciples | 5-10 | 27 / 32 / r133 | 16.5 | 19.2 | 6,103 | 13.1 | **hunter**: the most kills on us |

Their spread is the mean distance between their champions. For comparison, the team we beat most is tst (10-5):
first tribute r150, 4.7 kills on us, spread 18.5.

Behaviours an exploiter population should find:
- the rich-group farmer, which takes the 30-gem groups;
- the deathball, which keeps its champions within about 8 tiles and fights;
- the rush banker, with a first tribute before r50.

`stress/hunter` and `stress/hunter-carry` cover only the hunter type.

## Economy mechanism (real b5, v28; `econ_source.py`), up to r500

| per game, our losses (32) | us | them |
|---|---|---|
| gold from captures | 1,654 | 2,089 |
| gold from kills | 53 | 508 |
| other gold (passives, camp kills) | 0 | 108 |
| captures by r500 | 22.7 | 22.7 |
| gold per capture event | 88 | 99 |
| **champions on a capture (sharing the reward)** | **1.8** | **1.0** |
| gold spent in the shop | 1,387 | 2,458 |
| Treasure shards bought / champions holding them / most on one champion | 9.8 / 3.9 / 3.4 | 2.6 / 1.9 / 1.0 |
| first Treasure emblem (5 shards on one champion) | never by r500 | never |

In our wins: captures 29.6 vs 20.3, gold from captures 1,984 vs 1,406, and the same 1.8 vs 1.0 champions per capture.

Mechanism, in order of size:
1. **They earn kill bounties early:** 508 against our 53 by r500, about 40-80 gold per 50 rounds from r50 on.
2. **We capture in pairs, they capture solo.** The capture count is equal, but we tie up 1.8 champions per capture
   to their 1.0, so their spare champion-time goes into kills and more groups. In the sim, forcing solo captures
   (`rejected/v28-solo`: skip groups an ally stands on) gives more captures but loses: 33/80 vs v28, and 5-12 points
   lower vs farmer, hunter and B792, because the pair protects us in fights.
3. **Correction: Treasure is not wasted.** econ_source.py looked for emblems among shop purchases, but emblems form by
   themselves from 5 shards, so its "never" was an artefact. From inventories, champions holding a Treasure emblem in
   real b5: by r250 us 0.28 / them 0.58; by r500 us 2.04 / them 0.92; at the end us 4.0 / them 1.2. What v28 lacks is an
   early emblem. `directed/v28-emblem` (Treasure shards go to one carrier until its emblem is complete) gets 1.67 by r250
   (v28: 0.50) in local cambc games, and beats v28 52/80 in the sim (see "v28-emblem" below).
4. **Draft:** both sides take Vesper Vale (100% / 88%), so the gold passive is not the difference.


## v28-emblem (directed; --bot-seeds /80, runtime genome/v0 ca5180b)

v28 + Treasure shards (item 18) go to one carrier (our Vesper Vale, else the champion with the lowest type id) until
it owns the Treasure emblem. The other champions buy Jungle-HP in place of their Treasure share. After the emblem
the carrier returns to v28's plan.

**Head to head vs v28: 52/80.** Variants (in rejected/): Vesper Vale only 39/80; no Treasure after the emblem 35/80.

| anchor | L1c | gconv1 | v7 | L1 | rall2 | metadraft | hunter | hunter-carry | farmer | deathball | rushbank | lockall | B318 | B792 | seed | A61188 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v28 | 55 | 60 | 77 | 58 | 60 | 76 | 65 | 59 | 50 | 63 | 53 | 68 | 53 | 52 | 57 | 41 |
| v28-emblem | 54 | 62 | 77 | 60 | 63 | **72** | 64 | 66 | **46** | 62 | 60 | **64** | 53 | 49 | 59 | 57 |

Three anchors drop by 4: metadraft, farmer and lockall (one game over the bar; SE about ±4.5). Big gains vs A61188
(+16), rushbank and hunter-carry (+7 each).

Local cambc, v28-emblem vs v28, 6 maps: won 4 of 6. Gold by r250 874 vs 951 and by r500 2,281 vs 2,209. Champions
with a Treasure emblem by r250 1.67 vs 0.50, by r500 3.0 vs 3.2. Team item points at r500 65 vs 66.

## Map ranking by cost (pooled b1-b5: v22, v25, v26, v27, v28 on the same 50 matchups)

Cost = the sum of loss margins / 1000 (a 1000-gem loss counts 1). Each map's 5 or 10 games are 1 or 2 matchups × 5
bots, so a map's cost is partly its opponent.

| map | W-L (b1-b5) | v28 | mean loss margin | cost | top loss causes |
|---|---|---|---|---|---|
| 01shortcut | 0-10 | 0-2 | 792 | 7.9 | no-bank 5, gems-lost 4, low-yield 4 |
| 00elkring | 0-10 | 0-2 | 547 | 5.5 | fights 10 |
| 00contest | 3-7 | 1-1 | 743 | 5.2 | low-yield 7, fights 5 |
| 01broken_curve | 1-9 | 0-2 | 559 | 5.0 | low-yield 5, no-bank 2 |
| 01elk_arena | 0-5 | 0-1 | 954 | 4.8 | low-yield 5, no-bank 4 |
| 01starvation | 0-5 | 0-1 | 941 | 4.7 | fights 5, slow-start 4 |
| 00corners | 0-10 | 0-2 | 466 | 4.7 | fights 4 |
| 00eight | 0-5 | 0-1 | 805 | 4.0 | fights 5 |
| 01yellow_brick_road | 0-5 | 0-1 | 737 | 3.7 | slow-start 3 |
| 00reverse_spiral | 0-5 | 0-1 | 697 | 3.5 | low-yield 5, fights 5 |
| 01boss_battle | 0-5 | 0-1 | 689 | 3.4 | monolith 5, gems-lost 5 |

The top 5 maps carry 32% of the total cost and the top 10 carry 56%. Over all losses the causes are low-yield 86,
fights 81, slow-start 31, gems-lost 19, monolith 15, no-bank 13.

Families:
- **Bank access** (shortcut, broken_curve, elk_arena): 17.7 of 87.6, about 20%, across three maps. Altars walled in
  by camps or monolith groups, enemy locks, or no reachable gem group. This is the next directed target worth more
  than one map, and it is partly reproducible in the sim: shortcut and elk-arena idle and bank late there.
- **Fights** (elkring, corners, eight, starvation, gemfight): about 21.6, the band's fight and economy edge.
- **Yield** (contest, reverse_spiral, expanse): monolith-only gems, spawn duels.

## B318 anchor: where the v28 line loses, and why (2026-10-25)

The question: B318 is the anchor that keeps blocking candidates (v29-stall -5, B1573 -10, Arena A genomes). Is that a real weakness, or a quirk?

**Method.** `--bot-seeds` /80 vs genome/candidates/B318.genome for three genomes: v28 (a61188-mono), v28-emblem (now live v29) and v29-stall. Per-game rows were tabulated by map.

**Overall.** v28 53/80, v28-emblem 53/80, v29-stall 48/80. B318 is not a strong opponent for this line. The drops come from chaos, not from one mechanism:
- v28 → v28-emblem: 79/80 games diverge; 12 flip up, 12 flip down; net 0.
- v28-emblem → v29-stall: 31 games diverge; 4 flip up, 9 flip down; net -5. That spread is a sign-test p ≈ 0.27, two-sided. The lost games are spread over 9 maps, with no map losing more than 1 game.

**Maps the whole line loses (≤1 of 6 across the three genomes):**

| map | v28 / emblem / stall | why |
|---|---|---|
| 01boss-battle | 1 / 0 / 0 of 2 | Sim-only lock: both sides tribute 0 for 2000 rounds (monolith beside the altar, 14 camp deaths each, no hits after ~r800), so the gold tiebreak decides it. v28 does the same vs v7. Never seen on the ladder: b1–b5 boss_battle games all ended with gems submitted (we lose there to monolith deaths instead). Down-weight. |
| 00packs | 1 / 0 / 0 | Close economy losses (829–892 vs 1013–1022): captures 55–56 vs 58–61. |
| 00reverse-spiral | 1 / 0 / 0 | Pace: captures 51–63 vs 72–76, with few kills either way. |
| 01the-farm, 01starvation, 00monolith, 01elk-arena | 2 of 6 | the-farm and starvation are capture gaps (fewer captures, not lost fights); monolith and elk-arena are mixed. |

**Mechanism.** The v28 line's losses to B318 are on captures, not fights:
- Mean capture difference in losses: -4 (v28), -14 (emblem), -8 (stall).
- Mean kill difference in losses: -2 to -5.
- Gems lost to champions are about even.

This is the same pace gap as the 5-worst-archetype "farmer" rows above, so it isn't a separate weakness.

**Recommendation.**
- Treat B318 as a noisy pace check, not a blocker.
- Gate an anchor drop on a paired sign test over the games that diverge (e.g. block at p < 0.1), instead of a flat >3/80.
- Exclude 01boss-battle from the B318 row, or score its 0–0 lock as a draw, since the lock doesn't occur on the ladder.

## Monster deaths and solo farming vs idle (v29, 2026-10-25)

Target (Arena B lead): v29 vs builtin:idle, 80 games with bot seeds. It wins 80/80 but dies 4.25 times a game to monsters, and some maps don't reach 1000 gems.

**Why we die** (traced with GAME_EVENTS plus a local, uncommitted champion-damage event):
- Starvation: all 33 deaths are to elk group 2 (4 elks, strength 240, 88 gems).
- Starfish: deaths are to elk group 15 (6 elks, 360).
- Champions wake these groups one or two at a time. Often the trigger is hitting the group's own gem or gold clusters at its centre, which wakes the elks too.
- The camp walk (m11) has no strength check, and r_run fires only below 30% health. A lone champion inside the cluster takes 240 a turn and needs 3+ turns to get out of range 4.

**Why some maps don't reach 1000 alone:**
- Reverse-spiral is supply-capped, not broken: 839 gems captured, from 7-gem clusters plus an elk group (g9, 44) and wolves (g0, 22) that we start taking only at r688 and r774.
- Contest's only gem sources are its two monoliths (200 each). r15 allows monoliths only while `team_gems() == 0`, so after the first one we never take another: 200 gems in 2000 rounds.
- Boss-battle and shortcut are not traced yet.

**Children:**
- **directed/v29-run.genome** (sha256 97cdc776…): r3 also runs when health < 2.5 × the basic-attack damage of the awake camps in range (new gene i19).
  - vs idle: deaths 4.25 → 3.84, gems unchanged (8,769 short vs 8,766).
  - 42/80 vs v29.
  - Paired vs v29's own rows: B318 51 (53; 8 up / 10 down), L1c 61 (54; 12 / 5), gconv1 61 (62), v7 79 (77), L1 61 (60), rall2 68 (63; 8 / 3), metadraft 75 (72).
  - No anchor drop is significant; pooled over the anchors it's 45 up / 30 down.
  - Real cambc smoke vs the v29 build: 3-2 (starfish 1004-106 W, lanes W, big-world W, starvation L, great-wall L), 0 crashes.
- **directed/v29-runmono.genome**: v29-run plus r15, which also allows monoliths after the first tribute on maps where only monolith groups pay gems (MONO_ONLY, computed at round 3).
  - Contest vs idle: 200 → 600 gems.
  - 41/80 vs v29; paired anchors the same as v29-run within a game or two.
- Group gates that stop lone wakes (v29-lanch family) cut deaths to 2.6–2.8 a game (starvation 33 → 0) but stall farming where a strong group is the main gem source. See rejected/README.md.

## Solo farming vs idle: two general bugs (v29, 2026-10-25)

Target (Arena B lead): maps where v29 doesn't reach 1000 gems vs builtin:idle. They are about 34% of the band loss cost.
- Seeds matter here: passing a map N times gives N seeds.
- Broken-curve fails on side A in every seed (0 gems); rushbait mostly fails on side B.
- Traced with a debug build that prints each champion's rule and goal (scratch only, not committed).

**Bug 1: bank goal on a camp tile.**
- ALTAR_RING / SAFE_RING include camp spawn tiles.
- On broken-curve side A, the bank walk (rule 12) goes for (19,22), an altar-ring tile that a live gold cluster occupies. From r122 to r2000 the 3 champions stand beside it with 16 gems each, and every move scores 0.
- Fix: drop small-camp spawn tiles from both rings at mapping time; keep monolith/golem tiles. Boss-battle's only reachable ring tile is the monolith's own; dropping it took boss-battle to 0.

**Bug 2: a hurt champion next to an enemy spawn never heals.**
- r2 (heal on spawn) is off while any enemy is in reach.
- On rushbait and reverse-spiral the spawns are adjacent, and enemies standing on theirs are always in reach.
- So a hurt carrier loops forever: recall (r5 cash-out) → arrive → leave in the same turn without healing (healing happens at turn end) → still hurt → recall again.
- Fix: r2 ignores enemies standing on their own spawn (we can't fight them there; r7 already excludes them).

**directed/v29-ringheal.genome** (sha256 7b71d08a…) = v29 + both fixes.
- vs idle, only five maps change:
  - broken-curve 309 → 1004 gems (r1164)
  - shortcut 586 → 1028 (r1560)
  - reverse-spiral 78 → 1020 (r1855)
  - rushbait 9 → 1018 (r1602)
  - expanse +107 rounds
- Total rounds 53,218 → 51,541.
- 42/80 vs v29.
- Paired vs v29's rows: B318 56 (53), L1c 55 (54), gconv1 63 (62), v7 77 (77), L1 61 (60), rall2 62 (63), metadraft 74 (72). No drops.
- Real cambc vs the v29 build, both sides: 7-1, 0 crashes. Broken-curve 1-1, shortcut 2-0, reverse-spiral 2-0, rushbait 2-0.

**directed/v29-ringhm.genome** = ringheal + monoliths kept on maps where only monoliths pay gems.
- Contest 200 → 800 vs idle.
- 42/80 vs v29; anchors net +1 (B318 51, rall2 61).
- Not preferred over ringheal.

**Rejected: gem-groups-first (v29-gg; v29-ringgg with a strength cut at 300).**
- vs idle it's excellent: elk-arena, gold-rush, broken-curve and shortcut all reach 1000; total rounds 49,909. A cut under 300 avoids stampede's 6-elk herd. Paired anchors +24 in the sim.
- But it skips gold-only groups, so it starves gold vs a real opponent (pilgrimage 4,583 vs 14,258 gold; gold-rush 3,474 vs 23,151). It loses those fights: real smoke 0-2 on both maps.
- Its earlier cambc smoke was also void, because of the bot bug below.

**Bot bug (fixed in bb4c439):**
- bot/src/bot_api.cpp dropped the per-group gold, gems and respawn words of sdk_map_camp_layout, so group_gems / group_gold read 0 in cambc.
- v29 doesn't use them; gem-groups genes do.

## Contest rule on A81582-ringheal (2026-10-25)

**directed/A81582-rhm.genome**: A81582-ringheal + r15. On maps where every gem-paying camp spawn (wolf, elk, gem cluster, golem) is in a monolith group, keep going for monoliths after the first tribute. MONO_ONLY is computed from camp types, so it doesn't depend on group_gems.
- vs idle: only contest changes (200 → 800 gems, r1944).
- 39/80 vs A81582-ringheal; only contest's two games differ, the other 78 are near mirrors.
- Paired anchors: B318 63 (65; 0 up / 2 down), L1c 67 (65), gconv1 66 (65), the rest unchanged.
- Real cambc vs the A81582-ringheal build: 2-0, 0 crashes. 1000-200, then 600-600 won on the gold tiebreak (17,645 vs 15,431).

## Gem-first after the first buys (A81582-gg6, 2026-10-25)

**directed/A81582-gg6.genome**: A81582-ringheal + weak gem groups first (gem-paying, design strength under 300), but only after the champion has bought 6 times. A buy is a gold drop of 30+ between its turns. Before that it keeps v29's nearest-first order, which includes the gold-only groups near spawn. It reads group_gems, so it needs a bot built from genome/v0 at or after fd778fc.
- vs idle: total rounds 49,606 → 48,640.
  - Faster: great-wall 1862 → 1340, elk-arena 1885 → 1702 (864 → 1008 gems), yellow-brick-road 986 → 882, swirl, islands. Shortcut 644 → 746 gems.
  - Worst map: starfish +87 rounds. Monster deaths 6.53 → 6.04.
- 44/80 vs A81582-ringheal.
- Paired anchors vs its rows: B318 64 (65), L1c 62 (65; 4 up / 7 down, p 0.55), gconv1 67 (65), v7 78 (76), L1 63 (62), rall2 67 (64), metadraft 79 (79). Net +3, no significant drop.
- Real cambc vs the A81582-ringheal build: 4-2, 0 crashes.
  - pilgrimage 2-0 (1012-435, 1018-815); plain gem-first lost it 0-2
  - gold-rush 1-1
  - elk-arena 1-1 (1008-36, 708-804)
- A81582-gg3 (after 3 buys): 47,756 rounds vs idle, but starfish +158; 42/80 vs ringheal. No real smoke.
