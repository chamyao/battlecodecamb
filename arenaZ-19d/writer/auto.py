import sys, os, re, json, subprocess
sys.path.insert(0, '/root/w')
from lib import *
CHASE = '''@gene("new", "how much closer a step brings me to the weakest visible enemy champion when it is hurt and I am healthy", parents=["s1"])
def chase_gain(t: Tile) -> Num:
    if me().health_frac < 0.5:
        return 0
    v = best(enemies(), lambda u: 0 - u.health_frac)
    if not exists(v) or v.health_frac > 0.5 or dist(v.pos, me().pos) > 6:
        return 0
    return dist(v.pos, me().pos) - dist(v.pos, t)

'''
GEMF = '''@gene("new", "goal tiles narrowed to gem clusters when one is not much farther than the other goals", parents=["s3"])
def gem_first(gt: Tiles) -> Tiles:
    gem = gt & type_spawns(GEM_CLUSTER)
    if size(gem) == 0:
        return gt
    rest = gt - type_spawns(GEM_CLUSTER)
    if size(rest) == 0:
        return gem
    if dist(nearest(gem, me().pos), me().pos) <= dist(nearest(rest, me().pos), me().pos) + 8:
        return gem
    return gt

'''
OUTN = """@gene("new", "more visible enemy champions near me than allies, and I am not healthy", parents=["s1"])
def outnumbered() -> Bool:
    ne = count(dist(u.pos, me().pos) <= 5 for u in enemies())
    na = count(dist(u.pos, me().pos) <= 5 for u in allies())
    return ne > na + 1 and me().health_frac < 0.7

"""
HUNT = """@gene("new", "how much closer a step brings me to a visible enemy champion carrying many gems, when I am healthy and not alone", parents=["s1"])
def hunt_gain(t: Tile) -> Num:
    if me().health_frac < 0.6 or count(dist(u.pos, me().pos) <= 5 for u in allies()) == 0:
        return 0
    v = best(enemies(), lambda u: unit_gems(u))
    if not exists(v) or unit_gems(v) < 10 or dist(v.pos, me().pos) > 7:
        return 0
    return dist(v.pos, me().pos) - dist(v.pos, t)

"""
ESCG = """@gene("new", "how much farther a step takes me from the awake camps and enemies that can hit me", parents=["s1"])
def escape_gain(t: Tile) -> Num:
    return sum(dist(u.pos, t) - dist(u.pos, me().pos) for u in camps() if is_awake(u) and dist(u.pos, me().pos) <= u.attack_range + 1) + sum(dist(u.pos, t) - dist(u.pos, me().pos) for u in enemies() if dist(u.pos, me().pos) <= u.attack_range + 2)

"""
NAMES = []
MV = "        return 50 if progress(o.tile) > 0 else 0\n"
def editable(seq):
    u = json.load(open(f'/root/z19/queue/req-{seq}.json'))['user']
    return re.findall(r"## EDITABLE gene (\w+) ", u)
def fixed_names(seq):
    u = json.load(open(f'/root/z19/queue/req-{seq}.json'))['user']
    return re.findall(r"^- (\w+)\(", u, re.M)
def t_score(s, names):
    out = {}
    for nm, f in (('focus', focus), ('later', later)):
        s2 = f(s)
        if s2 != s: out[nm] = s2
    e = s.replace("me().health_frac < 0.25 and threat_at(me().pos) == 0", "me().health_frac < 0.3 and threat_at(me().pos) == 0").replace("if me().health_frac < 0.3 and threat_at(me().pos) > 0:", "if me().health_frac < 0.35 and threat_at(me().pos) > 0:")
    if e != s: out['earlier'] = desc(e, "earlier recall and retreat")
    try:
        wk = wake(s); out['wake'] = wk
    except AssertionError: pass
    if 'chase_gain' not in s and MV in s and 'chase_gain' not in names:
        out['chase'] = (desc(s.replace(MV, "        if chase_gain(o.tile) > 0:\n            return 55\n" + MV), "chase weak enemy champions"), CHASE)
    a = "    if o.kind == MOVE:\n"
    if s.count(a) == 1 and 'outnumbered' not in names and 'outnumbered' not in s:
        out['outnum'] = (desc(s.replace(a, a + "        if outnumbered() and dist(nearest(enemy_tiles(), o.tile), o.tile) > dist(nearest(enemy_tiles(), me().pos), me().pos):\n            return 90\n"), "back off when outnumbered"), OUTN)
    hc = "        if chase_gain(o.tile) > 0:\n            return 55\n"
    if hc in s and 'hunt_gain' not in names and 'hunt_gain' not in s:
        out['hunt'] = (desc(s.replace(hc, "        if hunt_gain(o.tile) > 0:\n            return 62\n" + hc), "hunt gem carriers"), HUNT)
    m = re.search(r"            return (\d+) if threat_at\(o\.tile\) < threat_at\(me\(\)\.pos\) else 0\n", s)
    if m and 'escape_gain' not in names and 'escape_gain' not in s:
        out['escgain'] = (desc(s.replace(m.group(0), f"            return {m.group(1)} if threat_at(o.tile) < threat_at(me().pos) or escape_gain(o.tile) > 0 else 0\n"), "step away from hitters even when cornered"), ESCG)
    if 'focus' in out and 'later' in out: out['focus+later'] = focus(later(s))
    return out
