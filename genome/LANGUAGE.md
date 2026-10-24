# Gene language reference

Generated from `genome/lang.py` (`python3 -m genome.reference > genome/LANGUAGE.md`). Design: `docs/GENOME.md`.

## A genome file

Python syntax, restricted to a typed subset. Top level: keep declarations and genes only.

```python
BAG: Num = 20                      # keep: persistent per bot instance; only update() assigns it
GOALS: Field = None                # keeps: Num, Bool, Tile (starts invalid), Tiles and Field (start empty)

@gene("g7", "danger at a tile", parents=["g2"])
def danger_at(t: Tile) -> Num:
    return sum(u.strength * u.health_frac for u in enemies() if dist(u.pos, t) <= 5)
```

- Entry genes: `score(o: Option) -> Num` (required): the value of doing option `o` now; the fixed loop does the best option while its score is > 0 (the draft always picks). `update() -> None` (optional): runs at the start of each turn; the only gene that may assign keeps or call `write_shared` / `set_priority`. `consider(kind: Num) -> Bool` (optional): option kinds it rejects are neither listed nor scored this pass. `reserve() -> Num` (optional, default 15000): read once per turn after `update()`; the loop starts no pass after the first with less fuel left than this (a turn that runs out of fuel is suspended and the next turn is lost).
- `after() -> None` (optional entry gene): runs at the end of each turn, after the loop's actions, with fresh observations. Like `update()`, it may assign keeps and call `write_shared` / `set_priority`. `acted(kind)` and `acted_tile(kind)` tell it what the loop did this turn (e.g. announce the camp it attacked, so allies acting later in the round see it). Shared bytes written in one gene and read in another are dependency edges, as calls are.
- Keeps: `Num`, `Bool`, `Tile`, `Tiles`, `Field`. Use a Tiles/Field keep set in `update()` to compute an expensive set or distance field once per turn instead of once per pass (zero-argument genes are recomputed every pass of the loop).
- Every gene has `@gene(id, description, parents=[...])`. IDs survive inheritance; a duplicated gene gets a new ID.
  IDs and parent IDs are 1-64 of `A-Z a-z 0-9 _ . -`; a description is one plain line (no control, format or
  line-separator characters, no backslash), since both are emitted into C++ `//` comments.
- Statements: assignment (function-scoped locals, type fixed at first assignment), `+= -= *= /=`, `if/elif/else`, `for x in S` (S: Units, Tiles or `range(n)`), `return`.
- Expressions: arithmetic on Num (`/` by 0 gives 0), comparisons, `and/or/not`, `a if c else b`, `t in S` (Tile in Tiles), Tiles `| & -`, fields (`u.pos`), calls to genes and primitives.
- Reductions: `sum(e for x in S if c)`, `count(c for x in S)`, `any(...)`, `all(...)`, `max((e for x in S), default=d)` (Python needs the generator in parentheses next to `default=`), `min(...)`, `max(a, b)`, `min(a, b)`; `best(S, lambda x: score)` returns the element with the highest score (an invalid Unit/Tile if S is empty: test with `exists(u)` / `valid(t)`).
- No recursion, no other loops: every gene finishes. Zero-argument genes are computed once per pass of the loop.
- Fuel: each own operation is charged (placeholder price until calibrated); primitives that call the engine are charged as the engine call. A turn over budget is suspended, as in the real game.

## Types

`Num` `Bool` `Tile` `Unit` `Units` `Tiles` `Option` `Field`

## Fields

- `Unit`: `pos` (Tile), `health` (Num), `max_health` (Num), `strength` (Num), `focus` (Num), `attack_range` (Num), `move_speed` (Num), `type` (Num), `is_enemy` (Bool), `is_champion` (Bool), `is_camp` (Bool), `health_frac` (Num)
- `Tile`: `x` (Num), `y` (Num)
- `Option`: `kind` (Num), `unit` (Unit), `tile` (Tile), `slot` (Num), `item` (Num), `champ` (Num), `count` (Num)

## Primitives

