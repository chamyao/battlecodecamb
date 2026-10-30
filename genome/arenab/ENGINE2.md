# Ladder engine 2.0.0 (cambc 4.0.0): what changed, from the SDK diff

Ladder games moved from engine 1.0.3 (cambc 3.0.5) to 2.0.0 (cambc 4.0.0, pip, released Oct 25 23:42 UTC).
Everything we measure locally (genome_eval sim, arena engines, real-cambc gates on 3.0.5) is on the old rules.
This note compares the SDK that `cambc init` writes for 3.0.5 (~/ws/sdk) and 4.0.0. The engine binary is
closed, so only what the SDK exposes is known; the new families' effects are not documented there.

## Maps: 40 -> 70 (none removed)
New: 00anvil 00breadcrumbs 00crater 00dunes 00galaxy 00oasis 00quarry 00ribs 00the-line 00vault, 02arena
02crossing 02cuts 02famine 02fields 02geodes 02gift-wrapping 02guardians 02harvest 02stalactites 02tangle
02the-pack 02the-pond 02treasure-box 02uncharted-lands, adgato-gemcombat1..5.
Our 40-map gates now cover 57% of the pool, and `--bot-seeds` 80-game sets no longer match deploy.

## Items: 7 families -> 14
- Item id = family * 6 + stat * 2 + (0 shard / 1 emblem), stat 0 str / 1 focus / 2 health. Ids 0-41 are
  unchanged, so our a11 constants (18/19 Treasure-Str, 28/29 Jungle-HP, 36 Bruiser-Str) still mean the same items.
- New families (ids 42-83): tribute 7, capture 8, prospector 9, hunter 10, skirmish 11, greed 12, collectors 13.
  New passives: tribute, capture, prospector, hunter, skirmish, collectors (greed has none listed).
- Changed passives (doc strings):
  - Treasure emblem: 20% -> **10%** more gold. Our shop goes Treasure first; that plan is now half as good.
  - Monster emblem: 10% -> **15%** more camp damage.
  - Unchanged: Power (counts as six shards), Durability 10% less damage, Jungle 30% less camp damage,
    Home recall 3 turn ends, Bruiser 5 + 1 of each.

## Camp capture
New API `camp_group_capture_state(handle) -> {timer, state}` with states no_capture_available,
ally_capturing, contested, enemy_capturing, capture_available. Capture is now contestable and visible to
bots; our r_hold / group_reward logic was written for the old capture rule.

## Other
- C++ SDK caches my champion / team per turn (cached_my_champion); ability target masks come from the design.
- No other API change in _cambc.pyi.

## What this means for our pipeline
1. Sim (genome_eval), arena gates and tune-B/Arena B real gates on 3.0.5 are measuring the old game.
   Nothing they produce after Oct 26 is evidence for the ladder until re-run on 4.0.0.
2. Real gates must move to cambc 4.0.0 and to the 70-map pool (140 games per pairing).
3. The sim needs the new item families, the passive changes, the capture rule and the new maps before it
   can screen anything again.
4. First directed targets once measurable: the shop (Treasure halved; new families unknown) and capture holds.

## Smoke on 4.0.0 (Oct 30 ~03:20 UTC)
v33 (B1873-bossbush) builds unchanged with cambc 4.0.0 (`cambc build --release`, fresh .cambc cache) and plays a
mirror on all 70 maps with 0 crashes/errors (side A 32, side B 38; mean 1,350 rounds, 14 games to r2000). Workspace:
scratchpad cambc4/ws4 (venv with cambc 4.0.0; ~/ws stays on 3.0.5).

## Shop probe on 4.0.0 vs v38 (Oct 30 ~03:40 UTC)
v38 = A93635-v33port (sha 67ea6f01). Its a11 + a9: Treasure-Str 18/19 -> Jungle-HP 28/29 -> Durability-HP 16/17 -> Bruiser-Str 36.
Variants (cand/engine2/), built from genome/v0 HEAD runtime with cambc 4.0.0 --release, 70 maps x 2 sides
(genome/arenab/gate4.sh, build4.sh). Bar for a constant-only change: >= 81/140.
| order | vs v38 /140 |
|---|---|
| Monster-Str -> Treasure -> Jungle -> Dur -> Bruiser (shop-mon-treas) | 76 |
| Jungle -> Treasure -> Dur -> Bruiser (shop-jung-first) | 74 |
| Monster-Str -> Jungle -> Dur -> Bruiser (shop-mon-first) | 72 |
| Jungle -> Dur -> Bruiser (shop-no-treas) | 68 |
| Jungle -> Dur -> Treasure -> Bruiser (shop-treas-last) | 66 |
| Treasure -> Monster-Str -> Dur -> Bruiser (shop-treas-mon) | 59 |
All 0 errors. No pass. Monster-first is mildly positive (76, 72) and dropping Jungle hurts (59); Treasure's halving did not
make it a liability. The seven new families (ids 42-83) were not tried: their effects are not in the SDK; waiting for
intel's rules export. (gate4.sh's mirror line counts both sides as the candidate when names match; ignore it.)

## The new item families are not reachable from our bots
Probe: v38 with each new family's Str emblem (ids 42/43 ... 78/79) in place of Treasure: every variant 2/140 vs v38.
Cause: the runtime's engine model has `kNumItems = 42` (genome/v0 bot/src/cbs/core.h; also sim/include/cbs/core.h), so
genome_rt.h never lists BUY options for ids 42-83 and shop_pending() keeps the champion waiting on spawn for an item
that never appears. Not a measurement of the families. Needed before any probe: kNumItems 84 plus item_design rows
(cost, combine count, passive, stat growth) for the 7 new families in bot/src/cbs (from the rules export), and the
same in the sim. The bot's own cbs tables also still carry the old Treasure/Monster passive values.

