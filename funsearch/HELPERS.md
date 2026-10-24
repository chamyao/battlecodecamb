# Shared helper library

Harvested by `python3 -m funsearch.helpers` from children that scored >= their best parent. Ranked by
mean score delta (child vs best parent, over the children that introduced or changed the helper) x
log(1 + uses). Library code: paste and call; mind fuel.

## 1. `fight(t)`: rank 0.3676
mean delta +0.0827 over 3 introductions; used in 84 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
        end_turn()
    attack(t)
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(t)
    elif ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(t)
    end_turn()
```

## 2. `hunt(u)`: rank 0.2783
mean delta +0.0558 over 1 introductions; used in 146 programs; lines hybrid, style; executed None; deps none

```policy
def hunt(u):
    set_team_target(u)
    if distance( unit_position(u), position() ) <= 1 or (i_am_ranged() and distance( unit_position(u), position() ) <= 3):
        if ability_ready(0):
            if slot_is_shield(0) or slot_is_heal(0):
                if health() < 1.01 * max_health():
                    cast_self(0)
            elif slot_is_dash(0):
                if i_am(champ_heart_of_ruin()):
                    dash_towards(0, unit_position(u))
            elif slot_is_aoe(0):
                cast_at_tile(0, unit_position(u))
            elif not slot_is_reset(0):
                cast_at_unit(0, u)
        if ability_ready(1):
            if slot_is_shield(1) or slot_is_heal(1):
                if health() < 1.01 * max_health():
                    cast_self(1)
            elif slot_is_dash(1):
                if i_am(champ_heart_of_ruin()):
                    dash_towards(1, unit_position(u))
            elif slot_is_aoe(1):
                cast_at_tile(1, unit_position(u))
            elif not slot_is_reset(1):
                cast_at_unit(1, u)
        attack(u)
        if ability_ready(0) and slot_is_reset(0):
            cast_self(0)
            attack(u)
        if ability_ready(1) and slot_is_reset(1):
            cast_self(1)
            attack(u)
        if not i_am_ranged():
            move_towards( unit_position(u) )
        end_turn()
    if distance( unit_position(u), position() ) > 1 + 1 and ability_ready(0) and slot_is_dash(0):
        dash_towards(0, unit_position(u))
    if distance( unit_position(u), position() ) > 1 + 1 and ability_ready(1) and slot_is_dash(1):
        dash_towards(1, unit_position(u))
    move_towards( unit_position(u) )
    if ability_ready(0):
        if slot_is_shield(0) or slot_is_heal(0):
            if health() < 1.01 * max_health():
                cast_self(0)
        elif slot_is_dash(0):
            if i_am(champ_heart_of_ruin()):
                dash_towards(0, unit_position(u))
        elif slot_is_aoe(0):
            cast_at_tile(0, unit_position(u))
        elif not slot_is_reset(0):
            cast_at_unit(0, u)
    if ability_ready(1):
        if slot_is_shield(1) or slot_is_heal(1):
            if health() < 1.01 * max_health():
                cast_self(1)
        elif slot_is_dash(1):
            if i_am(champ_heart_of_ruin()):
                dash_towards(1, unit_position(u))
        elif slot_is_aoe(1):
            cast_at_tile(1, unit_position(u))
        elif not slot_is_reset(1):
            cast_at_unit(1, u)
    attack(u)
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(u)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(u)
    end_turn()
```

## 3. `fight(t)`: rank 0.2346
mean delta +0.0690 over 1 introductions; used in 29 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    # damage abilities: never cast resets at the enemy (they are self-cast after a basic attack)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    # ranged champions step away from an adjacent enemy, then still shoot this turn
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
    if distance( unit_position(t), position() ) <= 1 or (i_am_ranged() and distance( unit_position(t), position() ) <= 3):
        attack(t)
        # attack reset: self-cast right after a basic attack, then attack again
        if ability_ready(0) and slot_is_reset(0):
            cast_self(0)
            attack(t)
        elif ability_ready(1) and slot_is_reset(1):
            cast_self(1)
            attack(t)
    end_turn()
```