def home(gf, t):
    if "my_spawn()" in gf:
        gf2 = re.sub(r"me\(\)\.health_frac < [\d.]+ and gems\(\) == 0", f"me().health_frac < {t} and gems() == 0", gf)
        return gf2 if gf2 != gf else None
    m = re.search(r"    return (field\(.*\))\n", gf)
    if not m or gf.count("return") != 1: return None
    head = gf[:gf.index("def goal_field")]
    return desc(head, "home when hurt and empty-handed") + f"def goal_field() -> Field:\n    if me().health_frac < {t} and gems() == 0:\n        return field(my_spawn())\n    return {m.group(1)}\n\n"
def t_goal_field(gf, names):
    out = {}
    for t in ("0.3", "0.35", "0.4"):
        h = home(gf, t)
        if h: out['home' + t] = h
    if 'gem_first' not in gf and 'gem_first' not in names and gf.count('return field(goals()') == 1 and 'type_spawns(GEM' not in gf:
        out['gemfirst'] = (gf.replace("field(goals()", "field(gem_first(goals())", 1).replace("goals())\n", "goals()))\n", 1), GEMF)
    return out
def t_goals(gg):
    out = {}
    if "+ 8:" in gg:
        out['m4'] = desc(gg.replace("+ 8:", "+ 4:"), "narrow gem margin"); out['m14'] = desc(gg.replace("+ 8:", "+ 14:"), "wider gem margin")
    a = "    if gems() >= 10 or (gems() > 0 and round() > 1900):\n"
    if a in gg:
        out['bankhurt'] = desc(gg.replace(a, "    if gems() >= 10 or (gems() > 0 and (round() > 1900 or me().health_frac < 0.4)):\n"), "bank early when hurt")
        out['bankclose'] = desc(gg.replace(a, "    if gems() >= 10 or (gems() >= 4 and dist(nearest(altars() - locked_altars(), me().pos), me().pos) <= 10) or (gems() > 0 and round() > 1900):\n"), "bank small bags when an altar is close")
    b = "    if gems() > 0:\n        acc = near(tile(-5, -5), 0)\n"
    if b in gg:
        out['finish'] = desc(gg.replace(b, "    if gems() > 0 and not (gems() < 7 and count(is_awake(u) for u in camps()) > 0):\n        acc = near(tile(-5, -5), 0)\n"), "finish fights before banking a small bag")
    if "+ 8:" not in gg and "GEM_CLUSTER" not in gg:
        m = re.search(r"    return (acc - [^\n]*)\n$", gg.rstrip() + "\n")
        if m:
            out['gc2'] = desc(gg.replace(f"    return {m.group(1)}\n", f"    rest = {m.group(1)}\n    gem = acc & type_spawns(GEM_CLUSTER)\n    if size(gem) > 0:\n        if dist(nearest(gem, me().pos), me().pos) <= dist(nearest(rest, me().pos), me().pos) + 8:\n            return gem\n    return rest\n"), "gem clusters first when close")
    return out