| primitive | returns |
| --- | --- |
| `me()` | Unit |
| `gems()` | Num |
| `gold()` | Num |
| `round()` | Num |
| `fuel()` | Num |
| `can_shop()` | Bool |
| `alive()` | Bool |
| `can_move()` | Bool |
| `can_attack()` | Bool |
| `channeling()` | Bool |
| `team_gems()` | Num |
| `enemy_gems()` | Num |
| `enemies()` | Units |
| `allies()` | Units |
| `camps()` | Units |
| `unit_gems(Unit)` | Num |
| `is_recalling(Unit)` | Bool |
| `is_tributing(Unit)` | Bool |
| `camp_group(Unit)` | Num |
| `is_awake(Unit)` | Bool |
| `camp_spawn(Unit)` | Tile |
| `group_gems(Num)` | Num |
| `group_gold(Num)` | Num |
| `group_respawning(Num)` | Bool |
| `group_reward(Num)` | Bool |
| `group_tiles(Num)` | Tiles |
| `num_groups()` | Num |
| `visible(Tile)` | Bool |
| `vision()` | Tiles |
| `ally_tiles()` | Tiles |
| `enemy_tiles()` | Tiles |
| `camp_tiles()` | Tiles |
| `altars()` | Tiles |
| `walls()` | Tiles |
| `bushes()` | Tiles |
| `holes()` | Tiles |
| `my_spawn()` | Tiles |
| `enemy_spawn()` | Tiles |
| `camp_spawns()` | Tiles |
| `type_spawns(Num)` | Tiles |
| `locked_altars()` | Tiles |
| `spawn_type(Tile)` | Num |
| `spawn_group(Tile)` | Num |
| `camp_base_health(Num)` | Num |
| `camp_base_strength(Num)` | Num |
| `width()` | Num |
| `height()` | Num |
| `tile(Num, Num)` | Tile |
| `dist(Tile, Tile)` | Num |
| `near(Tile, Num)` | Tiles |
| `nearest(Tiles, Tile)` | Tile |
| `size(Tiles)` | Num |
| `count_units(Units)` | Num |
| `valid(Tile)` | Bool |
| `exists(Unit)` | Bool |
| `field(Tiles)` | Field |
| `field_avoid(Tiles, Tiles, Tiles)` | Field |
| `box_field(Tiles, Tiles)` | Field |
| `dash_field(Tile, Tiles)` | Field |
| `wfield(Tiles, Tiles, Tiles, Num)` | Field |
| `path_step(Tile, Tile, Tiles, Num)` | Tile |
| `path_len(Tile, Tile, Tiles, Num)` | Num |
| `territory(Tiles, Tiles, Tiles)` | Tiles |
| `attack_damage(Unit, Unit)` | Num |
| `cast_damage(Unit, Num, Unit)` | Num |
| `shield(Unit)` | Num |
| `hits_to_kill(Unit, Unit)` | Num |
| `at(Field, Tile)` | Num |
| `walk_nearest(Tiles, Tile, Tiles)` | Tile |
| `slot_kind(Num)` | Num |
| `slot_ready(Num)` | Bool |
| `slot_range(Num)` | Num |
| `slot_radius(Num)` | Num |
| `slot_targets(Num)` | Num |
| `slot_moveless(Num)` | Bool |
| `item_cost(Num)` | Num |
| `item_strength(Num)` | Num |
| `item_focus(Num)` | Num |
| `item_health(Num)` | Num |
| `item_passive(Num)` | Num |
| `items_owned(Num)` | Num |
| `has_lock()` | Bool |
| `read_shared(Num)` | Num |
| `write_shared(Num, Num)` | None |
| `set_priority(Num)` | None |
| `acted(Num)` | Bool |
| `acted_tile(Num)` | Tile |
| `picked_by_us(Num)` | Bool |
| `picked_by_them(Num)` | Bool |
| `abs(Num)` | Num |
| `floor(Num)` | Num |
| `sqrt(Num)` | Num |
| `rand(Num)` | Num |

## Constants (Num)