## Draft probe on 4.0.0 vs v38 (Oct 30 ~04:10 UTC)
v38 d1 order: Vendetta, Vesper Vale, Tavi, Ryth, Ren. Single changes, 70 maps x 2 (cand/engine2/draft-*):
| draft (pick order) | vs v38 /140 |
|---|---|
| Ven, VV, Tavi, Ryth, Marcella (Marcella for Ren) | 71 |
| Ven, VV, Tavi, Ryth, HoR (HoR for Ren) | 69 |
| Ven, Issac, Tavi, Ryth, Ren (Issac for VV) | 65 |
| Ven, Tavi, Ryth, Ren, VV (VV last) | 65 |
| Ven, VV, Marcella, Ryth, HoR (no Tavi, no Ren) | 45 |
| Ven, HoR, VV, Marcella, Ryth (top teams' core) | 28 |
All 0 errors; none passes. Ren's slot is a wash; Tavi is load-bearing for this genome (remote shop: it buys anywhere),
and the top teams' core is far worse for our play style. VV's nerf does not make it replaceable by Issac.

## Search pass A103740 (arenaA-10) on 4.0.0
Old-engine sim 46/80 vs v38 (gatekeeper-32, all anchors clean). cambc 4.0.0 vs v38: 61/140 (old maps 45/80, new 16/60). Fail.

## Solo vs idle on cambc 4.0.0, all 70 maps (side A, rounds to finish; 2000 = never)
v38 total 83,068 rounds vs v33 80,876. Maps where v38 is >150 slower than v33 or either never finishes:
| map | v38 | v33 |
|---|---|---|
| 02stalactites (new) | 1782 | 408 |
| 00quarry (new) | 2000 (freeze; intel reproduced) | 869 |
| 01boss-battle | 2000 | 1398 |
| 01elk-arena | 1979 | 1550 |
| 01gold-rush | 2000 | 1815 |
| 01starvation | 2000 | 1813 |
| 00stampede | 2000 | 1810 |
| 02gift-wrapping (new) | 1130 | 916 |
| 01starfish | 1305 | 1141 |
| 00the-line, 02guardians, 02the-pack (new) | 2000 | 2000 (neither finishes) |
v38 is faster on 00contest, 00interlock, 00reverse-spiral, 00ribs, 02arena, 02fields. Solo is not the main new-map gap
(b14 new-map losses are fights: half the gold, +4 champion deaths), but v38 has solo regressions vs v33 on 7 maps, and
three new maps are unsolvable solo for both.

## Solo bisection on 4.0.0: v33 genes swapped into v38, one at a time (02stalactites, 00quarry vs idle)
Base v38: stalactites 1782, quarry 2000. 31 genes differ.
- 02stalactites: 8 different single swaps each fix it (a12 399, m11 427, s4 433, v2 448, r11 454, s15 454, r3 461, s3 515);
  8 others make it 2000 (a3, a8, a9, r16, v3, w1, w10, w3). Fragile timing/path behaviour, no single cause.
- 00quarry: no single swap fixes it (all 2000). Left to intel (replay extractor on v2) and the genome lead.

## Solo cluster bisection (00stampede, 01starvation, 01gold-rush, 01boss-battle: v38 2000 on all, v33 finishes)
v33 genes into v38, one at a time: only v2 (1573/1399/1939/1947) and m11 (1875/1430/1932/1771) improve all four; a9, a12,
m5, r16 fix boss-battle (1348-1390); m6, r11, r12, r5 help gold-rush. v38's m11 skips groups an ally already holds
(held_groups: the "spread" idea that lost 3-7 / 2-8 in intel's real tests on v33); v38's v2 adds lock-skip near
enemies, a narrower BLOCK (allies > 4 away ignored) and more priority classes.
Gates on 4.0.0 (correct old/new split; earlier "old-map" counts in this file included the ten new 00-maps):
| candidate | vs v38 /140 (old/80, new/60) | vs v33 /140 | solo total (v38 83,068; v33 80,876) |
|---|---|---|---|
| v38 + v33 v2 | 77 (41, 36) | 79 (v38 itself: 82) | 79,348 |
| v38 + v33 m11 + v2 | 77 (42, 35) | - | 80,712 |
| v38 + v33 m11 | 67 (39, 28) | - | 81,797 |
v38-v2 clears the structural bar vs v38 but is -3 vs v33 against v38's own row: within noise, not recommended.

## b14 new-map losses (intel extract_v2 rows) and a yield probe
15 new-map losses: gems per capture us 13.2 vs them 24.3; first tribute r314 vs r247; we capture more often but smaller
(02famine 120 caps x 7.3 vs 46 x 22.3; 02treasure_box 148 x 7.4 vs 62 x 16; 00anvil 105 x 6.3 vs 72 x 12). Low-yield 10/15,
fights 9/15. 02the_pack is 0-0 for everyone; 00quarry is the v38 freeze.
Probe on 4.0.0 vs v38 (/140, old /80, new /60), all 0 errors, none passes:
| variant | total | old | new |
|---|---|---|---|
| gem groups strength cap 300 -> 450 | 72 | 42 | 30 |
| cap 300 -> 600 | 71 | 41 | 30 |
| gem groups with >= 12 gems, cap 450 | 73 | 43 | 30 |
| gem-first after 3 buys, cap 450 | 66 | 40 | 26 |
| gem-first from round 3 (no buy gate) | 58 | 30 | 28 |
Richer-group targeting does not pay against v38; the band's rich-group opponents also out-fight us there, so the yield
gap is not a camp-choice constant.

## New-family probes on v39a (runtime genome/v0 671ac45b, kNumItems 84), cambc 4.0.0 vs v39a
v39a = v38 + quarry bush fix (sha 22ec24cf). Each family's Str emblem either first, or in place of Jungle-HP:
| family | first (total / old / new) | in place of Jungle |
|---|---|---|
| Prospector (+25% cluster share) | **76 / 42 / 34** | 58 / 34 / 24 |
| Hunter (+50 kill gold) | 66 / 35 / 31 | 64 / 34 / 30 |
| Capture (3-round capture) | 62 / 33 / 29 | 65 / 33 / 32 |
| Skirmish (x1.05 vs champions) | 61 / 35 / 26 | 46 / 22 / 24 |
| Tribute (shorter channel) | 51 / 26 / 25 | 58 / 33 / 25 |
Hold-out for prospector-first (total / old / new): vs v38 71 / 35 / 36 (v39a itself 71 / 38 / 33); vs v33 83 / 47 / 36
(v39a 78 / 46 / 32). New maps +3-4 over v39a against every reference. Hunter and Skirmish do not pay as a first emblem;
Jungle stays load-bearing.

## Prospector follow-ups vs the live v39 build (v39a on runtime 35bcf691a), cambc 4.0.0
prospector-first vs live v39: 69 / 35 / 34 (genome lead's run: same). Follow-ups (total / old / new):
| variant | result |
|---|---|
| Prospector after Treasure (pros-after-treas) | 63 / 32 / 31 |
| Prospector first when >= 12 gem+gold cluster spawns (pros-cond12) | 69 / 35 / 34 |
| ... >= 20 (pros-cond20) | 70 / 36 / 34 |
| ... >= 30 (pros-cond30) | 69 / 37 / 32 |
None reaches the 76 structural bar. The +3-4 new-map edge is real but small; no map-type gate isolates it from the
old-map cost. Shop probes on 2.0.0 are done: v39a's shop stands.

## Exploiters on 2.0.0
exploit-5 keepers (old engine) vs live v39 on 4.0.0 (total / old / new): x5-24 65/31/34, x5-108 64/36/28, x5-134 69/41/28.
None is a strong exploiter on 2.0.0. exploit-6 briefed (relay writer): runtime 671ac45b sim, target v39a, seeds v39a/x5-134/x5-24,
fitness wins + 0.01 x kills, 150 programs, top 8 real-screened on 4.0.0 (140 games), keepers become stress anchors.

## Carrier-safety edits on v39a vs live v39 (4.0.0; total / old / new)
cs-run (carrier with 20+ gems retreats when visible enemies within 7 outnumber allies within 5): 60 / 28 / 32
cs-bank (bag ready at 6+ gems when outnumbered that way): 62 / 36 / 26
cs-both: 63 / 33 / 30
All worse. Same result as on the old engine: pulling carriers out of play costs more than the bags it saves. Waiting on
exploit-6 for anchors that reproduce the ladder fights.

## exploit-6 (engine 2.0.0, queue writer, $0): candidates, not just anchors
Relay writer's real screen vs v39a (runtime 671ac45b): top 8 at 80-83/140 (mirror 70); no keeper at the 1.3x kill bar; anchors
frozen: x6-61, x6-83, x6-30 (arenab/b14-relay cdba85d3 arenab-b14/x6-exploit/exploit-6/keep/anchors/).
Line: v39a -> #4 (update: contest a gem group an enemy is farming; healthiest fighter acts first) -> #30 (held_groups: do not
leave a contested capture) -> #61 (r_hold: every ally on a contested capture holds).
My check on cambc 4.0.0, vs the live v39 build (v39a on runtime 35bcf691a) and hold-outs (total / old / new):
| candidate | vs live v39 | vs v38 | vs v33 |
|---|---|---|---|
| x6-83 (823f1ca3) | 79 / 46 / 33 | 80 / 46 / 34 | 75 / 39 / 36 |
| x6-61 (513f4ef1) | 77 / 43 / 34 | 78 / 43 / 35 | 77 / 40 / 37 |
| ref: v39a on 671ac45b | 69 (genome lead) | 71 / 38 / 33 | 78 / 46 / 32 |
Both clear the 76 structural bar vs live and gain +7-9 vs v38 over v39a's row; vs v33 they are -1 to -3.

## v40 = x6-83 (genome/v0 8e6dfb46c; genome lead reproduced 79/140 vs live v39)
x6-83 vs x6-61: x6-83 changes c0 (kill shot at 172 above cash-out) and r16 stays v39a; x6-61 changes r16 (every ally holds while
capture_state == CONTESTED). Combined (v40-hold): vs v40 71 / 40 / 31, vs live v39 77 / 43 / 34, vs v38 78 / 43 / 35, identical to
x6-61 alone; the hold rule masks the kill-shot gain. No better candidate than v40.

## v40 live (06:12Z); exploit-7 briefed (target v40, seeds v40/x6-61/x6-30, same setup; capture-contest emphasis)

## Band b16: v40 31-29 (same as v39, 6 flips each way); gems +30, +93 on b14 new maps. The 79/140 vs v39 did not carry to
ladder teams. v41 = v40 + cheap mono_groups going up. exploit-7 switched to multi-opponent fitness (v40, v38, v33, x6-30, band styles),
real screen vs v40 and v38.

## exploit-7 (vs v40 only; the multi-opponent change arrived after it started)
Relay writer's real screen vs v40: x7-125 77, x7-142 77, x7-110 76, x7-149 76 (mirror 70). Line: v40 -> #12 (hold a capture
through a threat with 3 allies on it) -> #27 (rule_target focus fire) -> #34 (no monoliths with an enemy within 6) -> #110
(later cash-out: recall below 0.4 + gems/60, cap 0.7; was 0.5 + gems/60, cap 0.85) -> #125 (stop piling onto a contested
capture once 3 allies hold it). Gain is gems v40 loses on death (1.14x), not kills.
My multi-opponent check on 4.0.0 (total / old / new):
| bot | vs v40 | vs v38 | vs v33 | vs x6-61 |
|---|---|---|---|---|
| x7-125 (4afcd1b6) | 77 / 42 / 35 | 80 / 49 / 31 | 76 / 38 / 38 | 79 / 42 / 37 |
| x7-149 (e12059a2) | 76 / 45 / 31 | 74 / 43 / 31 | 74 / 39 / 35 | 74 / 44 / 30 |
| v40 itself | 70 (mirror) | 80 / 46 / 34 | 75 / 39 / 36 | 66 / 39 / 27 |
x7-125 is >= v40's own row against every reference (+7, 0, +1, +13). x7-149 is below v40 on v38. Candidate: x7-125.