## 4. `fight(t)`: rank 0.2313
mean delta +0.0431 over 1 introductions; used in 212 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1):
        cast_at_unit(1, t)
    # ranged champions step away from an adjacent enemy instead of trading in place
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
        end_turn()
    attack(t)
    end_turn()
```

## 5. `go(t)`: rank 0.228
mean delta +0.0431 over 1 introductions; used in 196 programs; lines pure; executed None; deps none

```policy
def go(t):
    if ability_ready(0) and slot_is_dash(0):
        dash_towards(0, t)
    elif ability_ready(1) and slot_is_dash(1):
        dash_towards(1, t)
    move_towards(t)
```

## 6. `go_tribute(pool)`: rank 0.1544
mean delta +0.1406 over 1 introductions; used in 2 programs; lines pure; executed None; deps none

```policy
def go_tribute(pool):
    let altar = first( filter( pool, within(1, position()) ) )
    if exists(altar):
        tribute(altar)
        end_turn()
    move_towards( closest( ring(pool, 1) ) )
    end_turn()
```

## 7. `cast_on(slot, u)`: rank 0.1431
mean delta +0.0396 over 1 introductions; used in 36 programs; lines hybrid; executed True; deps none

```policy
def cast_on(slot, u):
    if ability_ready(slot) and not slot_is_dash(slot) and not slot_is_heal(slot) and not slot_is_reset(slot):
        if slot_is_shield(slot):
            if distance(position(), unit_position(u)) <= 3:
                cast_self(slot)
        elif distance(position(), unit_position(u)) <= slot_range(slot):
            if slot_is_aoe(slot):
                cast_at_tile(slot, unit_position(u))
            else:
                cast_at_unit(slot, u)
```

## 8. `cast_foe(u)`: rank 0.142
mean delta +0.0396 over 1 introductions; used in 35 programs; lines hybrid; executed False; deps none

```policy
def cast_foe(u):
    if ability_ready(0) and slot_stun(0) > 0 and not slot_is_dash(0) and not slot_is_shield(0) and not slot_is_heal(0) and not slot_is_reset(0) and distance(position(), unit_position(u)) <= slot_range(0):
        if slot_is_aoe(0):
            cast_at_tile(0, unit_position(u))
        else:
            cast_at_unit(0, u)
    elif ability_ready(1) and not slot_is_dash(1) and not slot_is_shield(1) and not slot_is_heal(1) and not slot_is_reset(1) and distance(position(), unit_position(u)) <= slot_range(1):
        if slot_is_aoe(1):
            cast_at_tile(1, unit_position(u))
        else:
            cast_at_unit(1, u)
    elif ability_ready(0) and not slot_is_dash(0) and not slot_is_shield(0) and not slot_is_heal(0) and not slot_is_reset(0) and distance(position(), unit_position(u)) <= slot_range(0):
        if slot_is_aoe(0):
            cast_at_tile(0, unit_position(u))
        else:
            cast_at_unit(0, u)
```

## 9. `fight(t)`: rank 0.1209
mean delta +0.0504 over 1 introductions; used in 10 programs; lines pure; executed None; deps consts: HURT_FRAC, KITE_FRAC

```policy
HURT_FRAC = 0.5
KITE_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    # damage casts: never shields, dashes, heals or attack resets (resets are self-cast after attacks)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    # ranged champions kite an adjacent enemy only when hurt and losing the trade
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move() and health() < KITE_FRAC * max_health() and health() < unit_health_frac(t) * max_health():
        move_away_from( unit_position(t) )
        end_turn()
    attack(t)
    # attack reset: self-cast after the basic attack, then attack again this turn
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(t)
    elif ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(t)
    end_turn()
```

## 10. `head_to(g, cs)`: rank 0.1165
mean delta +0.0486 over 1 introductions; used in 10 programs; lines style; executed None; deps defs: dash_to

```policy
def head_to(g, cs):
    if exists(g) and distance(position(), g) > 4:
        dash_to(0, g)
        dash_to(1, g)
    move_towards(g)
    if exists(first(filter(cs, in_attack_range()))):
        attack(first(filter(cs, in_attack_range())))
    set_priority( 1 + random_int(100) )
    end_turn()
