# Engine 2.0.0 (cambc 4.0.0): what changed

Compiled by intel on 2026-10-30, from cambc 4.0.0 (pip) in a scratch venv. Ladder games have run on engine 2.0.0 since at least 2026-10-30T01:40Z: our last 40 ranked games and all 50 b13 games.

Sources and confidence:
- **Read from the engine:** a probe bot printed `cambc.constants`, `_cambc.camp_design(k)` and `_cambc.item_info(i)` from inside a 2.0.0 game.
- **From the SDK:** `sdk/cpp/cambc.h` and `sdk/python/_cambc.pyi`.
- **Inferred:** passive effects, from engine symbol names in the cambc binary (`Engine::detail::_ItemPassiveDesigns::*`) and the passive magnitudes. Each one is marked *inferred* below.
- The online handbook is behind login (the site is a single-page app on S3; deep links return AccessDenied), so no official rule text was available.

## Unchanged

- **Settings:**

  | setting | value |
  |---|---|
  | CAPTURE_TIME | 5 |
  | CAMP_SLEEP_TIME | 2 |
  | RESPAWN_TIME | 60 |
  | RECALL_TIME | 5 |
  | tribute duration | 0.1 × gems (min 1, range 1) |
  | MAX_ROUNDS | 2000 |
  | WINNING_GEMS | 1000 |
  | KILL_GOLD | 100 |
  | ASSIST_GOLD | 0 |
  | PASSIVE_GOLD | 0 |
  | SPAWN_HEALING | 1.0 (full) |
  | ward | 1 active, cooldown 10, vision 6, placement radius 2 |
  | ALTAR_LOCK_HITS | 5 |
  | TP_CRYSTAL_TIME | 3 |
  | SHARED_MEMORY_BYTES | 8 |
  | DRAFT_MEMORY_BYTES | 1024 |

  SHARED_MEMORY_BYTES = 8 matters: genomes may only use shared slots 0-7. The rejected rendezvous child used slots 20-21; none of the live genomes do. Live genomes use slot 7 (lock).
- **Camps** (camp_design 0-5) are the same as the v1 table:

  | camp | health | strength | range |
  |---|---|---|---|
  | wolf | 1350 | 20 | 3 |
  | elk | 2400 | 60 | 4 |
  | gem cluster | 120 | 0 | 3 |
  | gold cluster | 120 | 0 | 3 |
  | monolith | 20000 | 200 | 5 |
  | golem | 5000 | 120 | 4 |
- **Items 0-41 keep their ids and stats.** These are the families Monster, Power, Durability, Treasure, Jungle, Home and Bruiser. Each family has a shard (30 gold, +1 stat) and an emblem (5 shards).
  - Emblems give +5 to their stat, or +6 for Power.
  - Bruiser emblems give 5/1/1.
  - Passive magnitudes:

    | family | magnitude |
    |---|---|
    | monster | 0.15 |
    | durability | 0.10 |
    | treasure | 0.10 |
    | jungle | 0.30 |
    | home | 0.5 |

  So the genome item constants (18/19 Treasure Str, 28/29 Jungle Hp, 36 Bruiser Str) still point at the same items.
- **Changed passive magnitudes** (v1 values from docs/GameRules.md; Arena B found the same in its SDK diff, genome/arenab 64f3b615):
  - **Treasure: 20% → 10% more gold.** Vesper Vale + Treasure is now 33% + 10% = 43%, down from 53%. This weakens the v29 emblem plan (Treasure Str first).
  - **Monster: 10% → 15% more damage to camps.**
  - Durability (10%), Jungle (30%) and Home (50%) are unchanged.

## New

**8 new item families, ids 42-83.** Shards are ids 42 + 6f + 2s, emblems are +1, with stat s = 0 str, 1 focus, 2 health.

| family | ids | shard → emblem | emblem stats | passive (id, magnitude) | effect (*inferred* from engine hook names) |
|---|---|---|---|---|---|
| Tribute | 42-47 | 30 g × 5 | +5 | 6, 0.33 | *inferred*: tribute-related; most likely a 33% shorter tribute channel (no separate hook name found) |
| Capture | 48-53 | 30 g × 5 | +5 | 7, 3.0 | *inferred*: `CaptureDuration`, a faster capture (3 rounds off the 5-round timer?) |
| Prospector | 54-59 | 30 g × 5 | +5 | 8, 0.25 | *inferred*: `ClusterReward`, +25% reward from gem/gold clusters |
| Hunter | 60-65 | 30 g × 5 | +5 | 9, 50.0 | *inferred*: `KillReward`, +50 gold per champion kill |
| Skirmish | 66-71 | 30 g × 5 | +5 | 10, 0.05 | *inferred*: `PlayerDamage`, +5% damage to champions |
| Greed | 72-77 | 30 g × **25** | **+35** (750 g) | none | a big stat emblem: 25 shards for +35 |
| Collectors | 78-83 | 30 g × 5 | +5 | 11, 0.01 | *inferred*: `CollectorsDamage`, +1% damage per unit of something collected (probably per carried gem) |

