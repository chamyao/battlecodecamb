# Genome fuel: how the simulator prices a genome, and how it was calibrated

Genomes run on the genome runtime (`runtime/genome_rt.h`), not the policy interpreter, so the
interpreter's measured block prices (`docs/FUEL.md`) do not apply. In the simulator a genome pays:
- engine calls, through `cbs::Api` with `PriceTable::bot_wrapper()` (as the policy bot);
- its own operations, `F(n)` in the generated code, at `GENOME_OP_FUEL` (1) each: compiled
  arithmetic is nearly free in the bot (18 if-compares cost 11, constant loops fold away); plus
  `GENOME_LOOP_FUEL` (8) per loop iteration (`FL`; `FLU` adds 11 for a loop over units) and `FX(n)`
  for a memoised gene's hit (28 for a scalar, 65 for Tiles / Field: the copy out);
- the runtime's own work beyond those calls, `Ctx::extra()` in each primitive (simulator only),
  fitted below. Without it the simulator undercharged genomes ~6.7x (Oct 24).

## Calibration (Oct 24, cambc 3.0.5)

`examples/calib.genome` runs one probe gene per primitive per turn (in rotation). Built with
`GENOME_PROF`, each gene's inclusive fuel is logged (`@@GENE`), in the real bot (`bot/sync.sh` +
`cambc run`) and in the simulator. `tools/calib_compare.py` prints real/sim per probe for
00ambush, 01big-world (100x100, 169 chunks) and 00lanes (90x30, 48 chunks). The extra charges are a
constant plus a term in map chunks, set size or units, e.g.:

| primitive | real fuel | extra charged in the sim |
| --- | --- | --- |
| tile-set union / intersection / minus | 520-1170 | 224 + 3.1 x chunks (minus 4.0) |
| `near` | 420-670 | 122 + 1.03 x chunks |
| `size` | 136-262 | 80 + 1.0 x chunks |
| `field` | 2.5k (48 ch) - 35k (169 ch) | search 9 + (16 + expansions) x chunks, exact; + wrapper 527 + 8.1 x chunks |
| `field_avoid` | as `field` | search as `field` (+ 2 with a stop set); wrapper 528 + 7.1 x chunks |
| iterating a tile set | ~66-91 per tile | 970 + chunks + 81 x tiles |
| `nearest` | ~52 per tile | 120 + 52 x tiles |
| `camps()` | 640-2000 | 600 + 80 x visible camps |
| `visible`, `contains` | ~230 / 55-66 | 150 / 52 |
| `vision`, `ally_tiles`, `enemy_tiles`, `camp_tiles` | 262 (48 ch) - 515 (169 ch) | beyond the Api's price: 100 + 2.1 x chunks (vision), 148 + 1.1 x chunks (occupancy) |
| `walk_nearest` | 1.9k-7k (the bot's memoised nearest-by-walk) | none: the Api prices the bot's memo; sim 0.84-1.38x real per call |
| `type_spawns` | ~100-120 | 100 |
| `spawn_type`, `spawn_group` | ~55-65; first call fills a W x H table, ~3 per tile | 55; 2700 + 3 x W x H once |
| `is_awake`, `camp_spawn` | 37 / 29 | 16 / 17 |
| `camp_base_health/strength` | ~15 | 6 |
| `group_reward`, `group_respawning` | 47 | 26 |
| `alive`; `can_move`, `can_attack`, `channeling` | 12; ~24 | 4; 11 |
| `rand` | 20 | 12 |
| `consider(kind)` | 27 per call (once per kind per pass) | ops only (sim 35) |
| `me()` (cached), `dist`, `at` (field read) | ~20 / ~30 / ~70 | 18 / 30 / 70 |
| cached `enemies()` / `allies()` / `camps()` | ~27 | 27 |
| `camps()` (fetch) | 212 + 3 x chunks + 510 per camp (with `enemies()`) | 174 + 3 x chunks + 253 per camp |
| listing the legal options | ~55-60 per tile option, ~100 per unit option, fixed parts per section | by section (below) |
| scoring an option (the loop) | ~30 beyond the gene's own work | 30 per option scored |
| a champion's first turn (start-up) | 35k (41x30) - 131k (100x100) | 17444 + 3.13 x W x H + 35.5 x holes + 376 x camps |

Fields (re-fit Oct 24 after a5bbfcf, `examples/calib2.genome`): the bot runs the host search into
its own buffer, so the simulator now prices the search on its own expansion count instead of the policy
bot's distance-field memo; per call the profiled search matches the host to the fuel
(`@@FIELD` lines: real = 28 + 16 x chunks + expansions x chunks over 1,200 searches on three maps, of
which 19 is the profiler's own `fuel_remaining`), and whole probes to 0-2%. `field_avoid`'s stop set
follows the host's ComputeTo: the search runs until *every* reachable stop tile is reached (it used
to stop at the first one in the simulator, so a genome with a stop set of several tiles played
differently in the bot; one stop tile, as v23 uses, is unaffected).

Whole games, genome vs starter (`tools/real_fuel.sh` for cambc), mean fuel per turn real/sim:

| genome | 00ambush | 01big-world | 00lanes | 00rows |
| --- | --- | --- | --- | --- |
| starter | 34.3k / 38.2k | 36.5k / 40.9k | 36.0k / 36.4k | 27.0k / 24.6k |
| farmer | 41.9k / 43.6k | 42.7k / 39.6k | 30.0k / 29.6k | 29.3k / 27.4k |

Ratios 0.89-1.10; turns at the 100k cap are of the same order (the sim slightly more). Re-run the
calibration whenever `runtime/genome_rt.h` or `bot/bot_api.cpp` changes, and check new primitives
with a probe before relying on them.

## Listing the options (task 3, Oct 24)

The bot used to pay ~160-170 fuel per listed option (default-constructing an Option, copying it into
a vector, a non-inlined terrain lookup per tile): a ground-target cast over 81 tiles cost ~13.7k,
wards ~4k per pass. The listing is now written in place into a reused buffer (`OptionList`, 24-byte
`Option`, unit targets as an index into the pass's cached unit lists instead of a copied Unit),
scans tiles row by row over the terrain bytes, tests occupancy per tile on the three SDK masks (no
board unions), walks a precomputed shop list, and fetches only the consumables for the lock check.
Same options, same order (identical 80-game results at 100x fuel for starter, farmer, fartest, v23).
Real fuel per pass of an idle champion: 23.1k -> ~9-12k on 01big-world (cast 13.7k -> 5.4k,
ward 4.0k -> 1.5k, move 2.4k -> 1.8k); an idle turn 20.3k -> 11.8k.

Simulator price per listing section (`@@L` profile lines: fuel, options, scanned items and
activations per section, fitted on idle / starter / farmer in cambc on two maps), beyond the Api's
own charges: start 40 (alive); shop 10 + 24 per shop item + 55 per buy option; move 421 + 1.24 x
chunks + 70 per move option; attack 97 per option (the unit lists are priced in `camps()` /
`enemies()`); cast 248 per slot + 56 per ground tile scanned + 75 per unit scanned; ward 168 + 17.8
per tile + 40 per option; recall 11 + 50; tributes 59 per altar; a dead champion's turn 250.
Idle genome, whole games: real / sim 11.0k / 11.2k (00ambush), 11.8k / 12.0k (01big-world),
10.1k / 10.2k (00lanes), 9.1k / 9.2k (00rows), and within 3% on four more maps.

How the scoring was priced: "score variants" (genomes that list and score every option but never
act, so the game state is the same in the bot and the simulator) differ from the idle genome only in
the score body; the per-option difference against the idle genome (6 champions per map) isolates one
construct at a time (`me()`, `dist`, `at`, memo hits, loops over units, 18 compares, arithmetic).

## Bot-side costs worth knowing (what the search pays for)

- A single host bitboard bit test or set costs ~120-170 fuel in the bot. The runtime keeps static
  terrain as plain bytes and caches each camp group's tiles; dynamic sets still pay it.
- A distance field costs 9 + (16 + expansions) x chunks in the host, plus ~530 + 8 x chunks around it.
- A memoised gene's result is copied out on every call (~28 fuel; ~65 for Tiles or Field), and a
  field read costs ~70: read a field once into a local where it is used many times.
- Distance fields cost ~100 fuel per map chunk. A genome that rebuilds its goals and field on every
  pass of the loop pays that each pass (the starter genome: ~2.5 passes, ~33k per turn).
- Row-major iteration over a host bitboard uses an insertion sort (quadratic per chunk row); the
  runtime uses a linear counting sort instead, and `nearest` breaks ties by (y, x) so it can take
  the host's cheap order.