```

## 11. `dangerous(g)`: rank 0.1094
mean delta +0.0404 over 1 introductions; used in 14 programs; lines style; executed None; deps keeps: my_dps

```policy
def dangerous(g):
    return group_threat(g) * group_hp(g) / (my_dps * (1 + allies_within(4))) > health()
```

## 12. `opener(s, f)`: rank 0.1048
mean delta +0.0504 over 1 introductions; used in 7 programs; lines pure; executed None; deps none

```policy
def opener(s, f):
    if ability_ready(s) and (slot_stun(s) > 0 or slot_is_damage(s)) and not slot_is_reset(s) and distance( position(), unit_position(f) ) <= slot_range(s) + slot_radius(s):
        if slot_is_dash(s):
            dash_towards( s, unit_position(f) )
        else:
            cast_at_unit( s, f )
        end_turn()
```

## 13. `cast_on(slot, u)`: rank 0.0897
mean delta +0.0266 over 1 introductions; used in 28 programs; lines style; executed None; deps none

```policy
def cast_on(slot, u):
    if ability_ready(slot):
        if slot_is_shield(slot) or slot_is_heal(slot):
            cast_self(slot)
        elif not slot_is_dash(slot) and not slot_is_reset(slot):
            cast_at_unit(slot, u)
```

## 14. `fight(t)`: rank 0.0725
mean delta +0.0315 over 1 introductions; used in 9 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    # damage abilities: never cast resets at the enemy (they are self-cast after a basic attack)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    if distance( unit_position(t), position() ) <= 1 or (i_am_ranged() and distance( unit_position(t), position() ) <= 3):
        attack(t)
        # attack reset: self-cast right after a basic attack, then attack again
        if ability_ready(0) and slot_is_reset(0):
            cast_self(0)
            attack(t)
        elif ability_ready(1) and slot_is_reset(1):
            cast_self(1)
            attack(t)
    # ranged champions step away from an adjacent enemy only if they could not attack
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
    end_turn()
```

## 15. `fight(u)`: rank 0.0624
mean delta +0.0225 over 1 introductions; used in 15 programs; lines style; executed None; deps none

```policy
def fight(u):
    set_team_target(u)
    if ability_ready(0):
        if slot_is_shield(0) or slot_is_heal(0):
            cast_self(0)
        elif slot_is_damage(0) or slot_is_aoe(0) or slot_is_stun(0):
            cast_at_unit(0, u)
    if ability_ready(1):
        if slot_is_shield(1) or slot_is_heal(1):
            cast_self(1)
        elif slot_is_damage(1) or slot_is_aoe(1) or slot_is_stun(1):
            cast_at_unit(1, u)
    attack(u)
    # attack reset: self-cast AFTER a basic attack, then attack again
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
    attack(u)
    end_turn()
```

## 16. `hunt(u)`: rank 0.0576
mean delta +0.0240 over 1 introductions; used in 10 programs; lines style; executed None; deps none