(The table has 7 families with passives plus Greed, which has none.)

- **Champion rebalance.** Read from the v2.0.0 wasm with analysis/designs.js (`Game_API_Champion_Design`). The full dump is tools/extract_v2/design_v2_0_0.json; diffed against analysis/design_v1_0_3.json. Settings and camps: no change. Champions, v1 → v2:

  | champion | change |
  |---|---|
  | Vesper Vale | base strength 55 → 45 |
  | Issac | base strength 40 → 45 |
  | Varg | base strength 40 → 45 |
  | Ryth | strength growth 5 → 4.5 |
  | Marcella | strength growth 5 → 4.5, focus growth 15 → 14 |
  | Heart of Ruin | strength growth 3.5 → 3.0, focus growth 12 → 10 |
  | Cassi | base focus 70 → 100 |
  | Willow | base focus 120 → 140 |
  | Stellar | focus growth 7 → 8.5 |
  | Prism | health growth 60 → 65 |
  | Ren | cc (ability 1) modifier 0.75 → 1.1 (cooldown 8, range 4, duration 1 unchanged) |
  | Tavi | cc (ability 2) modifier 1.4 → 1.6 |

  Vendetta: no change. Vesper Vale loses the most: 10 base strength, and the Treasure passive drops from 20% to 10% (see Unchanged).
- New import: `camp_group_capture_state(group)` returns a `timer` and a `state` (CampGroupCaptureType): 0 no capture available, 1 ally capturing, 2 contested, 3 enemy capturing, 4 capture available. v1 rules (docs/GameRules.md "Camps & capture"): a 5-round timer, extra allies do not speed it up, an empty or contested region resets it. Whether a contested capture still resets in 2.0.0 has not been measured. The separate CONTESTED state suggests it may now pause; this is untested.
- New CLI: `cambc submissions list|activate`.
  - Currently "Mode: follow newest ready version; Live: 38".
  - This shows which version is live, which answers the b10 question. Note v35 shows "cancelled": v36 replaced it two minutes later.

## Map pool

- 70 maps: the old 40 plus 30 new.
  - 00: anvil, breadcrumbs, crater, dunes, galaxy, oasis, quarry, ribs, the-line, vault.
  - 02: arena, crossing, cuts, famine, fields, geodes, gift-wrapping, guardians, harvest, stalactites, tangle, the-pack, the-pond, treasure-box, uncharted-lands.
  - adgato-gemcombat1-5.
- The ladder uses it: 19 of our last 40 ranked games were on new maps.
- Our sim gates (`maps/*.map26a`, 40 maps) and batch plans (b1's 40 maps) do not cover the 30 new maps.

## Tooling status

- **genome_eval / sim:** engine 1.0.3 rules and the 40-map pool. Item ids 42-83 don't exist there, and genomes can't use them until sim/include/cbs and the genome runtime learn them.
- **Replay extractor** (analysis/extract.js): ported to 2.0.0 in genome/intel/tools/extract_v2 (drop-in engine.js and analyse.py for analysis/sprint1, plus the v2_0_0 wasm from the cambc 4.0.0 cache). The v2 snapshot is 42840 bytes (v1 40152): 84 items, +168 bytes per champion, +2688 bytes before camps. Validated on all 50 b13 replays against the official summaries.
- Meanwhile, the official summaries (`summaries/*.json`) give per-team gems, per-champion kills/deaths/items/gold, and bot faults. Note that `deaths`/`kills` are strings there.
- **cambc 3.0.5** (old engine) in this container; 4.0.0 is in a scratch venv.

## Implications

1. All gates measured before 2026-10-30 are 1.0.3 measurements: sim, arena, real cambc 3.0.5. They need re-checking on 2.0.0.
2. The new families fit our loss profile:
   - Hunter (+50 gold per kill) and Skirmish (+5% vs champions) reward the fight-heavy band. Expect opponents to adopt them.
   - Capture and Prospector speed up farming.
   - Greed is a late gold sink.
   - Shop gene a11 is a natural place to try them once the sim knows the items.
