"""port.py IN OUT: graft v33's fixes (ring small-spawn exclusion, monolith farmable rule, heal off-spawn, killshot 165,
hold-through-bag 117, gem-groups-first after 6 buys, boss-battle bush) into an A-9 lineage genome."""
import sys, re
s = open(sys.argv[1]).read()
def rep(old, new, count=1, opt=False):
    global s
    if old not in s:
        if opt: print('skip:', old[:60]); return
        raise SystemExit('missing: ' + old[:80])
    s = s.replace(old, new, count)
if "ALTAR_MONO:" not in s: rep("OPEN: Bool = False      # this turn: GOAL can be walked to\n",
    "OPEN: Bool = False      # this turn: GOAL can be walked to\n"
    "ALTAR_MONO: Bool = False  # some altar-ring tile is a monolith-group spawn (boss-battle layout)\n"
    "MONO_ONLY: Bool = False  # every gem-paying camp spawn is in a monolith group\n"
    "GEM_BASE: Tiles = None  # CAMP_BASE tiles of weak gem-paying groups (from round 3)\n"
    "GEM_MAPPED: Bool = False\n"
    "BUYS: Num = 0           # shop spends of 30+ gold so far\n"
    "LAST_GOLD: Num = 0\n")
if "ALTAR_RING - small" not in s: rep("        MONO_GROUPS = mono_groups()\n",
    "        MONO_GROUPS = mono_groups()\n"
    "        small = camp_spawns() - type_spawns(MONOLITH) - type_spawns(GOLEM)\n"
    "        if size(ALTAR_RING - small) > 0:\n            ALTAR_RING = ALTAR_RING - small\n"
    "        if size(SAFE_RING - small) > 0:\n            SAFE_RING = SAFE_RING - small\n"
    "        ALTAR_MONO = size(ALTAR_RING & MONO_GROUPS) > 0\n"
    "        MONO_ONLY = size((type_spawns(WOLF) | type_spawns(ELK) | type_spawns(GEM_CLUSTER) | type_spawns(GOLEM)) - MONO_GROUPS) == 0\n")
if "GEM_MAPPED = True" not in s: rep("        MAPPED = True\n    RULE = rule()\n",
    "        MAPPED = True\n"
    "    if not GEM_MAPPED and round() >= 3:\n        GEM_BASE = CAMP_BASE & gem_groups()\n        GEM_MAPPED = True\n"
    "    if gold() <= LAST_GOLD - 30:\n        BUYS = BUYS + 1\n    LAST_GOLD = gold()\n"
    "    RULE = rule()\n")
# killshot outranks pass-through bank
if "r_killshot()" not in s: rep("    if 150 > top and r_fight():", "    if 165 > top and r_fight() and r_killshot():\n        top = 165\n        pick = 7\n    if 150 > top and r_fight():")
# hold a capture through a ready bag unless a threat is near
m = re.search(r"    if (\d+) > top and bank_on\(\) and threat_near\(\):", s)
if "117 > top" not in s: rep("    if 116 > top and bank_on() and bank_blocked():",
    "    if 117 > top and r_hold() and not threat_near():\n        top = 117\n        pick = 16\n    if 116 > top and bank_on() and bank_blocked():", opt=True)

rep("    return at_spawn() and me().health < me().max_health and not foe_in_reach()\n",
    "    return at_spawn() and me().health < me().max_health and not foe_in_reach_off_spawn()\n", opt=True)
rep("    if not exists(c) or not in_reach(c) or not (c.pos in camp_spawns()):\n        return False\n    return not valid(bank_t1())",
    "    if not exists(c) or not farmable(c) or not (c.pos in camp_spawns()):\n        return False\n    return not valid(bank_t1())", opt=True)
rep("def r_camp() -> Bool:\n    return exists(reach_camp()) and in_reach(reach_camp())\n",
    "def r_camp() -> Bool:\n    c = reach_camp()\n    if not exists(c) or not farmable(c):\n        return False\n"
    "    if not is_awake(c) and hurt_below(0.5) and group_threat(camp_spawn(c)) >= 240:\n"
    "        return count(dist(a.pos, here()) <= 6 and a.pos != here() for a in allies()) > 0\n    return True\n", opt=True)
rep("    if team_gems() == 0 and round() > 800:\n        return True\n", "    if (team_gems() == 0 or MONO_ONLY) and round() > 800:\n        return True\n", opt=True)
rep("    return best(camps(), lambda c: 1 if in_reach(c) else 0)\n", "    return best(camps(), lambda c: 1 if farmable(c) else 0)\n", opt=True)
rep("            return 90 if o.unit.is_camp and o.unit.pos == reach_camp().pos else 0\n",
    "            return 90 if o.unit.is_camp and farmable(o.unit) and o.unit.pos == reach_camp().pos else 0\n", opt=True)
rep("        if o.tile in bushes():\n            v += 0.05\n", "        if o.tile in bushes() and not ALTAR_MONO:\n            v += 0.05\n", opt=True)
rep("    if o.tile in bushes():\n        v += 0.05\n", "    if o.tile in bushes() and not ALTAR_MONO:\n        v += 0.05\n", opt=True)
m = re.search(r"def camp_goal\(\) -> Tile:\n", s)
if m and "GEM_BASE - respawning" not in s:
    s = s[:m.end()] + "    if BUYS >= 6 and size(GEM_BASE) > 0:\n        t = closest(GEM_BASE - respawning())\n        if valid(t):\n            return t\n" + s[m.end():]

rep("    return exists(c) and in_reach(c) and (is_awake(c) or enemies_within(5) == 0)\n",
    "    return exists(c) and farmable(c) and (is_awake(c) or enemies_within(5) == 0)\n", opt=True)

extra = '''
@gene('B2938a', 'the in-reach enemy champion the fight targets dies to one basic attack now (health plus shield)', parents=['r7'])
def r_killshot() -> Bool:
    f = fight_foe()
    return exists(f) and attack_damage(me(), f) >= f.health + shield(f)

@gene("i1", "camp in reach worth hitting: not in a monolith's group (a hit wakes the group), unless the team goes for monoliths, or it stands on an altar-ring tile and I carry gems (boss-battle)", parents=["s14"])
def farmable(c: Unit) -> Bool:
    if not in_reach(c):
        return False
    if not (camp_spawn(c) in MONO_GROUPS):
        return True
    if gems() > 0 and camp_spawn(c) in ALTAR_RING:
        return True
    return r_mono()

@gene("i5", "spawn tiles of every group whose reward has gems and whose design strength is under 300", parents=["m8"])
def gem_groups() -> Tiles:
    acc = camp_spawns() - camp_spawns()
    for g in range(num_groups()):
        if group_gems(g) > 0 and sum(camp_base_strength(spawn_type(t)) for t in group_tiles(g)) < 300:
            acc = acc | group_tiles(g)
    return acc

@gene("i22", "a visible enemy champion off its own spawn can hit me now or after one step (a hurt champion next to an enemy spawn otherwise never heals)", parents=["s5"])
def foe_in_reach_off_spawn() -> Bool:
    h = here()
    r = me().attack_range
    return any(dist(h, u.pos) <= max(r, u.attack_range + u.move_speed) for u in enemies() if u.health_frac > 0.2 and not (u.pos in enemy_spawn()))
'''
import itertools
parts = re.split(r'\n(?=@gene)', extra.strip('\n'))
for part in parts:
    fn = re.search(r'def (\w+)\(', part).group(1)
    if f'def {fn}(' not in s:
        s = s.rstrip('\n') + '\n\n' + part + '\n'
open(sys.argv[2], 'w').write(s)
