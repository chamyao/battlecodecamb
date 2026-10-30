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
