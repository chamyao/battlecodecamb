# arenaA-10 candidates (>= 43/80 vs v33 in an 80-game bot-seeded sim screen, 40 maps x 2 sides)

| name | vs v33 | vs B318 | vs A61188 | what changed |
| --- | --- | --- | --- | --- |
| A93635-v33port | 46/80 | 67/80 | 67/80 | A-9's A93635 + v33's fixes grafted (tools/port.py): altar rings without small-camp spawns, farmable() monolith rule (r13/r14/s14/a0, MONO_ONLY in r15), heal off enemy spawn (i22), killshot fight 165, hold-through-bag 117, gem-groups-first after 6 buys, boss-battle bush. Also the arena child of req 2603. A93635 unported: 34/80 vs v33, so the port is worth +12. |
| A103646-v33port | 51/80 | 67/80 | 67/80 | A103646 (arena tune child of A93636, rated 49.6) + the same v33 graft (tools/port.py). Unported A103646: 36/80 vs v33. farmer (genome/examples/farmer.genome): 80/80. Reference, v33 itself: 66/80 vs B318, 56/80 vs A61188, 80/80 vs farmer. |
| A103649-v33port | 48/80 | - | - | A103649 (arena cross of A103646 x A93635) + the v33 graft. |
| A103646-v33port-kf | 52/80 | 67/80 | 63/80 | A103646-v33port + rule_goal/rule_target read RULE (no re-run of rule(); 51/80 alone) + fight_foe ranks one-hit kills first. Sent to the arena as cross child of req 2641. |
