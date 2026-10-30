# arenaA-10 candidates (>= 43/80 vs v33 in an 80-game bot-seeded sim screen, 40 maps x 2 sides)

| name | vs v33 | vs B318 | vs A61188 | what changed |
| --- | --- | --- | --- | --- |
| A93635-v33port | 46/80 | 67/80 | 67/80 | A-9's A93635 + v33's fixes grafted (tools/port.py): altar rings without small-camp spawns, farmable() monolith rule (r13/r14/s14/a0, MONO_ONLY in r15), heal off enemy spawn (i22), killshot fight 165, hold-through-bag 117, gem-groups-first after 6 buys, boss-battle bush. Also the arena child of req 2603. A93635 unported: 34/80 vs v33, so the port is worth +12. |
| A103646-v33port | 51/80 | 67/80 | 67/80 | A103646 (arena tune child of A93636, rated 49.6) + the same v33 graft (tools/port.py). Unported A103646: 36/80 vs v33. farmer (genome/examples/farmer.genome): 80/80. Reference, v33 itself: 66/80 vs B318, 56/80 vs A61188, 80/80 vs farmer. |
| A103649-v33port | 48/80 | - | - | A103649 (arena cross of A103646 x A93635) + the v33 graft. |
| A103646-v33port-kf | 52/80 | 67/80 | 63/80 | A103646-v33port + rule_goal/rule_target read RULE (no re-run of rule(); 51/80 alone) + fight_foe ranks one-hit kills first. Sent to the arena as cross child of req 2641. |
| v33port-h4 | 52/80 | - | - | A103646-v33port-kf + pass-through bank with <= 10 gems even with a foe in reach (1-turn channel), no step into a 2-enemy pinch below half health, stun turns in threat_eta, our own lock does not block altar_eta/bank_t1, threat-aware altar choice (foe_gap). Gems 868 vs 833 for -kf. Sent to arena (req 2685). |
| v33port-heal | 54/80 | 64/80 | 62/80 | v33port-h4 + self-heal below 75% while carrying 10+ gems. Sent to arena (req 2687). h4 + this + calm altar tile + hurt-carrier bank-first = 52/80 vs v33, 69 B318, 60 A61188 (plateau ~52 +- 2). |
| v33port-heal-recall | 55/80 | 64/80 | 62/80 | v33port-heal + recall (r4, below 30%) only when no enemy champion can hit within 2 turns (damage cancels the channel). Sent to arena (req 2717). |
| v33port-calmbank | 56/80 | 64/80 | 60/80 | q1 (= v33port-heal-recall + monolith push after round 1400 with 3+ allies, 55/80) + bank_t2 prefers safe-altar tiles no enemy champion stands next to. Not yet sent to the arena. |
| v33port-spawnedge | 57/80 | 64/80 | 60/80 | v33port-calmbank + safe altar ring excludes altars within 3 of a golem spawn + no fight against a foe next to its own spawn while I am below half health. Sent to arena (req 2831). |
| A104033 | 54/80 | 67/80 | 63/80 | final arena #2 (S6, 50.17 in-arena), a mutate child in the ported lineage; highest gems of any screen (891 vs v33's 748). |
| A104023 | 55/80 | - | - | final arena #1 (S7, 50.47 in-arena); behaviour (gems 877.12) matches my injected w_b (v33port-calmbank + dash_mids excludes altars). |

Notes: x_2803 = v33port-spawnedge (57/80) is the best screened genome. Ideas screened harmful on it (do not ship): v33's r_run with threat_near (43), contested-camp avoidance in camp_goal (34), reach_camp reorder (42), treasure-first before round 300 (38), walk_field avoiding enemies when hurt (51), w1 unseen camps within 25 (52), under_fire ignoring recallers (53). Arena tuner bug seen in the wild: it perturbs index arguments (buff_turns(u, 1) -> 0.5234, ring(altars(), 1) -> 1.14).
