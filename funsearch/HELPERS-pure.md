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

## 2. `fight(t)`: rank 0.2346
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

## 3. `fight(t)`: rank 0.2313
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

## 4. `go(t)`: rank 0.228
mean delta +0.0431 over 1 introductions; used in 196 programs; lines pure; executed None; deps none

```policy
def go(t):
    if ability_ready(0) and slot_is_dash(0):
        dash_towards(0, t)
    elif ability_ready(1) and slot_is_dash(1):
        dash_towards(1, t)
    move_towards(t)
```

## 5. `go_tribute(pool)`: rank 0.1544
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

## 6. `fight(t)`: rank 0.1209
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

## 7. `opener(s, f)`: rank 0.1048
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

## 8. `fight(t)`: rank 0.0725
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

## 9. `can_open(s, d)`: rank 0.0538
mean delta +0.0132 over 1 introductions; used in 58 programs; lines pure; executed None; deps none

```policy
def can_open(s, d):
    return ability_ready(s) and (slot_stun(s) > 0 or (slot_is_damage(s) and not slot_is_dash(s))) and d <= slot_range(s) + slot_radius(s)
```

## 10. `open_with(s, foe)`: rank 0.0536
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

## 11. `fight(t)`: rank 0.0514
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

## 12. `fight(t)`: rank 0.0432
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

## 13. `go(t)`: rank 0.0397
mean delta +0.0120 over 3 introductions; used in 26 programs; lines pure; executed None; deps consts: DASH_FUEL_MIN

```policy
DASH_FUEL_MIN = 40000
def go(t):
    if fuel_remaining() > DASH_FUEL_MIN:
        if ability_ready(0) and slot_is_dash(0):
            dash_towards(0, t)
        elif ability_ready(1) and slot_is_dash(1):
            dash_towards(1, t)
    move_towards(t)
```

## 14. `opener_ok(t)`: rank 0.0389
mean delta +0.0187 over 1 introductions; used in 7 programs; lines pure; executed None; deps none

```policy
def opener_ok(t):
    return (ability_ready(0) and slot_stun(0) > 0 and distance( position(), unit_position(t) ) <= slot_range(0) + slot_radius(0)) or (ability_ready(1) and slot_stun(1) > 0 and distance( position(), unit_position(t) ) <= slot_range(1) + slot_radius(1))
```

## 15. `open_fight(t)`: rank 0.0389
mean delta +0.0187 over 1 introductions; used in 7 programs; lines pure; executed None; deps none

```policy
def open_fight(t):
    if ability_ready(0) and slot_stun(0) > 0 and distance( position(), unit_position(t) ) <= slot_range(0) + slot_radius(0):
        if slot_is_dash(0):
            dash_towards(0, unit_position(t))
        else:
            cast_at_unit(0, t)
    elif ability_ready(1) and slot_stun(1) > 0 and distance( position(), unit_position(t) ) <= slot_range(1) + slot_radius(1):
        if slot_is_dash(1):
            dash_towards(1, unit_position(t))
        else:
            cast_at_unit(1, t)
```

## 16. `opener(s, f)`: rank 0.0302
mean delta +0.0169 over 1 introductions; used in 5 programs; lines pure; executed None; deps none

```policy
def opener(s, f):
    if ability_ready(s) and slot_stun(s) > 0 and distance( position(), unit_position(f) ) <= slot_range(s) + slot_radius(s):
        if slot_is_dash(s):
            dash_towards( s, unit_position(f) )
        else:
            cast_at_unit( s, f )
        end_turn()
```

## 17. `affordable(t, n)`: rank 0.0273
mean delta +0.0249 over 1 introductions; used in 2 programs; lines pure; executed None; deps consts: CLEAR_POWER

```policy
CLEAR_POWER = 60
def affordable(t, n):
    # n = allies_within(4) for this turn, passed in so it is queried only once
    return group_threat(t) * group_hp(t) <= health() * CLEAR_POWER * (1 + n)
```

## 18. `go(t)`: rank 0.007
mean delta +0.0025 over 1 introductions; used in 15 programs; lines pure; executed None; deps consts: DASH_MIN_FUEL

```policy
DASH_MIN_FUEL = 40000
def go(t):
    # dashes are expensive in fuel; only cast one when there is plenty left
    if fuel_remaining() > DASH_MIN_FUEL and ability_ready(0) and slot_is_dash(0):
        dash_towards(0, t)
    elif fuel_remaining() > DASH_MIN_FUEL and ability_ready(1) and slot_is_dash(1):
        dash_towards(1, t)
    move_towards(t)
```

## 19. `go(t)`: rank 0.0046
mean delta +0.0028 over 1 introductions; used in 4 programs; lines pure; executed None; deps consts: FUEL_GUARD

```policy
FUEL_GUARD = 40000
def go(t):
    # dashes are expensive in fuel; skip them when fuel is short
    if fuel_remaining() > FUEL_GUARD:
        if ability_ready(0) and slot_is_dash(0):
            dash_towards(0, t)
        elif ability_ready(1) and slot_is_dash(1):
            dash_towards(1, t)
    move_towards(t)
```

## 20. `go(t)`: rank 0.0037
mean delta +0.0008 over 2 introductions; used in 79 programs; lines pure; executed None; deps consts: DASH_FUEL

```policy
DASH_FUEL = 45000
def go(t):
    if fuel_remaining() > DASH_FUEL:
        if ability_ready(0) and slot_is_dash(0):
            dash_towards(0, t)
        elif ability_ready(1) and slot_is_dash(1):
            dash_towards(1, t)
    move_towards(t)
```
