"""Turn-by-turn dumps of decisive fights, plus aggregate first-strike / focus / range / stat checks.

Usage: python3 fight_dump.py EXDIR FETCHDIR [--teams "A,B"] [--n 8] [TEAM]

A decisive fight = one of our champions dies to an enemy champion and we kill none of theirs within
10 rounds either side. The window starts at the first champion-vs-champion damage within 10 tiles
of the victim in the 15 rounds before the death.

Stats at fight start are rebuilt from shop events (shards add the champion's growth; emblems count
as 5 shards, Power 6, Bruiser 5 + 1 of each other stat). Max HP comes from the replay itself.
Vision is approximate: line of sight within 8 tiles, blocked by walls and by bushes the target
stands in unless the viewer is in the same bush cluster (the engine uses symmetric shadowcasting).
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapinfo
from analyse import CH

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = json.load(open(os.path.join(HERE, 'design_v1_0_3.json')))['champions']
STATN = ['str', 'focus', 'health']   # item stat order: Strength, Focus, Health
TYPES = {1: 'reset', 2: 'damage', 3: 'aoe', 4: 'cc', 5: 'heal', 6: 'dash', 7: 'shield'}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def stats_from_items(name, inv):
    st = DESIGN[name]['stats']
    pts = collections.Counter()
    for j, n in inv.items():
        if n <= 0:
            continue
        fam, rest = divmod(j, 6)
        stat, emb = divmod(rest, 2)
        if not emb:
            pts[stat] += n
        elif fam == 1:                 # Power
            pts[stat] += 6 * n
        elif fam == 6:                 # Bruiser
            pts[stat] += 5 * n
            for o in range(3):
                if o != stat:
                    pts[o] += n
        else:
            pts[stat] += 5 * n
    return dict(str=st['str'] + pts[0] * st['str_g'], focus=st['focus'] + pts[1] * st['focus_g'],
                hp_items=pts[2] * st['health_g'], pts=dict(pts))


def los(m, a, b, cluster):
    """Approximate symmetric LOS: Bresenham, walls block; bushes block unless shared cluster."""
    if cheb(a, b) > 8:
        return False
    x0, y0 = a; x1, y1 = b
    n = max(abs(x1 - x0), abs(y1 - y0))
    W = m['width']
    ca = cluster[a[1] * W + a[0]]
    for s in range(1, n):
        x = round(x0 + (x1 - x0) * s / n); y = round(y0 + (y1 - y0) * s / n)
        if (x, y) in m['walls']:
            return False
        if (x, y) in m['bushes'] and cluster[y * W + x] != ca:
            return False
    if b in m['bushes'] and cluster[b[1] * W + b[0]] != ca:
        return False
    return True


def load(exdir, v):
    d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
    return d, mapinfo.replay_map(d['file'])


def inventories(d):
    """champion -> list of (round, inventory Counter after that round's purchases)."""
    inv = collections.defaultdict(collections.Counter)
    hist = collections.defaultdict(list)
    for e in d['events']:
        if e['k'] == 'Shop':
            for y in e.get('d', []):
                for j, n in y.get('items', []):
                    inv[y['i']][j] += n
                hist[y['i']].append((e['r'], collections.Counter(inv[y['i']])))
    return hist


def inv_at(hist, i, r):
    cur = collections.Counter()
    for rr, c in hist.get(i, []):
        if rr <= r:
            cur = c
    return cur


def decisive(d, us):
    team = {c['i']: c['team'] for c in d['champions']}
    deaths = []
    our_kills = []
    for e in d['events']:
        for y in e.get('d', []):
            if y.get('alive') == 0 and e['a'][0] == 1:
                if team[y['i']] == us and team[e['a'][1]] != us:
                    deaths.append((e['r'], y['i'], e['a'][1]))
                elif team[y['i']] != us and team[e['a'][1]] == us:
                    our_kills.append(e['r'])
    return [x for x in deaths if not any(abs(k - x[0]) <= 10 for k in our_kills)]


def dump(d, m, us, death, out):
    r_death, victim, killer = death
    team = {c['i']: c['team'] for c in d['champions']}
    name = {c['i']: CH[c['type']] for c in d['champions']}
    R = {r: cs for r, _, _, cs in d['rounds']}
    hist = inventories(d)
    vp = (R[r_death - 1][victim][4], R[r_death - 1][victim][5])
    # fight start: first champion-vs-champion damage near the victim in the 15 rounds before
    r0 = r_death
    for e in d['events']:
        if r_death - 15 <= e['r'] <= r_death and e['k'] in ('Attack', 'Cast ability') and e['a'][0] == 1:
            if any(team[y['i']] != team[e['a'][1]] and y.get('hp', 0) < 0 for y in e.get('d', [])):
                cs = R.get(e['r'] - 1)
                if cs and cheb((cs[e['a'][1]][4], cs[e['a'][1]][5]), vp) <= 10:
                    r0 = min(r0, e['r'])
    cs0 = R[r0 - 1]
    near = [i for i, c in enumerate(cs0) if c[2] and cheb((c[4], c[5]), vp) <= 10]
    out.append(f"\n### {name[victim]} (ours) killed by {name[killer]}, round {r_death}; fight from round {r0}\n")
    out.append('Champions within 10 tiles at the start (stats rebuilt from purchases):\n')
    out.append('| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |')
    out.append('|---|---|---|---|---|---|---|---|')
    for i in near:
        c = cs0[i]
        s = stats_from_items(name[i], inv_at(hist, i, r0 - 1))
        out.append(f"| {'us' if team[i] == us else 'them'} | {name[i]} | ({c[4]},{c[5]}) | {c[6]} / {c[7]} | {c[1]} | {s['str']:.0f} | {s['focus']:.0f} | {dict((STATN[k], v) for k, v in s['pts'].items())} |")
    # vision before first hit: did any of ours see each of theirs in the 5 rounds before r0?
    seen = {}
    for i in near:
        if team[i] == us:
            continue
        flags = []
        for r in range(r0 - 5, r0):
            c = R.get(r)
            if not c or not c[i][2]:
                flags.append('-'); continue
            p = (c[i][4], c[i][5])
            vis = any(team[j] == us and c[j][2] and los(m, (c[j][4], c[j][5]), p, m['cluster']) for j in range(len(c)))
            flags.append('V' if vis else ('b' if p in m['bushes'] else '.'))
        seen[i] = ''.join(flags)
    out.append('\nTheir visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): ' +
               ', '.join(f"{name[i]} {f}" for i, f in seen.items()))
    out.append(f"\nRound by round (team {'A' if (r0 % 2 == 1) else 'B'} acts first in round {r0}; teams alternate each round). Actions in engine order:\n")
    acts = collections.defaultdict(list)
    for e in d['events']:
        if r0 - 2 <= e['r'] <= r_death and e['a'][0] == 1 and e['a'][1] in near and e['k'] in ('Attack', 'Cast ability', 'Recall', 'Gems submitted'):
            tg = e.get('tg')
            tgt = (name[tg[1]] + ('(us)' if team[tg[1]] == us else '(them)')) if tg and tg[0] == 'C' else ('camp' if tg and tg[0] == 'M' else (f"tile {tuple(e['t'])}" if e.get('t') else ''))
            dmg = ', '.join(f"{name[y['i']]} {y['hp']:+d}" for y in e.get('d', []) if y.get('hp')) or ''
            dead = ', '.join(f"{name[y['i']]} dies" for y in e.get('d', []) if y.get('alive') == 0)
            what = 'basic' if e['k'] == 'Attack' else (f"S{e['sl']}:{TYPES.get(e.get('ty'), e.get('ty'))}" if e['k'] == 'Cast ability' else e['k'])
            acts[e['r']].append(f"{'us' if team[e['a'][1]] == us else 'them'}:{name[e['a'][1]]} {what} -> {tgt} {('[' + dmg + ']') if dmg else ''} {dead}".strip())
    for r in range(r0 - 2, r_death + 1):
        c = R.get(r - 1)
        if not c:
            continue
        posline = '; '.join(f"{name[i][:6]}{'*' if team[i] != us else ''} ({c[i][4]},{c[i][5]}) {c[i][6]}hp d{cheb((c[i][4], c[i][5]), (c[victim][4], c[victim][5])) if c[victim][2] else '-'}" for i in near if c[i][2])
        out.append(f"- **r{r}** start: {posline}")
        for a in acts.get(r, []):
            out.append(f"  - {a}")
    return r0


def aggregates(rows):
    P = []
    n = len(rows)
    P.append(f"\n## Aggregates over all {n} decisive fights\n")
    if not n:
        return P
    fs = collections.Counter(x['first'] for x in rows)
    P.append(f"- first champion damage in the fight: {', '.join(f'{k} {100 * v / n:.0f}%' for k, v in fs.items())}")
    P.append(f"- their champions damaging the victim: {statistics.median([x['n_hitters'] for x in rows])} median; 2+ in {100 * sum(1 for x in rows if x['n_hitters'] >= 2) / n:.0f}%; rounds from first hit to death {statistics.median([x['ttk'] for x in rows])} median")
    P.append(f"- victim damaged any of theirs before dying: {100 * sum(1 for x in rows if x['victim_hit']) / n:.0f}%")
    P.append(f"- their hits on the victim from beyond the victim's own attack range: {100 * sum(x['out_range'] for x in rows) / max(1, sum(x['their_hits'] for x in rows)):.0f}% of hits")
    P.append(f"- stun/cc landed on the victim before the kill: {100 * sum(1 for x in rows if x['stunned']) / n:.0f}%")
    P.append(f"- stat gap at fight start, killer minus victim: strength {statistics.median([x['dstr'] for x in rows]):+.0f}, max HP {statistics.median([x['dhp'] for x in rows]):+.0f}, focus {statistics.median([x['dfoc'] for x in rows]):+.0f} (medians)")
    P.append(f"- killer unseen by all of ours in the 3 rounds before the first hit: {100 * sum(1 for x in rows if x['unseen']) / n:.0f}%")
    P.append(f"- their side acted first in the round of the first hit: {100 * sum(1 for x in rows if x['they_first']) / n:.0f}%")
    P.append(f"- HP fraction at fight start: victim {statistics.median([x['vfrac'] for x in rows]):.2f}, killer {statistics.median([x['kfrac'] for x in rows]):.2f} (medians); victim below 0.75: {100 * sum(1 for x in rows if x['vfrac'] < 0.75) / n:.0f}%")
    P.append(f"- victim attacking a camp in the 5 rounds before the first hit: {100 * sum(1 for x in rows if x['vcamp']) / n:.0f}%")
    for lo, hi in ((0, 150), (150, 400), (400, 9999)):
        sub = [x for x in rows if lo <= x['r0'] < hi]
        if sub:
            P.append(f"- fights starting in rounds {lo}-{hi}: {len(sub)}; item points killer {statistics.median([x['kpts'] for x in sub]):.0f} vs victim {statistics.median([x['vpts'] for x in sub]):.0f}; "
                     f"gap strength {statistics.median([x['dstr'] for x in sub]):+.0f}, focus {statistics.median([x['dfoc'] for x in sub]):+.0f}, max HP {statistics.median([x['dhp'] for x in sub]):+.0f}; "
                     f"2+ hitters {100 * sum(1 for x in sub if x['n_hitters'] >= 2) / len(sub):.0f}%; victim start HP {statistics.median([x['vfrac'] for x in sub]):.2f}")
    return P


def analyse_fight(d, m, us, death):
    r_death, victim, killer = death
    team = {c['i']: c['team'] for c in d['champions']}
    name = {c['i']: CH[c['type']] for c in d['champions']}
    R = {r: cs for r, _, _, cs in d['rounds']}
    hist = inventories(d)
    rng = {i: DESIGN[name[i]]['stats']['range'] for i in name}
    evs = [e for e in d['events'] if r_death - 15 <= e['r'] <= r_death and e['k'] in ('Attack', 'Cast ability') and e['a'][0] == 1]
    hitters, first, their_hits, out_range, stunned, victim_hit, r0 = set(), None, 0, 0, False, False, None
    for e in evs:
        a = e['a'][1]
        dmg = [y for y in e.get('d', []) if y.get('hp', 0) < 0 and team[y['i']] != team[a]]
        if not dmg:
            if e['k'] == 'Cast ability' and e.get('ty') == 4 and e.get('tg') and e['tg'][0] == 'C' and e['tg'][1] == victim:
                stunned = True
            continue
        if r0 is None:
            r0 = e['r']; first = 'them' if team[a] != us else 'us'
        if team[a] != us and any(y['i'] == victim for y in dmg):
            hitters.add(a); their_hits += 1
            cs = R.get(e['r'] - 1)
            if cs and cheb((cs[a][4], cs[a][5]), (cs[victim][4], cs[victim][5])) > rng[victim]:
                out_range += 1
            if e['k'] == 'Cast ability' and e.get('ty') in (4, 3, 6) and name[a] in ('Heart of Ruin', 'Ryth', 'Prism', 'Tavi', 'Cassi', 'Ren'):
                stunned = True
        if a == victim:
            victim_hit = True
    if r0 is None:
        return None
    sk = stats_from_items(name[killer], inv_at(hist, killer, r0 - 1)); sv = stats_from_items(name[victim], inv_at(hist, victim, r0 - 1))
    c0 = R.get(r0 - 1)
    unseen = True
    for r in range(r0 - 3, r0):
        c = R.get(r)
        if c and c[killer][2] and any(team[j] == us and c[j][2] and los(m, (c[j][4], c[j][5]), (c[killer][4], c[killer][5]), m['cluster']) for j in range(len(c))):
            unseen = False
    they_first = (r0 % 2 == 1) == (us == 1)    # team A acts first in odd rounds
    return dict(first=first, n_hitters=len(hitters), ttk=r_death - r0, victim_hit=victim_hit, their_hits=their_hits, out_range=out_range,
                stunned=stunned, dstr=sk['str'] - sv['str'], dfoc=sk['focus'] - sv['focus'],
                dhp=(c0[killer][7] - c0[victim][7]) if c0 else 0, unseen=unseen, they_first=they_first, r0=r0,
                vfrac=(c0[victim][6] / c0[victim][7]) if c0 else 1, kfrac=(c0[killer][6] / c0[killer][7]) if c0 else 1,
                vcamp=any(e['k'] == 'Attack' and e['a'] == [1, victim] and (e.get('tg') or [None])[0] == 'M' for e in d['events'] if r0 - 5 <= e['r'] < r0),
                kpts=sum(sk['pts'].values()), vpts=sum(sv['pts'].values()))


def main(exdir, fetchdir, me='Master', teams=None, n=8):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    out, rows, picked = [], [], []
    for key, v in sorted(sides.items()):
        us = 0 if v['A'] == me else 1
        o = v['B'] if us == 0 else v['A']
        if teams and o not in teams:
            continue
        d, m = load(exdir, v)
        for death in decisive(d, us):
            a = analyse_fight(d, m, us, death)
            if a:
                rows.append(a)
                picked.append((o, v['map'], d, m, us, death))
    # dump n fights: spread over teams, killer types and maps
    seen = set()
    chosen = []
    for o, mp, d, m, us, death in picked:
        k = (o, CH[d['champions'][death[2]]['type']])
        if k in seen or any(c[1] == mp for c in chosen):
            continue
        seen.add(k); chosen.append((o, mp, d, m, us, death))
        if len(chosen) >= n:
            break
    for o, mp, d, m, us, death in chosen:
        out.append(f"\n## {o} on {mp}")
        dump(d, m, us, death, out)
    print('\n'.join(aggregates(rows) + out))


if __name__ == '__main__':
    args = sys.argv[1:]
    teams, n = None, 8
    if '--teams' in args:
        i = args.index('--teams'); teams = set(args[i + 1].split(',')); del args[i:i + 2]
    if '--n' in args:
        i = args.index('--n'); n = int(args[i + 1]); del args[i:i + 2]
    main(*args, teams=teams, n=n)
