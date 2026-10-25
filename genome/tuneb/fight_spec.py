"""Fight-constant grid on v33 (B1873-bossbush), Arena B lead Oct 25 08:40: band losses are early fights.
python3 genome/tuneb/fight_spec.py OUT.json BASE.genome"""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import const_spec as cs

REUSE = ['run_hp', 'recall_hp', 'thr_r', 'thr_hp', 'thr_r2', 'thr2_r', 'thr_eta', 'fire_r', 'fir_hp', 'ahead_r',
         'ahead_fin_r', 'ahead_hpw', 'ahead_cc', 'heal_hp', 'pref_eta', 'pref_gems']
EXTRA = {'run_hp': [0.5], 'recall_hp': [0.5], 'heal_hp': [0.9]}

# (name, template, current, values)
NEW = [
    ('kill_mult', 'return exists(f) and attack_damage(me(), f) * {} >= f.health + shield(f)', 1, [0.8, 1.25, 1.5, 2]),
    ('kill_prio', '    if {} > top and r_fight() and r_killshot():\n        top = 165', 165, [155, 172, 177, 185]),
    ('fight_rng', 'return exists(f) and dist(here(), f.pos) <= me().attack_range + {} and not', 0, [-1, 1]),
    ('reach_pad', 'u.attack_range + u.move_speed + {}) for u in enemies() if u.health_frac > 0.2 or', 0, [-1, 1, 2, 3]),
    ('dang_pad', 'dist(p, u.pos) <= u.attack_range + {} or (unit_gems', 1, [0, 2, 3]),
    ('dang_carry', 'or (unit_gems(u) > 0 and dist(p, u.pos) <= {}) for u in enemies())', 2, [0, 1, 3, 4]),
    ('foe_gemw', 'lambda u: unit_gems(u) * {} - u.health if in_reach(u)', 10, [0, 3, 30, 100]),
    ('nd_hp', 'and (u.health_frac >= {} or unit_gems(u) > 0)', 0.15, [0, 0.1, 0.25, 0.35]),
    ('dmg_low', 'if k == AB_DAMAGE and f.health_frac < {}:', 0.3, [0.2, 0.4, 0.5]),
    ('dmg_bonus', '        base += 30\n', 30, [0, 15, 60]),
    ('kill_bonus', '        base += 40\n', 40, [0, 20, 80]),
    ('cc_bonus', '        base += 20\n', 20, [0, 40]),
]
# structural switches written as plain edits
SWITCH = [
    ('run_firedonly', 'and hurt_below(0.3) and (under_fire() or threat_near())', 'and hurt_below(0.3) and under_fire()'),
    ('fight_hp30', 'return exists(f) and dist(here(), f.pos) <= me().attack_range and not (f.pos in enemy_spawn())',
     'return exists(f) and dist(here(), f.pos) <= me().attack_range and not (f.pos in enemy_spawn()) and (not hurt_below(0.3) or r_killshot())'),
    ('fight_hp50', 'return exists(f) and dist(here(), f.pos) <= me().attack_range and not (f.pos in enemy_spawn())',
     'return exists(f) and dist(here(), f.pos) <= me().attack_range and not (f.pos in enemy_spawn()) and (not hurt_below(0.5) or r_killshot())'),
    ('shield_hp70', '        return 170 - o.slot if o.unit == me() else 0', '        return 170 - o.slot if o.unit == me() and me().health_frac < 0.7 else 0'),
    ('shield_hp90', '        return 170 - o.slot if o.unit == me() else 0', '        return 170 - o.slot if o.unit == me() and me().health_frac < 0.9 else 0'),
]


def variants(text):
    out = []
    by = {k[0]: k for k in cs.knobs(text)}
    knobs = [by[n] for n in REUSE if n in by]
    knobs = [(n, t, c, v + EXTRA.get(n, [])) for n, t, c, v in knobs] + NEW
    for n, tpl, cur, vals in knobs:
        old = tpl.format(cs.fmt(cur))
        if n == 'fight_rng' or n == 'reach_pad':
            old = tpl.replace(' + {}', '')
        if n == 'kill_mult':
            old = tpl.replace(' * {}', '')
        assert text.count(old) == 1, (n, old, text.count(old))
        for v in vals:
            out.append(dict(tag='%s=%s' % (n, cs.fmt(v)), edits=[[old, tpl.format(cs.fmt(v))]]))
    for n, old, new in SWITCH:
        assert text.count(old) == 1, (n, old)
        out.append(dict(tag=n, edits=[[old, new]]))
    return out


if __name__ == '__main__':
    v = variants(open(sys.argv[2]).read())
    v.insert(0, dict(tag='centre', edits=[]))
    json.dump(v, open(sys.argv[1], 'w'), indent=0)
    print(len(v))
