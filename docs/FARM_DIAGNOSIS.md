# 01the-farm: why v6 tributes nothing (simulator diagnosis)

v6 mirror on `maps/01the-farm.map26a`, 40 games at seed 3: 0 gems tributed by either side in
every game (reproduced). Found with the simulator's turn trace:
`INTERP_TRACE=1 interp_eval ... --games 1 --threads 1`. It prints, for each champion turn, the
state and the ordinal of the `end_turn()` that ended the turn (ordinals follow source order), plus
the `move_towards` target and step. `INTERP_TRACE_CAMPS=R` adds camps within R;
`INTERP_TRACE_TILES="x,y;..."` adds whether those tiles are blocked as the champion sees them.

## Failure 1: gem carriers livelock at a vision boundary (the main cause)

Five of six champions reach 10+ gems and then spend ~1,900 turns alternating between two
adjacent tiles, every turn ending at `move_towards(target)` (v6 line 88, the first altar
branch). Examples are (18,14)↔(19,13) and (18,15)↔(17,15), with the mirror image on team B.
The target is the ring of the pocket altars (23,22) and (26,22). The pocket's north entrance,
the gap (23..26,19) in the row-19 wall, is filled by asleep camps (gold cluster, wolf, wolf,
gold cluster). The real route goes around the west of the wall.

The interpreter blocks camp tiles only when the camp is **visible** (`refresh_occupancy`: the
camp occupancy). From (19,13) none of the gap camps are visible, so the gap looks open: the
target flips to (23,21) and the step goes back to (18,14). From (18,14), (23,19) and (24,19)
are visible and block, so the plan flips the other way. The two allies also block each
other's alternatives. Nobody ever reaches an altar.

**Block fix (interpreter):** camp tiles are static map data. Treat a camp tile we cannot see
as occupied for pathing, but keep it a valid goal: add it to the camp set, which
`move_towards_goals` and `closest` do not exclude. In `Interp::refresh_occupancy`, after the
camp occupancy:

```cpp
		static const bool fog_camps = std::getenv("INTERP_FOG_CAMPS") != nullptr; // EXPERIMENT
		if (fog_camps)
		{
			// Camp tiles are static map data: one we cannot see is assumed occupied, so paths do
			// not flip between "through the camp" and "around it" as it enters and leaves vision.
			if (!camp_tiles_ready)
			{
				for (const auto& cp : m().camps) camp_tiles.set(cp.pos);
				camp_tiles_ready = true;
			}
			Bitboard vis, unseen = camp_tiles;
			api.vision(vis);
			unseen.andnot(vis);
			dyn_block |= unseen;
			camps_cache |= unseen; // still valid goals (move_towards_goals / closest keep camp tiles)
		}
	}
	Bitboard camp_tiles;
	bool camp_tiles_ready = false;
```

It needs an `Api::vision` wrapper in `bot/src/bot_api.cpp`, which the bot does not have yet (one
host call per occupancy refresh; recalibrate afterwards). Measured in the simulator with the
fix as a runtime toggle:

| | farm mirror gems (A / B) | vs starter (200 games, 40 maps) | v6 mirror games with 0 gems (80) |
| --- | --- | --- | --- |
| v6, current interpreter | 0 / 0 | 195 | 8 (farm, contest, reverse-spiral, boss-battle) |
| v6, fog-camps fix | 747 / 795 | 196 | 6 (contest, reverse-spiral, boss-battle) |

A first version that also dropped unseen camp tiles as goals broke 22 maps (60/200 vs
starter): the goal sets are camp spawn tiles, so they must stay goals.

## Failure 2: idling on a dead camp of an uncleared group (the ladder 0-51 case)

A champion parks on a dead camp tile for hundreds to 1,600 turns, ending each turn at the
policy's last line. Example: (9,2), a gold cluster of group 7. At round 1000, elks (10,2),
(11,2) and gold clusters (9,2), (12,2) are dead; only the gem cluster (13,2) lives (asleep,
120 hp), 4 tiles away and out of attack range. The group is not capturable while it lives, and
a dead camp's tile is not "respawning" until the whole group clears. So it stays in `goals`,
`closest(goals)` is the champion's own tile, `move_towards` does nothing, and the champion
never walks the 4 tiles to finish the group. (Hypothesis 1 from the ladder notes is close:
hold-on-capturable never triggers because the group is not cleared, but the cause is the goal
pointing at our own tile.)

**Policy fix** (`policies/v6-idlefix.policy`): when the closest goal is our own tile, walk to
the nearest living visible camp, unless it is a monolith or golem:

```
let goal = closest(goals)
if distance(goal, position()) == 0:
    let live = nearest(camps)
    if exists(live) and not contains( union( monolith_tiles(), golem_tiles() ), unit_position(live) ):
        move_towards( unit_position(live) )
        end_turn()
move_towards( goal )
```

| | farm mirror gems | vs starter | v6-idlefix vs v6 (400 games, 40 maps × 5 seeds) |
| --- | --- | --- | --- |
| current interpreter | 0 / 0 (the livelock dominates) | 197 | 239/400 = 59.8% |
| with the fog-camps fix | 873 / 792 | 197 | 242/400 = 60.5% |
