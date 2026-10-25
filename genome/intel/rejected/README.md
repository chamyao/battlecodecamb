# Rejected directed children (kept for the record; not for the arena)

Sim, side A, 400 games, all maps (seeds 92001 vs the original, 92002 vs commit, 92003 vs stress/lockall).

| child | gap | vs original | vs commit (parent) | vs lockall | why rejected |
|---|---|---|---|---|---|
| cashout | 2 gems lost on death | 0.443 | 0.312 | 0.575 (commit 0.725) | lost_to_champs 50 → 40, but retreats/recalls cost more than they save. Variants: recall only 0.450, recall at 30+ 0.450, retreat at 40+ 0.425 vs commit. The sim under-counts our deaths ~3x, so this lever needs real-game evidence first. |
| lockfree | 6 altar locks | 0.540 | 0.500 | 0.662 (commit 0.725) | neutral; commit's goal hysteresis already fixes most of the lock collapse (lockall on rushbait + broken-curve: commit 0.75). |

## Rerun against stress/hunter (runtime genome/v0 822dbbe; seeds 94010 vs hunter, 94011 vs the original)

| child | vs hunter | vs original | lost_to_champs vs hunter |
|---|---|---|---|
| commit (parent) | 0.637 | 0.547 | 96.5 |
| cashout (retreat + recall at 20+) | 0.525 | 0.475 | 75.5 |
| cashout, recall only | 0.613 | 0.532 | 93.6 |
| cashout, retreat at 40+ only | 0.650 | 0.500 | 94.0 |

None wins clearly against hunter while losing under 1 point against the original, so all stay rejected.

## yield-rr (gap 3, on commit-mono; runtime genome/v0 822dbbe; seed 95001 vs the original, 95002 vs commit-mono)

The camp group is chosen by reward rate and kept across turns: the current group plus 4 others are re-scored per turn
(round-robin), with a switch at +20%. Result: 0.375 vs the original (commit-mono 0.610) and 0.312 vs commit-mono.
Gems per capture rise to 21.4, but captures fall from 83 to 32 and camp deaths rise from 3.7 to 8.9 per game. Rate
variants (2x and 4x distance weight plus static camp strength) score 0.325 and 0.350 vs commit-mono. A sticky
nearest-gem rate scores 0.400, so the stickiness itself hurts. The stateless nearest-gem-group rule
(directed/gem-groups-cm) wins instead: 0.600.

## b318-zerogem (GAPS v2 #3, on B318; seeds 96002 head to head, 97001 vs L1c, 97002 vs gconv1)

r15 r_mono also fires after round 150 when no gem-paying group exists outside monolith/golem groups.
Result: 0.487 vs B318; vs L1c 0.595 (B318 0.608); vs gconv1 0.657 (B318 0.672). On 00contest nothing
changes (0 to 0). The trace shows why: team A makes only 395 moves in 2,000 rounds. Its champions stay
near the spawn trading casts with enemy champions, and the monolith rule never gets to act. That looks like
docs/ZERO_GEM_MAPS.md's 00reverse-spiral spawn duel more than the monolith gate. Next to check: `r2` r_heal,
`a3`/`a5` cast-ahead and `r7` near our own spawn on 00contest.

## Deploy-faithful rescoring (--bot-seeds, /80, runtime genome/v0 d0c0704; `tools/gate80.sh`)

| genome | vs B318 | L1c | gconv1 | v7 | tune-v20-L1 | rall2-ca4-lean-g | metadraft | susp |
|---|---|---|---|---|---|---|---|---|
| B318 | — | 43 | 52 | 76 | 48 | 52 | 68 | 3.0 |
| directed/b318-firstbank | 42 | 39 | 48 | 74 | 48 | 54 | 66 | 3.1 |
| directed/b318-live-firstbank | 43 | 44 | 49 | 75 | 51 | 47 | 69 | 3.4 |
| b318-hold | 40 | 46 | 49 | 76 | 48 | 53 | 68 | 2.9 |
| b318-hold-zg | 37 | 44 | 47 | 74 | 47 | 51 | 67 | 2.8 |

