"""Constant grid around v28: each knob is (name, template, current, steps). Writes const.json."""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb

# (name, old exact snippet with {} for the value, current, candidate values)
KNOBS = [
    ('run_hp', 'return not at_spawn() and hurt_below({}) and under_fire()', 0.3, [0.2, 0.25, 0.35, 0.4]),
    ('recall_hp', 'return not at_spawn() and hurt_below({})\n', 0.3, [0.2, 0.25, 0.35, 0.4]),
    ('cash_min', '    if g < {}:\n        return False\n    f = min', 5, [3, 4, 7, 10]),
    ('cash_f0', 'f = min(0.8, {} + g / 100)', 0.55, [0.45, 0.5, 0.6, 0.65]),
    ('cash_fmax', 'f = min({}, 0.55', 0.8, [0.7, 0.75, 0.85, 0.9]),
    ('cash_eta', 'return altar_eta() > {}\n', 4, [2, 3, 6, 8]),
    ('pref_gems', 'return gems() >= {} and threat_eta() <= 2 and valid(adj_altar())', 5, [3, 4, 7, 10]),
    ('pref_eta', 'return gems() >= 5 and threat_eta() <= {} and valid(adj_altar())', 2, [1, 3, 4]),
    ('adj_bank', '(gems() >= {} and valid(adj_altar()))', 3, [1, 2, 5, 8]),
    ('bag', 'return g >= {} or (g >= 10 and altar_eta', 15, [10, 12, 18, 20, 25]),
    ('bag10', 'or (g >= {} and altar_eta() <= 3) or (g >= 10 and threat', 10, [6, 8, 12]),
    ('bag_eta', 'altar_eta() <= {}) or (g >= 10 and threat', 3, [2, 4, 5]),
    ('bag_thr', 'or (g >= {} and threat_near()) or round()', 10, [5, 7, 13]),
    ('bag_round', 'or round() > {} or hurt_below(0.3)', 1500, [1200, 1350, 1650, 1800]),
    ('bag_hp', 'round() > 1500 or hurt_below({})', 0.3, [0.2, 0.4, 0.5]),
    ('thr_r', 'return enemies_within({}) > 0 or (hurt_below(0.5)', 5, [3, 4, 6, 7]),
    ('thr_hp', 'or (hurt_below({}) and enemies_within(7)', 0.5, [0.3, 0.4, 0.6, 0.7]),
    ('thr_r2', 'and enemies_within({}) > 0) or threat_eta() <= 3', 7, [6, 8, 9]),
    ('thr_eta', ' > 0) or threat_eta() <= {}\n', 3, [1, 2, 4, 5]),
    ('mono_round', 'return team_gems() == 0 and round() > {}', 800, [500, 650, 1000, 1200]),
    ('bg_gems', 'return valid(g) and gems() >= {} and group_threat', 10, [5, 7, 15, 20]),
    ('bg_thr', 'group_threat(g) >= {} and fuel() > 65000', 240, [160, 200, 300, 360]),
    ('dash_d', 'dist(here(), GOAL) > {} and fuel() > 45000', 2, [1, 3, 4]),
    ('dash_fuel', 'dist(here(), GOAL) > 2 and fuel() > {}', 45000, [35000, 40000, 50000, 55000]),
    ('dash_rfuel', '        return fuel() > {}\n    if walks() and valid(GOAL) and dist', 40000, [30000, 50000, 60000]),
    ('mv_near', 'v -= {} * count(dist(t, o.tile) <= 2', 0.3, [0, 0.15, 0.6, 1.0]),
    ('mv_far', 'v -= {} * count(dist(t, o.tile) <= 3', 0.1, [0, 0.05, 0.2, 0.4]),
    ('mv_bush', 'v += {}\n', 0.05, [0, 0.2, 0.5]),
    ('fir_hp', 'for u in enemies() if u.health_frac > {})', 0.2, [0, 0.1, 0.3, 0.4]),
    ('fire_r', 'return in_danger() or enemies_within({}) > 0', 6, [4, 5, 7, 8]),
    ('ahead_r', 'dist(here(), f.pos) <= {} and not (f.pos in enemy_spawn())\n\n@gene("a6"', 5, [3, 4, 6, 7]),
    ('bank_skip', 'if dist(here(), b) + {} < dist(here(), a):', 4, [0, 2, 6, 10]),
    ('safe_mono', 'ring(type_spawns(MONOLITH), {})', 5, [3, 4, 6, 7]),
    ('dash_foe', 'k = d * 10 + {} * sum', 15, [0, 5, 30, 60]),
    ('lock_fuel', 'has_lock() and fuel() > {} and v', 60000, [45000, 50000, 70000]),
    ('bg_fuel', 'group_threat(g) >= 240 and fuel() > {}', 65000, [50000, 55000, 60000, 75000]),
    ('eta_pad', 'return -floor(-(d * {} / 5) / max(1, s))', 6, [5, 7, 8]),
    ('treas', '    t = floor(n / {})\n    j =', 2, [1, 3, 4]),
    ('jung', '    j = floor((n - t) / {})\n', 2, [1, 3]),
    ('str', '    s = floor((n - t - j) / {})\n', 2, [1, 3]),
    ('ahead_cc', 'if k == AB_CC and threat_eta() <= {}:', 2, [1, 3, 4]),
]


def fmt(v):
    return repr(v) if isinstance(v, float) else str(v)


def variants():
    base = tb.base_text()
    out = []
    for name, tpl, cur, vals in KNOBS:
        old = tpl.format(fmt(cur))
        assert base.count(old) == 1, (name, old, base.count(old))
        for v in vals:
            out.append(dict(tag='%s=%s' % (name, fmt(v)), edits=[[old, tpl.format(fmt(v))]]))
    return out


if __name__ == '__main__':
    v = variants()
    json.dump(v, open(sys.argv[1], 'w'), indent=0)
    print(len(v))
