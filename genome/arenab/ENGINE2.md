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