The two seeded winners (0.575 / 0.588) are even with B318 under --bot-seeds (42 and 43 of 80).

## b318-hold (GAPS v2 #3: the 00contest standoff)

On 00contest the sim (B318 mirror, --bot-seeds) records **0 captures in the whole game**. From round ~1000 every
champion sits on a cleared gold-cluster spawn under rule 16, r_hold; `tools/b318-rule-ping.genome` shows
16,114 rule-16 pings. Both teams hold tiles of the same groups, so the capture is contested, never completes,
and r_hold never lets go. b318-hold holds only while no visible enemy champion stands on the group's tiles.
00contest then flips to 2/2 with 136 captures, but still 0 gems (a tiebreak win). It is neutral overall
(40/80 vs B318) and mixed against the anchors. Adding the early monolith rule (b318-hold-zg) is worse: 37/80.
01elk-arena and 01shortcut do not change, so their causes differ. On 01elk-arena the idle champions are
under rule 20 (camp walk) with no live goal; on 01shortcut it is rule 12, the bank walk to monolith-guarded altars.

## Yield on B318 (GAPS v2 #1), --bot-seeds /80 vs B318

| child | vs B318 | per capture | captures |
|---|---|---|---|
| B318 + gemgroups (nearest gem-paying group) | 38 | 14.5 | 58.7 |
| ... gem group only if at most 3 tiles farther than the nearest group | 36 | 11.9 | 73.1 |
| ... at most 6 farther (kept: b318-gg6) | 38 | 12.5 | 69.2 |
| ... at most 10 farther | 33 | 13.0 | 66.5 |

Choosing richer groups raises gems per capture in the sim but loses head to head. The sim does not reward the
real yield gap. In the real games yield barely separates wins from losses (11.3 vs 9.4 gems per capture), so it
may be a consequence (being pushed off contested groups) more than a choice. Testing it needs real games, e.g.
b318-gg6 vs B318 in real cambc.

## b318-reach (GAPS v2 #3, 01elk_arena idle; --bot-seeds, runtime genome/v0 212a505)

The hypothesis: closest() (w4) treats candidate camp spawns as passable while walk_field (w5) does not, so a
camp-walk goal could be unreachable. The edit: when rule 20's field cannot reach its goal, re-target a free tile
next to a live camp. Result: 39/80 vs B318 (anchors: L1c 46 vs B318's 45, gconv1 52 vs 51, v7 76 = 76, L1 49 vs 47,
rall2 52 = 52, metadraft 70 vs 69). The re-target never fires on 01elk-arena: the rule pings stay at 980 idle
rule-20 turns with a valid, open goal and a reachable field. So the freeze is elsewhere: no downhill
step outside BLOCK, or refused moves. The sim also does not reproduce the real 01elk_arena loss (B318 beats L1c
16/20 there), so this gap needs a real-replay look first.

Anchor row of B318 itself at 212a505: L1c 45, gconv1 51, v7 76, L1 47, rall2 52, metadraft 69 (/80).

## b318-fed18 / b318-fed14 (GAPS v2 #2 fights: fed carries; --bot-seeds, 212a505)

r7 skips fights against an enemy at 1.8x (1.4x) our strength while no ally is within 4.
Result vs B318: 40/80 (34/80). Anchors: fed18 L1c 44, gconv1 49, v7 75, L1 52, rall2 48, metadraft 66; fed14 40, 51, 74, 47, 46, 69.
Vs hunter: 54 and 52 (B318 55). The sim's opponents never grow a fed carry, so the sim cannot price this lever.

## stress/hunter-carry calibration and lever (a) (GAPS v2 #2; --bot-seeds /80, runtime genome/v0 212a505)

stress/hunter-carry = B318 + a fed carry (its Vesper Vale stacks the treasure strength shard; non-carries leave targets
under 25% to it when it is within 4) + hunter's chase rule.