def t_cast(c):
    out = {}
    a = "        if exists(o.unit) and (o.unit.is_champion or (o.unit.is_camp and (gems() == 0 or is_awake(o.unit)))):\n            return 85\n"
    a2 = "        if exists(o.unit) and (o.unit.is_champion or (o.unit.is_camp and (gems() < 10 or is_awake(o.unit)))):\n            return 85\n"
    for x in (a, a2):
        if x in c:
            cond = "(gems() == 0 or is_awake(o.unit))" if x == a else "(gems() < 10 or is_awake(o.unit))"
            out['champfirst'] = desc(c.replace(x, f"        if exists(o.unit) and o.unit.is_champion:\n            return 88\n        if exists(o.unit) and o.unit.is_camp and {cond}:\n            return 85 + 3 * (1 - o.unit.health_frac)\n"), "spells on champions first")
    a = "    if k == AB_HEAL:\n"
    if 'AB_DASH' not in c and c.count(a) == 1 and 'progress' in NAMES:
        if 'threat_at' in NAMES:
            out['dash'] = desc(c.replace(a, "    if k == AB_DASH:\n        if me().health_frac < 0.3 and threat_at(me().pos) > 0:\n            return 105 if threat_at(o.tile) < threat_at(me().pos) else 0\n        return 52 if progress(o.tile) >= 2 else 0\n" + a), "dash toward goals or away from danger")
        else:
            out['dash'] = desc(c.replace(a, "    if k == AB_DASH:\n        return 52 if progress(o.tile) >= 2 else 0\n" + a), "dash toward goals")
    c2 = c.replace("(o.unit.is_camp and gems() == 0)", "(o.unit.is_camp and (gems() == 0 or is_awake(o.unit)))").replace("(o.unit.is_camp and gems() < 10)", "(o.unit.is_camp and (gems() < 10 or is_awake(o.unit)))").replace("o.unit.health_frac < 0.6 else 0", "o.unit.health_frac < 0.75 else 0")
    if c2 != c: out['cvt'] = desc(c2, "finish awake camps, heal earlier")
    return out

def t_progress(p, names):
    out = {}
    if 'threat_at' in names and 'threat_at' not in p:
        out['escape'] = """@gene("s4", "how much closer a step brings me to the goals; when hurt under fire, how much safer it is")
def progress(t: Tile) -> Num:
    if me().health_frac < 0.3 and threat_at(me().pos) > 0:
        return threat_at(me().pos) - threat_at(t)
    return at(goal_field(), me().pos) - at(goal_field(), t)

"""
    return out
def t_threat(t):
    out = {}
    t2 = t.replace("dist(u.pos, t) <= u.attack_range for u in camps()", "dist(u.pos, t) <= u.attack_range + 1 for u in camps()")
    if t2 != t: out['margin'] = desc(t2, "with a one tile margin")
    return out
def t_chase(c):
    out = {}
    c2 = c.replace("dist(v.pos, me().pos) > 6", "dist(v.pos, me().pos) > 8")
    if c2 != c: out['range8'] = desc(c2, "longer reach")
    c3 = c.replace("v.health_frac > 0.5", "v.health_frac > 0.6")
    if c3 != c: out['hp6'] = desc(c3, "chase sooner")
    return out

def cross_candidates(seq):
    u = json.load(open(f'/root/z19/queue/req-{seq}.json'))['user']
    A, B = re.findall(r"```python\n(.*?)```", u, re.S)[:2]
    sa, sb = [float(x) for x in re.findall(r"Parent \w \(score ([\d.]+)\)", u)]
    P, Q = (A, B) if sa >= sb else (B, A)
    fn = lambda src: re.findall(r"\ndef (\w+)\(", "\n" + src)
    out = []
    qonly = "".join(g(Q, f) for f in fn(Q) if f not in fn(P))
    for f in fn(P):
        if f in fn(Q) and edit_norm(g(P, f)) != edit_norm(g(Q, f)):
            out.append((f'take:{f}', P.replace(g(P, f), g(Q, f)).rstrip() + "\n\n" + qonly))
    # also plain transforms of P's score and goal_field
    for k, v in t_score(g(P, 'score'), fn(P)).items():
        if isinstance(v, str): out.append((f'P-score:{k}', P.replace(g(P, 'score'), v)))
        else: out.append((f'P-score:{k}', P.replace(g(P, 'score'), v[0]).rstrip() + '\n\n' + v[1]))
    global NAMES
    NAMES = fn(P)
    if 'cast_value' in fn(P):
        for k, v in t_cast(g(P, 'cast_value')).items(): out.append((f'P-cast:{k}', P.replace(g(P, 'cast_value'), v)))
    if 'goal_field' in fn(P):
        for k, v in t_goal_field(g(P, 'goal_field'), fn(P)).items():
            if isinstance(v, str): out.append((f'P-gf:{k}', P.replace(g(P, 'goal_field'), v)))
    return out
