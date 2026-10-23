# Maps where a v7 mirror tributes nothing (simulator diagnosis)

After the 01the-farm fixes (docs/FARM_DIAGNOSIS.md), a v7 mirror (interp/v0 f88ae73) still
tributes 0 gems on both sides on 00contest, 00reverse-spiral and 01boss-battle. Traced with
`INTERP_TRACE=1` (see FARM_DIAGNOSIS.md). The three causes are unrelated. Fixes are in
`policies/v7-zerogem.policy`; each was also measured alone as a v7 variant (10-game mirrors on
its map; 400 games vs v7 on all 40 maps × 5 seeds).

## 00reverse-spiral: an endless duel at adjacent spawns

The two spawn regions are within attack range of each other. From round 1, every champion
with an enemy in range attacks forever (v7 line 73). The spawn heals both sides every turn
end, so nobody ever dies or leaves. The champion with no enemy in its own range is hit by
ranged enemies, never reaches full health, and waits forever in "heal on spawn before heading
out" (line 53). Every champion stands on one tile for all 2000 rounds.

Fix: do not fight an enemy that stands on its own spawn:
`if exists(enemy) and not contains( spawn_region(enemy()), unit_position(enemy) ):`.
Mirror 0/0 -> 913/945 gems; alone vs v7: 202/400.

## 01boss-battle: the only altar is behind a monolith

The single altar (25,20) sits in a wall line. Its four open neighbours (24..25, 19) and
(24..25, 21) are **holes**, (26,20) is a wall, and (24,20) is a monolith (20,000 HP, 200 dmg,
range 5; with another at (23,20)). The only tile from which anyone can tribute is the
monolith's own tile, once it is dead. v7 never fights monoliths. Carriers with 20-80 gems
walk to the closest altar-ring tile, which is the monolith's tile (blocked), and wait beside it.

Fix: in the carrier branch, when the closest altar-ring tile is a camp tile, attack a camp in
range (the monolith):
```
    let altar_goal = closest(altar_ring)
    if contains(camp_spawns, altar_goal):
        let blocker = first( filter( camps_visible(), in_attack_range() ) )
        if exists(blocker):
            attack(blocker)
            end_turn()
    move_towards( altar_goal )
```
Mirror 0/0 -> 812/880 gems; alone vs v7: 205/400.

## 00contest: the only gems are in monoliths

Every camp on 00contest is a 0-gem gold cluster except two monoliths (200 gems each). v7
excludes monoliths from its goals, so it can never hold a gem there. The 0-0 is by design of
the policy, and cambc showed it too.

Fix: if nothing has been tributed by round 300, walk to the closest camp including monoliths:
```
if team_score(ally()) == 0 and round_number() > 300:
    move_towards( closest( minus( minus( camp_spawns, respawning_visible_spawns() ), golem_tiles() ) ) )
    end_turn()
```
Mirror 0/0 -> 340/200 gems; alone vs v7: 197/400 (neutral elsewhere).

## Combined (policies/v7-zerogem.policy)

| | result |
| --- | --- |
| mirrors (10 games): reverse-spiral, boss-battle, contest | 913/945, 955/685, 340/200 gems |
| vs v7, 400 games (40 maps × 5 seeds) | 211/400 = 52.8% |
| vs v7, `--bot-seeds` (what cambc will say, 80 games) | 43/80 |
| vs starter, 200 games | 194/200 |
