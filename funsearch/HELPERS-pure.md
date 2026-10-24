# Shared helper library

Harvested by `python3 -m funsearch.helpers` from children that scored >= their best parent. Ranked by
mean score delta (child vs best parent, over the children that introduced or changed the helper) x
log(1 + introductions); kept with >= 2 introductions or a mean delta >= 0.05. Library code: paste and call;
mind fuel.

## 1. `fight(t)`: rank 0.1147
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

## 2. `go_tribute(pool)`: rank 0.0974
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

## 3. `fight(t)`: rank 0.0478
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

## 4. `fight(t)`: rank 0.0432
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

## 5. `fight(t)`: rank 0.0349
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

## 6. `opener(s, f)`: rank 0.0349
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

## 7. `go(t)`: rank 0.0167
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

## 8. `go(t)`: rank 0.0009
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

## 9. `fight(t)`: rank 0.0
mean delta +0.0000 over 2 introductions; used in 2 programs; lines pure; executed None; deps consts: HURT_FRAC

```policy
HURT_FRAC = 0.5
def fight(t):
    # self-shield / self-heal when hurt
    if health() < HURT_FRAC * max_health():
        if ability_ready(0) and (slot_is_shield(0) or slot_is_heal(0)):
            cast_self(0)
        elif ability_ready(1) and (slot_is_shield(1) or slot_is_heal(1)):
            cast_self(1)
    # stun first so the target loses its turn, then damage abilities (not resets: those self-cast)
    if ability_ready(0) and slot_is_stun(0):
        cast_at_unit(0, t)
    elif ability_ready(1) and slot_is_stun(1):
        cast_at_unit(1, t)
    if ability_ready(0) and not slot_is_shield(0) and not slot_is_dash(0) and not slot_is_heal(0) and not slot_is_reset(0):
        cast_at_unit(0, t)
    if ability_ready(1) and not slot_is_shield(1) and not slot_is_dash(1) and not slot_is_heal(1) and not slot_is_reset(1):
        cast_at_unit(1, t)
    # ranged champions step away from an adjacent enemy instead of trading in place
    if i_am_ranged() and distance( unit_position(t), position() ) <= 1 and can_move():
        move_away_from( unit_position(t) )
        end_turn()
    attack(t)
    # attack reset: self-cast right after the basic attack, then attack again
    if can_attack():
        if ability_ready(0) and slot_is_reset(0):
            cast_self(0)
            attack(t)
        elif ability_ready(1) and slot_is_reset(1):
            cast_self(1)
            attack(t)
    end_turn()
```