def edit_norm(t):
    return re.sub(r"@gene\([^\n]*\n", "", t).strip()
def candidates(seq):
    ed_ = editable(seq); names = fixed_names(seq)
    per = {}
    if 'score' in ed_: per['score'] = t_score(ed(seq, 'score'), names)
    if 'goal_field' in ed_: per['goal_field'] = t_goal_field(ed(seq, 'goal_field'), names)
    if 'goals' in ed_: per['goals'] = t_goals(ed(seq, 'goals'))
    global NAMES
    NAMES = names + ed_
    if 'cast_value' in ed_: per['cast_value'] = t_cast(ed(seq, 'cast_value'))
    if 'progress' in ed_: per['progress'] = t_progress(ed(seq, 'progress'), names)
    if 'threat_at' in ed_: per['threat_at'] = t_threat(ed(seq, 'threat_at'))
    if 'chase_gain' in ed_: per['chase_gain'] = t_chase(ed(seq, 'chase_gain'))
    if 'gem_first' in ed_:
        gf = ed(seq, 'gem_first'); m = re.search(r"\+ (\d+):", gf)
        if m: per['gem_first'] = {f'gm{v}': desc(gf.replace(f"+ {m.group(1)}:", f"+ {v}:"), "margin tweak") for v in (4, 12) if str(v) != m.group(1)}
    cands = []
    for gname, opts in per.items():
        for k, v in opts.items():
            txt = v if isinstance(v, str) else v[0] + v[1]
            cands.append((f'{gname}:{k}', txt))
    # pairwise combos across genes (first two genes)
    keys = list(per)
    if len(keys) >= 2:
        import itertools
        for (g1, o1), (g2, o2) in itertools.combinations(per.items(), 2):
            for k1, v1 in list(o1.items())[:2]:
                for k2, v2 in list(o2.items())[:2]:
                    t1 = v1 if isinstance(v1, str) else v1[0] + v1[1]
                    t2 = v2 if isinstance(v2, str) else v2[0] + v2[1]
                    if 'gem_first' in t1 and 'gem_first' in t2 and '@gene("new", "goal tiles' in t1 and '@gene("new", "goal tiles' in t2: continue
                    cands.append((f'{g1}:{k1}+{g2}:{k2}', t1 + t2))
    return cands
if __name__ == '__main__':
    seq = int(sys.argv[1]); panel = sys.argv[2]; games = sys.argv[3] if len(sys.argv) > 3 else '16'
    res = []
    import random
    cs = cross_candidates(seq) if 'mutate one link' not in json.load(open(f'/root/z19/queue/req-{seq}.json'))['system'] else candidates(seq); random.Random(seq).shuffle(cs)
    pri = ('dash', 'outnum', 'hunt')
    cs = [c for c in cs if any(p in c[0] for p in pri) and '+' not in c[0]][:2] + [c for c in cs if not (any(p in c[0] for p in pri) and '+' not in c[0])]
    for name, txt in cs[:int(os.environ.get("CAP", "6"))]:
        p = f'/root/w/d/{seq}.{re.sub(r"[^a-z0-9]+", "_", name.lower())}.txt'
        open(p, 'w').write("```python\n" + txt + "```\n")
        v = subprocess.run(['python3', '/root/w/val.py', str(seq), p], capture_output=True, text=True)
        if 'BUILD OK' not in v.stdout:
            print(name, 'INVALID', (v.stdout + v.stderr)[-200:]); continue
        os.rename(f'/root/w/child-{seq}.genome', p + '.genome')
        r = subprocess.run(['python3', '/root/w/panel.py', p + '.genome', panel, games], capture_output=True, text=True, env=dict(os.environ, T='2'))
        sc = float(r.stdout.split()[1]) if r.stdout.startswith('panel') else -1
        print(f'{sc:.3f} {name}', flush=True); res.append((sc, name, p))
    res.sort(reverse=True)
    if res:
        print('BEST', res[0]); open(f'/root/w/d/{seq}.best', 'w').write(res[0][2])