```policy
def hunt(u):
    set_team_target(u)
    if distance( unit_position(u), position() ) <= 1 or (i_am_ranged() and distance( unit_position(u), position() ) <= 3):
        if ability_ready(0):
            if slot_is_shield(0) or slot_is_heal(0):
                if health() < 1.01 * max_health():
                    cast_self(0)
            elif slot_is_dash(0):
                if i_am(champ_heart_of_ruin()):
                    dash_towards(0, unit_position(u))
            elif slot_is_aoe(0):
                cast_at_tile(0, unit_position(u))
            elif not slot_is_reset(0):
                cast_at_unit(0, u)
        if ability_ready(1):
            if slot_is_shield(1) or slot_is_heal(1):
                if health() < 1.01 * max_health():
                    cast_self(1)
            elif slot_is_dash(1):
                if i_am(champ_heart_of_ruin()):
                    dash_towards(1, unit_position(u))
            elif slot_is_aoe(1):
                cast_at_tile(1, unit_position(u))
            elif not slot_is_reset(1):
                cast_at_unit(1, u)
        attack(u)
        if ability_ready(0) and slot_is_reset(0):
            cast_self(0)
            attack(u)
        if ability_ready(1) and slot_is_reset(1):
            cast_self(1)
            attack(u)
        if not i_am_ranged():
            move_towards( unit_position(u) )
        end_turn()
    # stun opener: land the stun from its reach before walking in (first hit lands first)
    if ability_ready(0) and slot_stun(0) > 0 and distance( unit_position(u), position() ) <= slot_range(0) + slot_radius(0):
        if slot_is_dash(0):
            dash_towards(0, unit_position(u))
        elif slot_is_aoe(0):
            cast_at_tile(0, unit_position(u))
        elif slot_is_damage(0):
            cast_at_unit(0, u)
    if ability_ready(1) and slot_stun(1) > 0 and distance( unit_position(u), position() ) <= slot_range(1) + slot_radius(1):
        if slot_is_dash(1):
            dash_towards(1, unit_position(u))
        elif slot_is_aoe(1):
            cast_at_tile(1, unit_position(u))
        elif slot_is_damage(1):
            cast_at_unit(1, u)
    if distance( unit_position(u), position() ) > 1 + 1 and ability_ready(0) and slot_is_dash(0):
        dash_towards(0, unit_position(u))
    if distance( unit_position(u), position() ) > 1 + 1 and ability_ready(1) and slot_is_dash(1):
        dash_towards(1, unit_position(u))
    move_towards( unit_position(u) )
    if ability_ready(0):
        if slot_is_shield(0) or slot_is_heal(0):
            if health() < 1.01 * max_health():
                cast_self(0)
        elif slot_is_dash(0):
            if i_am(champ_heart_of_ruin()):
                dash_towards(0, unit_position(u))
        elif slot_is_aoe(0):
            cast_at_tile(0, unit_position(u))
        elif not slot_is_reset(0):
            cast_at_unit(0, u)
    if ability_ready(1):
        if slot_is_shield(1) or slot_is_heal(1):
            if health() < 1.01 * max_health():
                cast_self(1)
        elif slot_is_dash(1):
            if i_am(champ_heart_of_ruin()):
                dash_towards(1, unit_position(u))
        elif slot_is_aoe(1):
            cast_at_tile(1, unit_position(u))
        elif not slot_is_reset(1):
            cast_at_unit(1, u)
    attack(u)
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(u)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(u)
    end_turn()
```

## 17. `can_open(s, d)`: rank 0.0538
mean delta +0.0132 over 1 introductions; used in 58 programs; lines pure; executed None; deps none

```policy
def can_open(s, d):
    return ability_ready(s) and (slot_stun(s) > 0 or (slot_is_damage(s) and not slot_is_dash(s))) and d <= slot_range(s) + slot_radius(s)
```

## 18. `open_with(s, foe)`: rank 0.0536
mean delta +0.0132 over 1 introductions; used in 57 programs; lines pure; executed None; deps none

```policy
def open_with(s, foe):
    if slot_is_dash(s):
        dash_towards(s, unit_position(foe))
    else:
        cast_at_unit(s, foe)
    set_team_target(foe)
    if distance( position(), unit_position(foe) ) <= 1 or (i_am_ranged() and distance( position(), unit_position(foe) ) <= 3):
        attack(foe)
    else:
        move_towards( unit_position(foe) )
    end_turn()
```

## 19. `fight(t)`: rank 0.0514
mean delta +0.0138 over 1 introductions; used in 41 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    # ranged champions step away from an adjacent enemy, then still attack from range
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
    attack(t)
    # attack reset: self-cast after the basic attack, then attack again
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(t)
    elif ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(t)
    end_turn()
```

## 20. `fight(t)`: rank 0.0432
mean delta +0.0624 over 1 introductions; used in 1 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    # damage casts at the enemy: skip shields, dashes, heals and resets (resets are self-cast below)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    # ranged champions step away from an adjacent enemy instead of trading in place
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
        end_turn()
    attack(t)
    # attack reset: self-cast right after a basic attack, then attack again
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        if can_attack():
            attack(t)
    elif ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        if can_attack():
            attack(t)
    end_turn()
```