| variant | B318 vs it (/80) | B318 deaths to champions / gems lost to champions per game |
|---|---|---|
| non-carries buy no shards | 76 | 4.1 / 49 |
| non-carries keep the seed split, carry stacks the strongest shard, feed 0.25 | 52 | 6.6 / 91 |
| ... feed 0.4 | 60 | 6.8 / 110 |
| ... and non-carries hunt only with the carry within 6 | 56 | 5.5 / 66 |
| **... carry stacks treasure strength (18): stress/hunter-carry.genome** | **50** | **7.4 / 109** |

Real b2 losses: 11.0 deaths, killer/victim item points 53/16, burst 20%. With the strongest-shard carry (6 local
cambc games): killer/victim 17/17, burst 3%. The carry ends with the highest strength on the map (365) but fewer
item points than B318's own Vesper Vale (62 vs 85), so a B318-based opponent cannot reproduce the band's fed
carries; they out-earn us. B318 still wins 50/80 against the best version.

Lever (a), rejected/b318-carry (our Vesper Vale stacks shard 18): 29/80 vs B318, 48/80 vs carry (B318 50).
Anchors: L1c 42 (B318 45), gconv1 48 (51), v7 73 (76), L1 41 (47), rall2 44 (52), metadraft 72 (69).

## Fight children on B792 (ladder v26) for a possible ladder A/B (--bot-seeds /80, runtime genome/v0 b5d606b)

The bar: >= 38/80 vs B792, no anchor drop > 3, and a fight-metric gain vs stress/hunter-carry.

| genome | vs B792 | L1c | gconv1 | v7 | L1 | rall2 | metadraft | vs hunter-carry | deaths / gems lost to champions |
|---|---|---|---|---|---|---|---|---|---|
| B792 | — | 52 | 50 | 78 | 49 | 55 | 72 | 57 | 6.0 / 79 |
| b792-disengage (r3: retreat when a growing pack outnumbers us by 2+) | 36 | 45 | 50 | 77 | 46 | 47 | 68 | 58 | 7.1 / 109 |
| b792-disengage-bag (same, only while carrying) | 38 | 50 | 50 | 76 | 42 | 50 | 66 | 59 | 6.3 / 111 |
| b792-groupup (alone near enemies: go to the nearest ally before a 14+ gem group) | 39 | 54 | 45 | 76 | 47 | 56 | 72 | 58 | 6.1 / 161 |

None qualifies, since each drops an anchor by 5-8. All three lose more gems to hunter-carry than B792 (the
retreats are caught, and group-up walks carriers around). Same pattern as cashout: in the sim, disengaging costs more than it saves.

## On v28 (a61188-mono), runtime genome/v0 ca5180b, --bot-seeds /80

- v28-firstbank (r11: bank 8+ while the team has banked nothing): 27/80 vs v28; vs rushbank 54 (v28 53). v28 is
  not weak vs the rush banker in the sim (53/80), so the noobers loss is not a first-bank gap the sim shows.
- 01shortcut: in the sim v28 wins every game there, but banks only 257-585 gems and still has 8-10 camp deaths;
  the sim opponents are as stuck. Both altars sit in pockets reachable only through gem clusters cardinally connected
  to the monolith. The mono edit forbids hitting those, and hitting them wakes the monolith. Real band teams bank
  there 10-25 times a game. A "hit the altar blocker" variant (r13 with a non-monolith blocker) gains little (385 vs
  362 gems vs B792), and the rule's TGT still comes from reach_camp, so a clean fix needs c2/a0 edits too. Not pursued yet.

## Early bankers (real replays, `early_bankers.py`, b1-b5) and rushbank-v2

