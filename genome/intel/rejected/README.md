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