## CORRECTION: x7-125 retracted (reference-bot runtime mismatch)
My v38 and v33 reference bots in the hold-outs above were built on older genome/v0 runtimes (v33e2 even on the pre-2.0 one),
while candidates were on 671ac45b. With v38 rebuilt on 671ac45b ("v38n"): x7-125 68 / 41 / 27, x7-149 76 / 45 / 31, v40 (x6-83)
84 / 48 / 36 (relay writer's numbers reproduced). Every exploit-7 pick drops 8-16 vs v38 relative to v40: the later cash-out
overfits v40. No candidate. Hold-out rows in this file against "v38" and "v33e2" before this note are on mismatched builds.
Rule from here: every reference is built on the candidate's runtime. exploit-8 started with multi-opponent fitness
(v40, v38, v33, x6-30, band styles; all on 671ac45b).

## exploit-8 (multi-opponent mean fitness: v40, v38, v33, x6-30, farmer; all on 671ac45b; ran vs v40)
Relay writer's real screen (total, old/new); bar >= 76 vs v40 and not below v40's own row vs v38 (84) and v33 (65):
| bot | vs v40 | vs v38 | vs v33 |
|---|---|---|---|
| x8-140 (e3217087) | 81 (48/33) | 80 (43/37) | 72 (38/34) |
| x8-87 | 73 | 79 | 74 |
| x8-8 / x8-11 | 72 | 79 | 75 |
| v40 own row | 70 | 84 (48/36) | 65 (40/25) |
No candidate under the bar. x8-140 is +11 vs v40 and +7 vs v33 but -4 vs v38 (sum over the three: 233 vs v40's 219); it fights
better (10.0 kills / 6.9 deaths per game vs the mirror's 8.75 / 8.75). Line adds: break an enemy capture before its timer
runs out (camp_goal), hit the champion not camps in a fight, lock the altar nearest an enemy gem carrier.
Every exploit-8 program beats v40 vs v33 and trails it vs v38.

## v43 = x8-140 live (genome lead real 81/140 vs live v40). Search sim solo-blocked it (+1057 rounds on 00quarry, 00reverse-spiral,
01starvation); real cambc solo vs idle (both sides): quarry 879/822 vs v40 879/818, reverse-spiral 2000/2000 both, starvation
2000/2000 vs 1912/2000. Sim artefact; real solo is the check. Sim also underrates v43 h2h by ~12.

## CORRECTION: v43 quarry-A stall is real
My solo checks used a C++ starter with play_turn removed as "idle"; fuel/search use genome/examples/idle.genome (different
draft). 00quarry side A, real 4.0.0: x8-140 (v43) 879 vs starter-idle but 1699 vs genome-idle (B side 796); v40 861/794,
v39a 891/794 vs genome-idle. The sim was right: v43 stalls on quarry A against that draft. Solo-vs-idle numbers earlier in this
file used the starter idle. From here, solo checks use the genome idle.

## v43 quarry-A stall: bisection and fix (solo vs genome idle, real 4.0.0)
v40 genes swapped into x8-140 one at a time (differ: Zb, a0, c0, m1, m11, v2): only Zb (farmable) fixes quarry A (1699 -> 861).
x8-140's Zb: no camp hit while an enemy champion is in my reach and I am above half health. On quarry A the idle enemies
stand on their spawn within reach of our camps, so those camps are never farmed.
v43-fix (cand/engine2/v43-fix.genome): the same rule, ignoring enemies on their own spawn.
- Solo vs genome idle, all 70 maps x 2 sides: totals v40 158,785, v43 159,965, v43-fix 159,048; 0 losses each.
  quarry A 861 (v40 861). Remaining v43-only slow spots, unchanged by the fix: boss-battle B 2000 (v40 1498), famine B 1773
  (1532), expanse A 1463 (1309).
- vs v43 (x8-140 on 671ac45b): 71 / 41 / 30, a bugfix-level change.

## boss-battle B / famine B on v43-fix: bisection and fix (solo vs genome idle, real 4.0.0)
v40 genes into v43-fix one at a time: only m11 fixes both (boss-battle B 2000 -> 1572, famine B 1773 -> 1532). v43's m11 sends
a healthy champion to any contested ally capture within 8 first; idle enemies on/near their spawn keep a group contested, so
champions keep walking back to it.
| variant | solo total | quarry A | boss-battle B | famine B | expanse A | new slow spots vs v40 | vs v43 /140 |
|---|---|---|---|---|---|---|---|
| v40 | 158,785 | 861 | 1498 | 1532 | 1309 | - | - |
| v43-fix (Zb) | 159,048 | 861 | 2000 | 1773 | 1463 | - | 71 / 41 / 30 |
| v43-fix2 (+ m11 contest target minus ring(enemy_spawn, 3)) | 162,053 | 840 | 1353 | 1646 | 1569 | 12 maps (stalactites B, boss-battle A, stampede A 2000) | 70 / 33 / 37 |
| v43-fix3 (+ m11 only when an enemy champion off its spawn is within 10) | 160,409 | 861 | 1572 | 1675 | 1309 | 02stalactites A 2000 (v40 429) | **75 / 43 / 32** |
fix3 without stalactites A: 158,838. Stalactites is the fragile map from the v38 bisection (8 unrelated single swaps move it).

## b18: v43 30-30 vs v40 same-hour 33-27; reverted to v40, v43 line dropped (v43-fix3 kept on file as a possible base).
Three local 79-84/140 wins (v40, v41, v43) all landed within +-3 on the ladder band. Candidate work on hold until intel sizes a
ladder screen band.

## Ladder-screen regime: local pre-filter (>= 72 vs live v40, no new solo stall vs genome idle)
Solo vs genome idle, 70 maps x 2 (v40 total 158,785):
| candidate | vs v40 /140 | solo total | new stalls vs v40 |
|---|---|---|---|
| x7-125 | 77 | 160,429 | boss-battle A and B 2000 (v40 1424 / 1498) |
| x7-149 | 76 | 159,769 | boss-battle A 2000, gold-rush B 2000, gift-wrapping B 1245 (759) |
| x8-36 | 75 | 160,427 | boss-battle B 2000, stalactites B 2000 (588) |
| x8-87 | 73 | 160,547 | same |
| x8-8 | 72 | 160,544 | same |
| x8-36f (+ m11 real-contester gate) | 71 | 158,647 | tangle A 2000 (1893) only |
| x8-87f / x8-8f | 64 / 66 | 158,746 | tangle A only |
The contest-the-capture behaviour that wins locally is the one that stalls against an idle enemy parked by its spawn; gating it
on a real contester removes the stalls and most of the h2h edge. Whether the stall matters vs moving ladder teams is a ladder question.

## Fight-cohesion edit: v40-join (pre-filter FAIL)

The edit, on x6-83 (v40): new rule 23 at priority 125, placed before r_prefight. The bot walks to join an enemy within 9 tiles when an ally is within 6 tiles of that enemy. Conditions: not at spawn, health >0.5, gems <15, and the enemy is not on its spawn. New genes: j1 `join_foe` and j2 `r_join`.

Pre-filter vs live v40 (cambc 4.0.0, runtime 671ac45b, 140 games): **64/140** (old 34/80, new 30/60). The bar is 72, so it fails. I did not run the solo check.
The unconditional join pulls units off income for fights they can't swing. The next narrower variant joins only when we'd outnumber the enemy near the foe.

**v40-join2** adds an outnumber gate: our allies within 6 of the foe, plus the joiner, must exceed the enemies within 6 of it. Result: **70/140** vs v40 (old 38/80, new 32/60). That fails the 72 bar, but by less than v40-join, so the outnumber gate helps.
**v40-join3** is v40-join2 plus a rescue-only condition: an ally within 6 of the foe must be below half health.
Result: **72/140** vs v40 (old 39/80, new 33/60), which passes the head-to-head bar.
Solo vs genome idle: total 161,435 (v40 158,785), no losses, but **2 new stalls**: 01boss-battle A at 2000 (v40 1424) and 02stalactites A at 2000 (v40 429). It fails the no-new-stall rule.
Stall checks on just those two A games (v40 re-run reproduces 1424 / 429):
| variant | boss-battle A | stalactites A |
|---|---|---|
| join3b (also skip foes within ring(enemy_spawn, 3)) | 2000 | 2000 |
| join3c (join3b + champions only) | 2000 | 2000 |
| joinoff (control: r_join returns False) | 1424 | 429 |
The rule really does fire against idle enemies. It doesn't come from reaching for foes on their spawn, or from monsters. The likely trigger is an ally hurt by camps near an idle enemy champion. I haven't diagnosed it further.
This is the same pattern as the x7/x8 table: a local head-to-head edge, paid for with stalls against a parked enemy.

The genome lead's call: let the ladder decide. v40-join3 is #7 in the ladder-screen queue (boss-battle and stalactites are known-fragile maps). The cohesion line stops unless the screen likes it.

## Death-reduction line (new direction after ladder screens s1-s8)
Every below-noise ladder candidate had +1.2 to +3.1 deaths to champions per game; the control had +0.7.
New tool, `genome/arenab/deaths.py RUNDIR CAND`: it extracts the replays (intel's extract_v2, engine/v2_0_0.wasm) and counts deaths to champions per side in a gate run.
Local deaths to champions over 140 games (cand / ref):
| run | cand | ref |
|---|---|---|
| j3 vs v40 | 1071 | 1141 |
| x7-125 vs v40 | 1151 | 1144 |
| x8-36f vs v40 | 1174 | 1194 |
| x7-125 vs v38n | 1156 | 1080 |
Local head-to-head deaths don't reproduce the ladder signal: x7-125 is level with v40 locally but +3.1 per game on the ladder.
I've asked intel for a per-death dump of the ladder deaths.

Where champions die locally, as a share of deaths to champions (v40 vs v38n; x7-125 vs v40 is similar):
- 59-64% were above 70% health 10 rounds before death. These are burst deaths, so a retreat at 30% health is too late.
- 52-56% had no ally within 6.
- 36-44% faced 2+ more enemies than allies.
- 17% carried 10+ gems.

Variants on v40 (x6-83):
- **d-out:** new rule dx1 at priority 171 (after killshot, before cashout). Retreat to spawn when off spawn with 2+ enemy champions within 6, outnumbering us (me included).
- **d-th:** r_run threshold 0.3 → 0.45 (with 15+ gems: 0.5 → 0.6).
- **d-both:** d-out plus d-th.
Results vs v40, 140 games:
| variant | wins | old / new | deaths to champions (cand / v40) |
|---|---|---|---|
| d-out | 59 | 31 / 28 | 975 / 1149 (-1.2 per game) |
| d-th | 24 | 10 / 14 | 984 / 730 |
| d-both | 27 | 15 / 12 | 913 / 687 |
- d-th is catastrophic: leaving at 45% health gives away fights v40 then wins.
- d-out does cut deaths, but it costs the head-to-head.

Softer d-out versions, now gating:
- **d-out2:** retreat only when outnumbered by 2+ (enemies ≥ allies incl. me + 2).
- **d-out3:** d-out, only when also below 70% health.
| d-out2 | **75** | 43 / 32 | 1091 / 1165 (-0.5 per game); died after <50% HP 24% vs v40 25%; captures 10926 / 10709 |
| d-out3 | 71 | 40 / 31 | 1048 / 1114 |
d-out2 passes the head-to-head bar and the deaths ≤ v40 check. Its solo check is running.

The coordinator's target (Fish study): Fish champions die 6% of the time after dropping below half health, ours 88%.
Locally, deaths.py measures about 25% for both v40 and d-out2 (any drop below 0.5 that ends in death before recovering). The Fish figure must use a different definition.
My guess at why d-th failed: its trigger, under_fire, includes awake camps, so champions abandoned camp fights at 45% and walked to spawn.
New variants, which a camp alone never triggers:
- **d-h50:** new rule dh1 at priority 171. Off spawn and below 0.5 health (shield counts), with an enemy champion within 6 or able to hit us within 2 turns → retreat to spawn.
- **d-h50r:** d-h50, plus recall below 0.5 when no threat within 5 turns and not under fire.
d-out2 solo vs genome idle: total 164,115 (v40 158,785), no losses, but 2 new stalls: 00rushbait-v2 B at 2000 (v40 1411) and 01shortcut A at 2000 (v40 1511).
| d-h50 | 40 | 23 / 17 | 1004 / 770; captures 9211 / 11602 (-21%) |
| d-h50r | 50 | 27 / 23 | |
Half-HP disengage loses badly even when champion-only: it gives up fights and farming.

Ladder death dump (intel, genome/intel/batches/deaths_v40.json; v40 b18base + s8, 903 deaths to champions).
Allies within 6 (excluding the victim) × enemies within 6 at death, top cases:
- 0 × 2: 254 (28%)
- 0 × 1: 200 (22%)
- 0 × 3: 102
- 1 × 1: 80
- 1 × 2: 70
- 1 × 3: 68

Share of ladder deaths each trigger covers (at death):
- d-out: 52%.
- d-out2: 16%.
- 65% were below 0.5 health 3 rounds before death, but the median 10 rounds before was 0.84.

New variants:
- **d-out4:** retreat when no ally is within 6 and 2+ enemies are within 6, or when outnumbered by 2+. This covers the dominant 2v1 case.
- **d-out2b / d-out4b:** d-out2 / d-out4, but enemy champions on their own spawn are not counted. In a quick check on its 2 stall games, d-out2b removes both stalls (1355 / 1511).
- **d-out4c:** d-out4b with enemies counted within 8; the outnumbered retreat walks to the nearest ally champion more than 2 away (regroup), else to spawn. This follows the genome lead's 'don't be alone near 2+ enemies'.
| d-out4b | 63 | 36 / 27 | 998 / 1052; captures 10596 / 11134 (-5%); solo: new stall 02stalactites A 2000 |
Retreating whenever a champion is alone against 2 costs captures and the head-to-head (the same trade as the cautious ladder screens).
(A batch job queued on a pgrep wait loop matched its own command line and hung for 2 hours. `full.sh` now runs one variant per job.)
| **d-out2b** | **72** | 41 / 31 | 1080 / 1139 (-0.4 per game); died after <50% HP 24% / 24%; captures 10864 / 10738 (+1%); solo total 159,056 (v40 158,785), no losses, **no new stalls** |
**d-out2b passes the full pre-filter** and goes to the genome lead for a ladder screen. Genome: cand/engine2/d-out2b.genome (v40 + rule dx1 at priority 171).
Rule dx1: off spawn, 2+ enemy champions within 6 (not on their spawn, health ≥ 0.15 or carrying gems), and at least 2 more of them than of us (me included) within 6 → retreat to spawn. A killshot still goes first.
| d-out4c | 51 | 26 / 25 | 1099 / 1024 (more deaths); captures 10433 / 11511 (-9%); solo: new stall 02stalactites A 2000 |
Regrouping toward the nearest ally is worse than retreating to spawn. It pulls champions off their farm and across the map, and they die more.
d-out2b went to the ladder as screen s11 (the genome lead reproduced it: 72/140, deaths 1585 vs 1683).

## d-out2b on the ladder (s11): 12-18 vs the fresh v40 control's 10-20
4 flips up, 2 down; gems level; deaths -0.8; captures level. Promoted to the full band b19 (genome lead / intel).

Second death edit on top of d-out2b. Tavi is the most frequent victim on the ladder: 260 of 903 deaths.
- Of those 260: 167 with no ally within 6, 97 at 1v1, 121 at ≥0.9 health 10 rounds earlier, and 213 'apart' (a fight in place).
- Tavi has 900 health (the lowest), a range-3 attack, and banks for the team.

Variants:
- **d2-tout:** for Tavi, dx1 uses d-out's trigger (2+ enemies and more of them than of us within 6). Other champions keep d-out2b's +2 margin.
- **d2-th:** adds rule dt1 at priority 171. Tavi off spawn and below 0.5 health, with an enemy champion off its spawn within 6 or able to hit it within 2 turns → retreat to spawn.
| **d2-tout** | **76** | 41 / 35 | 963 / 1151 (-1.3 per game); died after <50% HP 22% / 25%; captures 10832 / 10725 (level); solo total 160,456, no losses; new slow: 02stalactites A 2000 (v40 429) |
The stalactites A "stall" is resource exhaustion, not a retreat loop.
- Our team has 790 submitted by round 450. After that no event of any kind happens: all champions stand still with 0 gems, far from the idle enemy.
- v40 wins at 429, presumably by reaching the threshold before the map's resources run out. d2-tout ends 10 gems short.
- This is the fragile map from the v38 bisection, where 8 unrelated single swaps move it.
d2-tout goes to the genome lead with this caveat.
| d2-th | 62 | 35 / 27 | 1067 / 1025 (more); captures 10234 / 11017 (-7%); solo clean (158,632) |
A half-health disengage fails again, even for Tavi alone: it costs fights and farm. The outnumbered trigger is the edit that works.
d2-tout was confirmed by the genome lead (76/140, deaths 1476 vs 1682) and is queued for a ladder screen after b19.
| d3-ven (d2-tout + Vendetta strict) | 65 | 35 / 30 | 994 / 1136; captures 10578 / 10938 (-3%); solo stalactites A 2000 |
Vendetta is a front-line fighter: making it leave fights costs games. Next: d3-vv (d2-tout + Vesper Vale strict).
| d3-vv (d2-tout + Vesper Vale strict) | 60 | 34 / 26 | 1045 / 1117; captures 10549 / 10938 (-4%); solo stalactites A 2000 |
The strict trigger only pays for Tavi, our banker with the lowest health. Extending it to any front-liner costs games and captures. The death line is d-out2b → d2-tout.

## d-out2b LIVE as v59 (intel, b19 full band, same hour)
- Record: 31-29 vs v40's 30-30.
- Gems lost on death: -14.5 ± 6.9.
- Deaths to champions: -0.8 ± 0.6.
- Captures: held.
d-out2b is the first edit to beat v40 on the band. d2-tout cut deaths further but lost captures on the ladder, so it was not adopted.
New base for Arena B work: d-out2b (cand/engine2/d-out2b.genome).
d2-tout on the ladder screen went 12-18, level with d-out2b. Deaths were -0.8, but captures -2.5 and gems -41, so it was not adopted. Targeted retreat works; broader caution gives up farm.

## On d-out2b (live v59): Marcella slice
Marcella is the top killer in deaths_v40.json: 223 of 903.
- 176 of those are 'apart' (a fight in place); 99 victims were at ≥0.9 health 10 rounds earlier; 71 were Tavi.
- d-out2b's trigger covers 34 of Marcella's 223 kills. Counting an enemy Marcella twice raises that to 108, i.e. +74 ladder deaths covered.
- A lone champion vs a lone Marcella still doesn't trigger (weighted 2 vs us 1: the +2 margin is not met).

**d4-marc:** d-out2b with each enemy Marcella counted twice in dx1.
Gated against the live bot d-out2b; solo compared with gsolo-d-out2b. full.sh and solo.sh now take the reference bot as an argument.
| **d4-marc** vs d-out2b | **73** | 43 / 30 | 1070 / 1100; died after <50% HP 23% / 24%; captures 10636 / 10592 (level); solo 158,951 (d-out2b 159,056), no losses, no new stalls |
d4-marc passes the pre-filter. Caveat: our draft never picks Marcella, so the double count never fires in local games.
The local gate only shows the edit is harmless here (the residual is noise). Whether it helps can only be shown on the ladder, where Marcella is the top killer.

## Capture side, on d-out2b
v40's b18base ladder rows, per game:
| | us | them |
|---|---|---|
| gems captured | 895 | 743 |
| captures | 73.3 | 52.5 |
| gold-only captures | 21.4 | |
| gems per capture | 12.2 | 14.1 |
| gold earned | 5812 | 5058 |

Per gem-bearing capture we get about 17.2 gems, so the low gems-per-capture figure is an artefact of the gold-only captures; we already out-capture opponents on gems. The live question is whether gold-only captures are worth their walk plus 5 rounds.
(Rewards: wolf 4 gems, elk 15, gem cluster 7 for 120 health, gold cluster 20 gold and 0 gems.)
- **c-nogold:** camp_goal skips a gold-only cluster when a gem-paying group is at most 4 tiles farther.
- **c-gem3:** the camp walk switches to gem-only groups (GEM_BASE) after 3 shop buys instead of 6.
| c-nogold vs d-out2b | 64 | 38 / 26 | 1239 / 1038 (more); captures 10230 / 11042 (-7%); solo: 6 new slow games (boss-battle B, famine B, gift-wrapping B, harvest A, stalactites A and B) |
Gold-only captures pay: their gold buys the fights we win. Skipping them loses fights and stalls the solo games.
| c-gem3 vs d-out2b | 66 | 36 / 30 | 1046 / 1010; captures 10600 / 10859 (-2%); solo famine B 1930 (1675) |
Moving to gem groups earlier fails too. Opposite probe, **c-gem9**: stay on mixed camps until 9 buys.
| c-gem9 vs d-out2b | 71 | 41 / 30 | 1082 / 1092; captures 10774 / 10688 (level); solo clean (159,063) |
The gold → gem switch point is flat from 6 to 9 buys and falls off at 3; skipping gold clusters is clearly bad.
d-out2b's camp targeting is at a local optimum on this axis. Capture-side line closed: no candidate.

## Gems lost on death, on d-out2b: conditional threat bank
History: v34 cash3 (an earlier cash-out in general) and x7-125 (a later cash-out) both failed on the band. The trigger must be conditional only.
New rule db1, `r_threatbank(n)`, at priority 155 (after killshot, cashout and pass-through bank, before fight 150). It walks to bank (rule 11) when all of these hold:
- off spawn, carrying n+ gems, and no altar next to us (adjacent banking keeps its own rules);
- an enemy champion off its spawn within 8;
- `altar_eta() < threat_eta()`: the nearest usable altar is reachable before that enemy can hit us.
Variants: **b-tb15** (n = 15) and **b-tb10** (n = 10).
deaths.py now also reports gems lost on death to champions (carried the round before death). c-gem9 vs d-out2b: 6972 / 6929, i.e. about 49 per game locally.
| b-tb15 vs d-out2b | 72 | 42 / 30 | 1055 / 1049; captures 10603 / 10583; **gems lost on death 7124 / 6345 (+5.6 per game)**; solo clean |
b-tb15 passes the head-to-head bar but repeats the v34 cash3 failure: more gems are lost on death, because carriers walk to bank with an enemy near. Not sent.
**b-near:** n = 10, and only when the altar is at most 2 turns away (and before the threat).
| b-near vs d-out2b | 71 | 41 / 30 | 1096 / 1077; captures 10536 / 10766 (-2%); gems lost on death 6666 / 6670 (level); solo clean |
Bank-under-threat line closed. The loose trigger (b-tb15) raises gems lost on death; the tight one (b-near) changes nothing.
Gems lost on death are not cut by bank timing on top of d-out2b; d-out2b's retreat already takes the carrier out.

## Draft and shop on d-out2b (loosened pre-filter for ladder-only effects: ≥68/140 vs d-out2b, 0 crashes, no new solo stall, captures level)
Shop order on d-out2b: Treasure Str to its emblem (18/19), Jungle HP to its emblem (28/29), Durability HP emblem (16/17), then bruiser Str (36).
- **s-hunt3:** Hunter Str to its emblem (60/61, +50 kill gold) as the 3rd emblem, then as before.
- **s-skirm3:** Skirmish Str to its emblem (66/67, x1.05 vs champions) as the 3rd emblem, then as before.
(v39a probes: Hunter and Skirmish lost as a 1st emblem or in place of Jungle. Here Treasure and Jungle stay first.)
**s13, d4-marc on the ladder:** 10-20 vs a clean d-out2b control's 12-18. Deaths to Marcella fell 109 → 71, but total deaths to champions only 329 → 318: the deaths moved to other killers. Reverted to d-out2b (v61).
Lesson: retreating from one specific killer hands the kill to another.
| **s-hunt3** vs d-out2b | **70** | 36 / 34 | 1048 / 1110; captures 10685 / 10579 (level); gems lost on death 6309 / 6723; solo 158,738, no losses; slow game: 00stampede A 2000 (d-out2b 1763) |
The stampede A game is slower play, not a freeze. s-hunt3 submits 960 by round 2000 vs d-out2b's 1120 at 1763; it is still attacking, capturing and dying (63 respawns after round 1500 vs 26).
Passes the loosened bar with that caveat; sent to the genome lead.
| **s-skirm3** vs d-out2b | **72** | 41 / 31 | 1062 / 1102; captures 10811 / 10626 (+1.7%); gems lost on death 6698 / 6639 (level); solo 158,738, the same slow 00stampede A game |
The solo results of s-skirm3 and s-hunt3 are identical (same total, same stampede game). The slowdown comes from delaying the Durability emblem by one slot, not from the family bought.
Both pass the loosened bar; sent to the genome lead.
