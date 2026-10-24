# gen.py out.policy key=val ...   builds the hunter from tune-5's body
import sys
P = dict(HUNT_R=6, REACH=1, BAG_SAFE=45, BAG_NEAR=15, RET=0.3, CHASE_DASH=1, LS=0, STUN_FIRST=0, ALLY_MIN=0, PREY_HP=1.01, CHASE=1, SHIELD_HP=1.01, K10=0, TARGET='weakest', ENGAGE_HP=0, ODDS=9, OPENER=0, GROUP=0, PACK_R=12, STACK=0, JOIN_R=0)
for kv in sys.argv[2:]:
    k, v = kv.split('='); P[k] = v
src = open(__import__('pathlib').Path(__file__).resolve().parents[2] / 'policies' / 'tune-5.policy').read()
macros = src[src.index('def cast_on'):src.index('# ---- draft ----')]
body = src[src.index('# ---- every turn ----'):]
def kit(s, ind):
    i = ' ' * ind
    return f'''{i}if ability_ready({s}):
{i}    if slot_is_shield({s}) or slot_is_heal({s}):
{i}        if health() < {P["SHIELD_HP"]} * max_health():
{i}            cast_self({s})
{i}    elif slot_is_dash({s}):
{i}        if slot_stun({s}) > 0:
{i}            dash_towards({s}, unit_position(u))
{i}    elif slot_is_aoe({s}):
{i}        cast_at_tile({s}, unit_position(u))
{i}    elif not slot_is_reset({s}):
{i}        cast_at_unit({s}, u)
'''
def hits(ind):
    i = ' ' * ind
    out = kit(0, ind) + kit(1, ind) + f'{i}attack(u)\n'
    for s in (0, 1):
        out += f'{i}if ability_ready({s}) and slot_is_reset({s}):\n{i}    cast_self({s})\n{i}    attack(u)\n'
    return out