`PICK`, `MOVE`, `ATTACK`, `CAST`, `WARD`, `BUY`, `RECALL`, `TRIBUTE`, `CANCEL`, `LOCK`, `BUY_LOCK`, `RYTH`, `VESPER_VALE`, `VENDETTA`, `CASSI`, `ISSAC`, `STELLAR`, `PRISM`, `MARCELLA`, `WILLOW`, `REN`, `VARG`, `TAVI`, `HEART_OF_RUIN`, `WOLF`, `ELK`, `GEM_CLUSTER`, `GOLD_CLUSTER`, `MONOLITH`, `GOLEM`, `AB_NONE`, `AB_RESET`, `AB_DAMAGE`, `AB_AOE`, `AB_CC`, `AB_HEAL`, `AB_DASH`, `AB_SHIELD`, `P_NONE`, `P_MONSTER`, `P_DURABILITY`, `P_TREASURE`, `P_JUNGLE`, `P_HOME`, `T_CAMPS`, `T_ENEMIES`, `T_ALLIES`, `T_SELF`, `T_GROUND`, `INF`

Option kinds: PICK (o.champ), MOVE (o.tile), ATTACK (o.unit), CAST (o.slot + o.unit or o.tile), WARD (o.tile), BUY (o.item, o.count: 1, 2, 4, ... units up to what we can pay), BUY_LOCK, RECALL, TRIBUTE (o.tile = altar; at an enemy-locked altar it hits the lock), CANCEL (a running recall/tribute), LOCK (o.tile = altar).

Notes on the newer primitives (SDK reads and generic operations only):
- `vision()`, `ally_tiles()`, `enemy_tiles()`, `camp_tiles()`: the SDK's vision and occupancy masks (one engine call each). `ally_tiles()` includes me.
- `field_avoid(goals, walls, stop)`: the engine distance field to `goals` over tiles not in `walls`; the search ends after the layer by which every reachable `stop` tile has been reached (the host's ComputeTo; one stop tile: the first layer that reaches it; empty `stop`: whole map), farther tiles read unreachable (1e9).
- `box_field(goals, walls)`: the walking field to `goals` over tiles not in `walls`, through the engine field memo the policy bot's walking uses (cheap on later turns while the goals stay the same); readable only on my 3 x 3 box and up to my own distance (enough to choose a step), unreachable (1e9) everywhere else.
- `dash_field(goal, walls)`: the walking field to one `goal` tile through the engine field memo the policy bot's dash uses (root = the goal, dests = my 5 x 5 box); only the box tiles nearest to the goal read their distance, every other tile unreachable (1e9): for choosing a dash landing. ~4-6k per call.
- `wfield(goals, walls, slow, k)`: a weighted walking field computed in our own code (Dijkstra, bucket queue): stepping onto a tile costs 1, or 1 + k on a `slow` tile (k clamped to 0..8); `walls` cannot be entered (goal tiles can); distances above 65534 read 1e9. Dear: a whole 100x100 map costs ~4.5M fuel in the bot (~45 turns of budget), 90x30 ~1.3M.
- `path_step(from, to, walls, budget)` / `path_len(...)`: A* from `from` to `to` over tiles not in `walls` (`to` allowed), expanding at most `budget` tiles: the first step (invalid if not found) / the length (1e9). About 1.4k + 380 per tile expanded in the bot.
- `territory(mine, theirs, walls)`: tiles strictly nearer by walking to `mine` than to `theirs` (empty `theirs`: every tile reachable from `mine`), over tiles not in `walls` (sources allowed): two engine fields and a compare in our code, ~300k fuel on 100x100 (~80k on 90x30).
- Fights, exact from the game's formulas and the units' host data (emblem passives from their items, shields from their buffs), in the engine's float order: `attack_damage(a, b)` what one basic attack of `a` takes off `b` (strength, missing-health passive, Monster emblem and the camp multiplier against camps, then Durability / Jungle; before shields); `cast_damage(a, slot, b)` the same for a damage / stun / area ability (modifier x focus); `shield(u)` the shield left on a champion; `hits_to_kill(a, b)` basic attacks of `a` that kill `b` from now (shields first; 1e9 if none hurts). A champion's items and buffs are read once per pass (~0.9k); calls ~0.1-0.25k after that.
- `walk_nearest(cand, from, walls)`: the engine's nearest-by-walk (ties row-major); invalid if none is reachable.
- `type_spawns(k)`, `spawn_type(t)`, `spawn_group(t)`, `camp_spawn(u)`, `camp_base_*(k)`: static map and camp design data (-1 off a spawn tile).
- `is_awake(u)`: camp life state; `group_reward(g)`: the group is cleared and waiting for capture.
- `set_priority(p)`: turn order for the next round (update() only). `rand(n)`: uniform integer in [0, n) from the instance's own generator.
