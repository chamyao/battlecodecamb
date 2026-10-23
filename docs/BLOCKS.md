# Building blocks (v0, to iterate)

Each block is one compute move with a fuel price (to be measured). Split to the
smallest manageable unit. SDK call(s) in brackets. "Settings" are the few
fixed options a block comes in (e.g. depth); each setting is its own move.

## Read: static map (known from turn one and in the draft)
1. Map size [`game_map.width/height`]
2. Walls [`game_map.walls`]
3. Holes [`game_map.holes`]
4. Bushes [`game_map.bushes`]
5. Altars [`game_map.altars`]
6. Spawn region, own or enemy [`game_map.spawn_region`]
7. Camp groups: positions and types [`game_map.camp_groups`]
8. Symmetry [`game_map.symmetry`]

## Read: self
9. Position [`position`]
10. Health / max health [`health`, `max_health`]
11. Gems, gold [`gem_count`, `gold_count`]
12. Stats: strength, focus [`strength`, `focus`]
13. Ability cooldowns / readiness [`abilities`, `can_cast`]
14. Allowances left: move, attack, buy [`can_move`, `can_attack`, `can_buy`]
15. Channel state: recalling, tributing, teleporting, time left
16. Buffs/restrictions: stun, shield [`restrictions`, `state`]
17. Ward charge [`ward_cooldown`]
18. Inventory: items, consumables [`item_count`, `consumables`]

## Read: world (vision-limited)
19. Visible champions, ally/enemy [`vision.champions`]
20. Visible camps and state (alive/asleep/awake, health) [`vision.camps`]
21. Camp group state / respawn timer, if in vision [`CampGroup.state`]
22. Visible wards, altar locks, teleports [`vision.wards/altar_locks/teleports`]
23. Is tile in vision [`vision.in_vision`]
24. Round number, team tributed gems [`round_number`, `global_submitted_gems`]

## Read: control and memory
25. Fuel remaining [`fuel_remaining`]
26. Shared memory, one byte or range [`SharedMemoryBuffer.read`]
27. Draft memory, one byte or range [`DraftMemoryBuffer`]
28. Champion type, team [`champion_name`, `team`, `is_draft`]

## Compute
29. Distance field to target set (BFS) [`DistanceField.compute`]
    settings: full / capped expansion count
30. Next move along a distance field [`next_move_from`]
31. A* to a tile, settings: depth / node cap
32. Walkable mask [walls | holes | altars | occupied, enemy spawn]
33. Visible tiles from a position, e.g. to plan wards [`visible_tiles_from`]
34. Fight calculator vs a camp or champion: turns to kill, damage taken
35. Lookahead search over own moves, settings: depth 1/2/3, beam width
36. Belief update: where an unseen enemy could be (bitboard expansion)
37. Camp value: gems, gold, respawn, distance, danger -> score
38. Bitboard ops: and/or/not, count, nearest set tile

## Write: memory
39. Shared memory write, one byte or range
40. Draft memory write (draft only)
41. Private memory: store / load a value

## Act: board
42. Move one step / move towards [`move`, `move_towards`]
43. Basic attack target [`attack`]
44. Cast slot 0 / slot 1 at target, tile or self
45. Place ward [`place_ward`]
46. Recall / cancel recall
47. Tribute / cancel tribute [`submit_gems`, `cancel_submit_gems`]
48. Buy shard of stat S / consumable C [`buy`]
49. Use consumable: altar lock, teleport crystal
50. Sell (Tavi only) [`sell`]

## Act: control
51. Set priority [`set_priority`]
52. End turn [`end_turn`]
53. Resign [`resign`]

## Draft
54. Current draft state: picks so far, team size [`draft.current_draft`, `team_size`]
55. Pick champion [`draft.pick`]

## Lists and sets (pure; replace loops in the grammar)
56. `filter(list, predicate)`
57. `first(list)` -> item or none
58. `exists(x)`
59. `union(sets)`, `minus(a, b)`, `contains(set, tile)` (bitboard ops)
60. `ring(set, r)`: tiles within Chebyshev r of a set
61. `closest(set)`: nearest reachable tile in a set

## Predicates (arguments to `filter`)
62. `in_attack_range`
63. `within(r, tile)`
64. `is_enemy`, `is_ally`, `is_awake`, `is_asleep` ...

## Randomness (mixed strategies)
65. `random_choice(list)`
66. `random_int(n)`

## Movement helper
67. `move_towards(tile or set)`: block occupied tiles, distance field from
    goals, step downhill (bundles the starter bot's `move_towards_closest`)