chase = ''
if int(P['CHASE_DASH']):
    for s in (0, 1):
        chase += f'''    if distance( unit_position(u), position() ) > {P["REACH"]} + 1 and ability_ready({s}) and slot_is_dash({s}):
        dash_towards({s}, unit_position(u))
'''
opener = ''
if int(P['OPENER']):
    for s_ in (0, 1):
        opener += f'''    if ability_ready({s_}) and slot_stun({s_}) > 0 and distance( unit_position(u), position() ) <= slot_range({s_}):
        if slot_is_dash({s_}):
            dash_towards({s_}, unit_position(u))
        elif slot_radius({s_}) > 0:
            cast_at_tile({s_}, unit_position(u))
        else:
            cast_at_unit({s_}, u)
'''
head = f'''# opp-hunter (style line): sim stand-in for the ladder's top teams (docs/TOP_TEAMS.md on analysis/sprint1).
# Meta draft; engages any enemy champion within {P["HUNT_R"]} tiles (focus fire via team_target, short chase);
# stuns/damage first, then attack + reset + attack; farms and banks like tune-5 otherwise.
# params: {" ".join(f"{k}={v}" for k, v in P.items())}

{macros}# engage u: hit it if in reach, else close in (dash when farther than our reach), then hit
def hunt(u):
    set_team_target(u)
    if distance( unit_position(u), position() ) <= {P["REACH"]}:
{hits(8)}        move_towards( unit_position(u) )
        end_turn()
{opener}{chase}    move_towards( unit_position(u) )
{hits(4)}    end_turn()

# ---- draft ----
if is_draft():
    let pool = unpicked_champions()
    if available(pool, champ_vesper_vale()):
        pick(champ_vesper_vale())
    elif available(pool, champ_heart_of_ruin()):
        pick(champ_heart_of_ruin())
    elif available(pool, champ_vendetta()):
        pick(champ_vendetta())
    elif available(pool, champ_marcella()):
        pick(champ_marcella())
    elif available(pool, champ_ryth()):
        pick(champ_ryth())
    else:
        pick( random_champion(pool) )
    end_turn()

'''
old = '''let enemy = weakest( filter( enemies_visible(), in_attack_range() ) )
# an enemy on its own spawn is healed every turn: fighting it there never ends (00reverse-spiral)
if exists(enemy) and not contains( spawn_region(enemy()), unit_position(enemy) ):
    cast_on(0, enemy)
    cast_on(1, enemy)
    attack(enemy)
    end_turn()
'''
new = f'''# in reach: hit the weakest enemy we can already attack (not on its own spawn)
let near_e = weakest( filter( enemies_visible(), in_attack_range() ) )
if exists(near_e) and not contains( spawn_region(enemy()), unit_position(near_e) ):
    hunt(near_e)
# ---- hunt: any enemy champion within {P["HUNT_R"]} tiles (not on its own spawn); the team target first ----
let enemy_spawn = spawn_region(enemy())
let tt = team_target()
if exists(tt) and distance( unit_position(tt), position() ) <= max_join and not contains( enemy_spawn, unit_position(tt) ) and local_strength({P["HUNT_R"]}) > {P["LS"]} and allies_within(4) >= {P["ALLY_MIN"]} and {P["CHASE"]} > 0:
    hunt(tt)
let prey = {P["TARGET"]}( enemies_visible() )
if exists(prey) and distance( unit_position(prey), position() ) <= {P["HUNT_R"]} and health() > {P["ENGAGE_HP"]} * max_health() and enemies_within(5) <= allies_within(5) + {P["ODDS"]} and not contains( enemy_spawn, unit_position(prey) ) and local_strength({P["HUNT_R"]}) > {P["LS"]} and allies_within(4) >= {P["ALLY_MIN"]} and unit_health_frac(prey) < {P["PREY_HP"]} and {P["CHASE"]} > 0:
    hunt(prey)
'''
new = new.replace('max_join', str(int(P['JOIN_R']) if int(P['JOIN_R']) else int(P['HUNT_R']) + 2))
assert old in body; body = body.replace(old, new)
o = 'let bag_ready = gems() >= 25 or round_number() > 1500 or health() < 0.3 * max_health()'
assert o in body
body = body.replace(o, f'let bag_ready = gems() >= {P["BAG_SAFE"]} or (gems() >= {P["BAG_NEAR"]} and enemies_within(8) > 0) or round_number() > 1500 or health() < 0.3 * max_health()')
body = body.replace('if not at_spawn and health() < 0.3 * max_health():', f'if not at_spawn and health() < {P["RET"]} * max_health():')
o_camp = """if exists(camp):
    cast_on(0, camp)
    cast_on(1, camp)
    attack(camp)
    end_turn()"""
assert o_camp in body
body = body.replace(o_camp, """if exists(camp):
    cast_on(0, camp)
    cast_on(1, camp)
    attack(camp)
    # attack reset: cast after the first basic attack, then hit again (coordinator's tune5-reset fix)
    if ability_ready(0) and slot_is_reset(0):
        cast_self(0)
        attack(camp)
    if ability_ready(1) and slot_is_reset(1):
        cast_self(1)
        attack(camp)
    end_turn()""")
if int(P['GROUP']):
    o_goal = "let goal = closest(goals)\n"
    assert o_goal in body
    body = body.replace(o_goal, f"""# group: follow the camp group an ally has claimed (move and fight as a pack), else lead and claim
let pack = closest( claimed_by_allies() )
if exists(pack) and distance(pack, position()) > 0 and distance(pack, position()) <= {P["PACK_R"]}:
    if distance(pack, position()) > 2:
        dash_to(0, pack)
        dash_to(1, pack)
    move_towards(pack)
    end_turn()
let goal = closest(goals)
if exists(goal):
    claim(goal)
""")
if int(P['STACK']):
    i0 = body.index("    let shards_bought = floor( gold() / 30 )")
    i1 = body.index("    buy( shard(stat_health()), rest_after_jungle - strength_shards )\n") + len("    buy( shard(stat_health()), rest_after_jungle - strength_shards )\n")
    body = body[:i0] + """    # one stat per carry (TOP_TEAMS_FIGHTS): focus on the spell champions, strength on the rest
    if i_am(champ_heart_of_ruin()) or i_am(champ_ryth()) or i_am(champ_marcella()):
        buy( shard(stat_focus()), floor( gold() / 30 ) )
    else:
        buy( shard(stat_strength()), floor( gold() / 30 ) )
""" + body[i1:]
open(sys.argv[1], 'w').write(head + body)
