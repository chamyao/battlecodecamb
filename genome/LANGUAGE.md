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
- Keeps: `Num`, `Bool`, `Tile`, `Tiles`, `Field`. Use a Tiles/Field keep set in `update()` to compute an expensive set or distance field once per turn instead of once per pass (zero-argument genes are recomputed every pass of the loop).
- Every gene has `@gene(id, description, parents=[...])`. IDs survive inheritance; a duplicated gene gets a new ID.
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
- `walk_nearest(cand, from, walls)`: the engine's nearest-by-walk (ties row-major); invalid if none is reachable.
- `type_spawns(k)`, `spawn_type(t)`, `spawn_group(t)`, `camp_spawn(u)`, `camp_base_*(k)`: static map and camp design data (-1 off a spawn tile).
- `is_awake(u)`: camp life state; `group_reward(g)`: the group is cleared and waiting for capture.
- `set_priority(p)`: turn order for the next round (update() only). `rand(n)`: uniform integer in [0, n) from the instance's own generator.