| | noobers (4-21 vs us) | GLM5.3 (9-16) | stress/rushbank vs v28 (4 local cambc games on noobers' maps) |
|---|---|---|---|
| their first tribute (median) | r37 | r79 | r31 |
| their first kill on us (median) | r239 | r293 | r225 |
| our deaths to them by r500 / kill bounties | 5.6 / 629 gold | 2.2 / 270 | 2.5 / 293 |
| our deaths before r500 in our half / at our camps | 69% / 71% | 24% / 49% | 90% / 50% |
| ... victim alone / carrying | 46% / 39% | 64% / 56% | 40% / 50% |
| ... enemy pack within 5 | 2.5 | 1.8 | 2.2 |

noobers bank by r37, then raid our half: they kill us at our own camps with packs of about 2.5, twice as often as
rushbank does. GLM5.3 kills us alone in their half instead.

rushbank-v2 (`rejected/rushbank-v2.genome`) adds the raid: after the team has banked, from r80 to r600 a champion with
under 10 gems walks to camps in our half. It makes the anchor weaker, not stronger. v28 wins 74/80 against it
(plain rushbank: 53). With the raid only when an ally is within 5, v28 wins 68; ending it at r400, 62. A B792-level
fighter loses the raids it starts, so the noobers raid works only with their fights, and a rule edit does not
reproduce it.

## v28-shortcut (GAPS #5, 01shortcut; rejected)

When every altar-adjacent tile is a camp spawn, r13 fights the non-monolith camp standing on the bank tile even
inside a monolith group, and c2 points rule 13 at it (new gene i12 blocker).
- Sim on 01shortcut: gems vs B792 362 → 557, vs farmer 585 → 599, vs hunter 546 → 574.
- Overall: 38/80 vs v28; anchors 0 to −3.
- Real cambc smoke on 01shortcut vs the v28 build: **lost both** (292-695 as A, 516-872 as B).

The sim's shortcut gain does not hold in the real engine.

## v28 directed-fix queue (genome lead's live analysis), runtime genome/v0 ca5180b, --bot-seeds

**(0) Fuel is not costing yield.** v28 at 1x vs 10x fuel, both sides:

| opponent | 1x fuel | 10x fuel |
|---|---|---|
| B792 | 52/80, 10.8 gems/capture, 82 captures, 6.0 susp | 46/80, 10.6, 83, 0 susp |
| A61188 | 41/80, 10.3, 86 | 43/80, 10.3, 84 |
| farmer | 50/80, 10.1, 83 | 48/80, 10.2, 80 |

**(1) Yield: not a timing problem** (`yield_contest.py`; rich group = 14+ gems per capture; real b5, b4 the same):

| b5 | rich captures us / them | our share of rich gems | first rich capture us / them | our deaths near a rich group per game |
|---|---|---|---|---|
| wins (18) | 24.2 / 17.3 | 59% | r79 / r74 | 5.7 (to champions 47%) |
| losses (32) | 19.6 / 28.6 | 34% | r66 / r63 | 9.2 (to champions 72%; 63% after r500) |

We reach the rich groups as early as they do, then lose them in mid-game fights. A camp-choice change
cannot fix this; it is gap 2 (fights) again.

**(2) 01boss_battle.**
- Narrowing r15 (monolith push only with 2+ or 3+ healthy allies within 5) does not reduce deaths: non-champion
  deaths vs B792 22 → 24.5 / 23; vs farmer 10.5 → 11.5 / 10; gems mixed. Files: v28-mono2, v28-mono3.
- Trace (v28 vs B792): the opponent wakes the monolith (591 hits against v28's 75). In the 30 rounds before 12 of our
  13 monolith deaths the hits were mostly or entirely theirs, and the awake monolith hits the nearest champion, often
  us at the single altar beside it.
- v28-awake (a bank walk into an awake monolith's range waits): lost all six games (0/2 against each of three
  opponents). Deaths fell against B792 (22 → 17), but it gives up the map's only bank.
- So boss_battle's monolith deaths are opponent-caused, and there is no cheap fix.

**(3) 01shortcut**: see v28-shortcut above (lost 0-2 in the real smoke).

## Fight study (`fight_study.py`): real b4/b5 engagements after r500 near rich groups, vs v28 in local cambc

Real, b4 + b5 (851 engagements):

| engagement result | n | champions us / them | HP at the first hit | item points | casts per champion | focus fire | we hit first |
|---|---|---|---|---|---|---|---|
| fights we lost | 327 | 2.2 / 2.4 | 3,964 / 5,008 | **55 / 128** | 2.6 / 2.9 | 72% / 72% | 48% |
| even | 441 | 1.7 / 1.5 | 3,483 / 2,705 | 54 / 59 | 2.0 / 1.7 | 77% / 68% | 62% |
| fights we won | 83 | 2.5 / 2.7 | **6,508 / 4,189** | 120 / 122 | **3.9 / 2.3** | 63% / 61% | 70% |

Sim (v28 vs farmer and hunter in local cambc, 10 games, engagements after r300) shows the same pattern, weaker: in
fights we lose they have 77 item points to our 50.

**Reading.** The band does not out-play us in fights:
- Focus fire is equal (72% / 72%).
- Retreat rates are equal (about 0.1 per engagement).
- Casts and hits in the first 3 rounds are close.

Fights are decided by the item and HP lead brought into them: 2.3x their item points in the fights we lose, and our
HP lead plus more casts in the fights we win. So the band's edge is economic (more gold → items), which then wins fights.

**Rules tried (all rejected):**
- v28-power08 / 08r / 06r: fight and cast-ahead only with local power (health × strength within 5) at least 0.8 or 0.6
  of theirs, optionally retreating at 1.5x theirs. Results: 33, 32 and 34 of 80 vs v28. Against hunter: 51, 61 and 61
  (v28: 65). Our deaths vs hunter fall to 4.2-4.3 with the retreat (v28: 5.2), but we lose more.
- picky-hunter (stress): a hunter that fights only with a 1.3x or 1.0x power lead. v28 wins 71 and 65 against it
  (plain hunter: 65), so it is weaker.

No fight rule closes the gap. The lever is the item lead itself, which comes from the economy gap (kill bounties
plus gem-group captures).

## v28-boss (01boss_battle; --bot-seeds, runtime genome/v0 ca5180b)

A bank walk into an awake monolith's range waits only while we would be its nearest target (an awake monolith hits
the nearest champion; an enemy champion nearer to it takes the hits). `farmable` itself never hits a camp in a monolith's
group, awake or not, unless the r15 push is on, so it has no special case for an awake monolith.

| 01boss-battle, 2 games each | v28 W / gems / non-champion deaths | v28-boss |
|---|---|---|
| vs B792 | 1 / 463-670 / 22 | 1 / 522-478 / 18 |
| vs farmer | 0 / 96-526 / 10.5 | 0 / 96-504 / 10.5 |
| vs hunter | 2 / 437-245 / 16.5 | 0 / 412-549 / 20 |
| vs A61188 | 1 / 0-0 / 9 | 0 / 359-487 / 11.5 |
| vs v28 itself | — | 0 / 557-927 / 20.5 |

38/80 vs v28 overall. On the boss map it wins 1 of 8 against v28's 4 of 8 (2-game samples). Rejected: banking beside an
awake monolith when an enemy is nearer still gets our carrier hit once that enemy dies or leaves.

## Bank-access fallback on v28-emblem (v29 candidate); --bot-seeds, runtime genome/v0 97194bf

- **v29-bank** = v29 + both parts:
  - Stall fallback: a bank walk with no field progress for 8 rounds gives up that altar ring until a tribute.
  - BREAK: enemy locks in reach are broken while carrying (the new option kind).
- **Variants:** BREAK only (v29-break) 37/80; stall only (`v29-stall`) **40/80**; stall at 15 rounds 38; BREAK only at
  an adjacent altar under a bank rule (`v29-bank2`) 38. BREAK at 145 costs: it spends attacks on locks we were not
  going to use.

| 3 bank-access maps, wins of 18 (vs B792, farmer, lockall; 2 games each) | shortcut | broken-curve | elk-arena |
|---|---|---|---|
| v28-emblem (base) | 5/6 | 4/6 | 2/6 |
| v29-bank | 6/6 | 5/6 | 2/6 |
| v29-stall | 6/6 | 5/6 | 1/6 |

Example gem gains: shortcut vs B792 414 → 670; broken-curve vs farmer 624 → 1,055.

v29-stall vs the anchors (base in brackets): L1c 58 (54), gconv1 66 (62), v7 76 (77), L1 58 (60), rall2 60 (63),
metadraft 76 (72), hunter 66 (64), hunter-carry 61 (66), farmer 44 (46), deathball 65 (62), rushbank 59 (60),
lockall 65 (64), **B318 48 (53)**, B792 47 (49), seed 59 (59), v28 51 (52). B318 drops by 5.

**Real cambc smoke** (v29-stall vs the v28-emblem build, both sides): shortcut 627-381 W / 184-632 L; broken-curve
673-1020 L / 1010-66 W; elk-arena 1044-324 W / 504-792 L. That is **3-3**, with +138 gems per game.

Not a pass: it banks more on these maps but does not win more, and one anchor drops by 5.

## Monster deaths vs idle (2026-10-25): group gates

Target from the Arena B lead: v29 vs builtin:idle (80 games, bot seeds) wins 80/80 but dies 4.25 times a game to monsters. Starvation (33) and starfish (15.5) are the worst maps.

**Trace.**
- Starvation: every death is to elk group 2 (4 elks, strength 240, 9,600 HP, 88 gems).
- Starfish: deaths are to elk group 15 (6 elks, 360).
- Champions wake the group one or two at a time, often by hitting its gem or gold clusters.
- Each lone champion then takes 240 damage a turn and can't walk out of range-4 coverage in time (1,140 HP to 0 in 5 rounds).

**Columns.** vs idle: monster deaths per game and gems short of 1000 (summed over 80 games). The paired/anchor columns compare against v29.

| child | change | deaths | short | notes |
|---|---|---|---|---|
| v29 (base) | | 4.25 | 8,766 | |
| v29-groupup | strong sleeping groups need 3 (4 at 360+) of us within 4 | 3.96 | 11,733 | stalls: starfish 674, great-wall 572, stampede 560 gems |
| v29-lanch (first version) | strong groups need the fight check (our summed damage × health ≥ theirs); weaker groups first | 2.56 | 11,094 | stampede 0 gems: its only gem group is a 6-elk herd that never passes the check |
| v29-lanchA/C/D | gem-first goal order; count fallback; no gate where no weaker gem group exists | — | — | the count fallback brings deaths back (stampede 23); gem-first order feeds early (stampede 33.5) |
| v29-lanchE(2/4) | weaker first + the fight check, both off on maps with no weaker gem group | 2.8 | 9,334 | 41/80 vs v29; anchors net +1. Pilgrimage 858 and elk-arena 504 gems (v29: 1,036 / 792). First build had 31 suspensions a game (per-camp group scans), fixed with a static STRONG set |
| v29-runlanch | lanchE + v29-run | 2.6 | — | 44/80 vs v29, but paired: B318 -6 (5 up / 11 down), L1 -6 (4 / 10) |

Not a pass. The gate removes most monster deaths on starvation and starfish (33 → 0, 15.5 → 0.5). But no version keeps v29's gems on maps where a strong group is the main gem source (stampede, pilgrimage, elk-arena). v29-run (directed/) is the narrow alternative that passes.

## Superseded (2026-10-25)

A81582-ringgg (Arena B lead: real 0-2 on pilgrimage, gold-rush and broken-curve, so withdrawn) and A81582-rgheal (heal fix on it: vs idle reverse-spiral 115 -> 1007, rushbait 16 -> 1006; 42/80 vs A81582-ringgg; anchors unchanged). Superseded by genome/arenab/cand/A81582-ringheal.genome (real 55/80 vs v29).
