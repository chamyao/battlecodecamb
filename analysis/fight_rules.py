"""Top teams' fighting as decision rules: per champion type, from their side of our games.

Usage: python3 fight_rules.py EXDIR FETCHDIR [--teams "A,B,C"] [TEAM]

An engagement starts when one of their champions damages one of ours (attack or cast) after
>= 10 rounds without damaging any of ours, and ends after 6 rounds without damage. Per
engagement:
- approach: distance to the target 10, 5 and 0 rounds before the first hit, and whether the
  attacker stood in a bush during the 3 rounds before;
- conditions at the first hit: own HP fraction, target HP fraction, own allies and our champions
  within 5 tiles, target carrying gems, target the lowest-HP / closest of our visible champions;
- opening: first action (basic attack or ability slot/type), first three actions, rounds from the
  first hit to the first ability cast;
- range kept: Chebyshev distance at each basic attack;
- outcome: kill, rounds, chase (tiles the attacker moved during the engagement), the attacker's
  HP at the end, and whether it recalled within 10 rounds.
Also, items bought by round 200 per champion type, and the opening route (position every 25
rounds up to the first engagement).
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo
from analyse import CH, item_name

TYPES = {0: 'none', 1: 'attack reset', 2: 'damage', 3: 'aoe', 4: 'cc', 5: 'heal', 6: 'dash', 7: 'shield'}


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def q(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def fmt(xs, digits=0):
    xs = [x for x in xs if x is not None]
    if not xs:
        return '-'
    f = (lambda v: f'{v:.{digits}f}') if digits else (lambda v: f'{v:.0f}')
    return f"{f(statistics.median(xs))} [{f(q(xs, 0.25))}-{f(q(xs, 0.75))}] n={len(xs)}"


def engagements(d, us, m):
    team = {c['i']: c['team'] for c in d['champions']}
    ctype = {c['i']: CH[c['type']] for c in d['champions']}
    R = {r: cs for r, _, _, cs in d['rounds']}
    bushes = m['bushes']
    acts = collections.defaultdict(list)            # their champion -> [(round, kind, slot, type, target)]
    hits = collections.defaultdict(list)            # their champion -> [(round, our target)]
    kills = collections.defaultdict(list)           # their champion -> [(round, victim)]
    recalls = collections.defaultdict(list)
    for e in d['events']:
        if e['a'][0] != 1 or team.get(e['a'][1]) == us:
            continue
        k = e['a'][1]
        tg = e.get('tg')
        if e['k'] in ('Attack', 'Cast ability'):
            on_us = tg and tg[0] == 'C' and team.get(tg[1]) == us
            dmg_us = [y['i'] for y in e.get('d', []) if team[y['i']] == us and y.get('hp', 0) < 0]
            acts[k].append((e['r'], e['k'], e.get('sl'), TYPES.get(e.get('ty')), tg[1] if on_us else None))
            for v in ([tg[1]] if on_us else []) + [x for x in dmg_us if not (on_us and x == tg[1])]:
                hits[k].append((e['r'], v))
        if e['k'] == 'Recall':
            recalls[k].append(e['r'])
        for y in e.get('d', []):
            if y.get('alive') == 0 and team[y['i']] == us:
                kills[k].append((e['r'], y['i']))
    out = []
    for k, H in hits.items():
        H.sort()
        start = None
        last = -99
        for r, v in H + [(10 ** 9, None)]:
            if start is not None and r - last > 6:
                out.append((k, start, last, tgt))
                start = None
            if v is None:
                break
            if start is None and r - last >= 10:
                start, tgt = r, v
            elif start is None:
                start, tgt = r, v
            last = r
    res = []
    for k, r0, r1, v in out:
        cs, pre = R.get(r0 - 1), R.get(r0)
        if not cs:
            continue
        me_p = (cs[k][4], cs[k][5]); v_p = (cs[v][4], cs[v][5])

        def dist_at(r):
            c = R.get(r)
            return cheb((c[k][4], c[k][5]), (c[v][4], c[v][5])) if c and c[k][2] and c[v][2] else None
        vis = [i for i, c in enumerate(cs) if team[i] == us and c[2] and cheb((c[4], c[5]), me_p) <= 8]
        hpf = lambda c: c[6] / c[7] if c[7] else 0
        lowest = min(vis, key=lambda i: hpf(cs[i])) if vis else None
        closest = min(vis, key=lambda i: cheb((cs[i][4], cs[i][5]), me_p)) if vis else None
        A = [a for a in acts[k] if r0 <= a[0] <= r1]
        first_cast = next((a[0] for a in A if a[1] == 'Cast ability'), None)
        moved = 0
        for r in range(r0, r1):
            a, b = R.get(r), R.get(r + 1)
            if a and b and a[k][2] and b[k][2]:
                moved += cheb((a[k][4], a[k][5]), (b[k][4], b[k][5]))
        end = R.get(r1 + 1) or R.get(r1)
        res.append(dict(
            champ=ctype[k], r0=r0, dur=r1 - r0 + 1,
            d10=dist_at(r0 - 10), d5=dist_at(r0 - 5), d0=cheb(me_p, v_p),
            bush=any((R.get(r) and (R[r][k][4], R[r][k][5]) in bushes) for r in range(r0 - 3, r0)),
            hp=hpf(cs[k]), thp=hpf(cs[v]),
            allies=sum(1 for i, c in enumerate(cs) if team[i] != us and i != k and c[2] and cheb((c[4], c[5]), me_p) <= 5),
            enemies=sum(1 for i, c in enumerate(cs) if team[i] == us and c[2] and cheb((c[4], c[5]), me_p) <= 5),
            carrier=cs[v][1] > 0, lowest=(lowest == v), closest=(closest == v),
            first=(f"ability s{A[0][2]} {A[0][3]}" if A and A[0][1] == 'Cast ability' else 'basic attack') if A else '?',
            seq=' > '.join(('B' if a[1] == 'Attack' else f"S{a[2]}:{a[3]}") for a in A[:3]),
            cast_delay=(first_cast - r0) if first_cast is not None else None,
            ranges=[cheb((R[a[0] - 1][k][4], R[a[0] - 1][k][5]), (R[a[0] - 1][a[4]][4], R[a[0] - 1][a[4]][5]))
                    for a in A if a[1] == 'Attack' and a[4] is not None and R.get(a[0] - 1)],
            kill=any(r0 <= r <= r1 + 1 for r, _ in kills[k]), chase=moved,
            hp_end=hpf(end[k]) if end and end[k][2] else 0.0,
            recall10=any(r1 <= r <= r1 + 10 for r in recalls[k])))
    return res


def items_by(d, t, rmax=200):
    out = collections.defaultdict(collections.Counter)
    team = {c['i']: c['team'] for c in d['champions']}
    for e in d['events']:
        if e['k'] == 'Shop' and e['r'] <= rmax:
            for y in e.get('d', []):
                if team[y['i']] == t:
                    for j, n in y.get('items', []):
                        if n > 0:
                            out[CH[d['champions'][y['i']]['type']]][item_name(j)] += n
                    for j, n in y.get('cons', []):
                        if n > 0:
                            out[CH[d['champions'][y['i']]['type']]][{0: 'teleport', 2: 'altar lock'}.get(j, str(j))] += n
    return out


def main(exdir, fetchdir, me='Master', teams=None):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    E = []
    items = collections.defaultdict(collections.Counter)
    games_with = collections.Counter()
    for key, v in sides.items():
        path = os.path.join(exdir, 'ladder', v['file'])
        if not os.path.exists(path):
            continue
        us = 0 if v['A'] == me else 1
        o = v['B'] if us == 0 else v['A']
        if teams and o not in teams:
            continue
        d = json.load(open(path))
        m = mapinfo.replay_map(d['file'])
        sp = [((a[0] + a[2]) / 2, (a[1] + a[3]) / 2) for a in m['spawn']]
        R = {r: cs for r, _, _, cs in d['rounds']}
        for x in engagements(d, us, m):
            x['opp'] = o
            x['game'] = key
            cs = R.get(x['r0'] - 1)
            if cs:
                p = next(((c[4], c[5]) for i, c in enumerate(cs) if d['champions'][i]['team'] != us and CH[d['champions'][i]['type']] == x['champ']), None)
                if p:
                    x['our_half'] = cheb(p, sp[us]) < cheb(p, sp[1 - us])
            E.append(x)
        for ch, c in items_by(d, 1 - us).items():
            items[ch].update(c)
            games_with[ch] += 1
    P = print
    P(f"{len(E)} engagements by {len(set(x['opp'] for x in E))} teams\n")
    for ch in sorted(set(x['champ'] for x in E), key=lambda c: -sum(1 for x in E if x['champ'] == c)):
        X = [x for x in E if x['champ'] == ch]
        n = len(X)
        P(f"## {ch} ({n} engagements, kill rate {100 * sum(x['kill'] for x in X) / n:.0f}%)\n")
        P(f"- approach: distance to target 10 rounds before {fmt([x['d10'] for x in X])}, 5 before {fmt([x['d5'] for x in X])}, at first hit {fmt([x['d0'] for x in X])}; from a bush in the 3 rounds before: {100 * sum(x['bush'] for x in X) / n:.0f}%")
        P(f"- conditions at first hit: own HP {fmt([x['hp'] for x in X], 2)}, target HP {fmt([x['thp'] for x in X], 2)}, own allies within 5 {fmt([x['allies'] for x in X])}, our champions within 5 {fmt([x['enemies'] for x in X])}")
        P(f"- target: carrier {100 * sum(x['carrier'] for x in X) / n:.0f}%, lowest-HP visible {100 * sum(x['lowest'] for x in X) / n:.0f}%, closest visible {100 * sum(x['closest'] for x in X) / n:.0f}%")
        fc = collections.Counter(x['first'] for x in X)
        sq = collections.Counter(x['seq'] for x in X)
        P(f"- opening: first action {', '.join(f'{k} {100 * v / n:.0f}%' for k, v in fc.most_common(4))}; first three: {', '.join(f'{k} ({v})' for k, v in sq.most_common(4))}; rounds from first hit to first cast {fmt([x['cast_delay'] for x in X])}")
        rg = collections.Counter(r for x in X for r in x['ranges'])
        tot = sum(rg.values())
        P(f"- basic attack range kept: {', '.join(f'{k}: {100 * v / tot:.0f}%' for k, v in sorted(rg.items()))}" if tot else '- basic attack range kept: -')
        P(f"- engagement: rounds {fmt([x['dur'] for x in X])}, chase (tiles moved) {fmt([x['chase'] for x in X])}; kills {fmt([x['chase'] for x in X if x['kill']])} tiles chased")
        P(f"- disengage: own HP at end {fmt([x['hp_end'] for x in X], 2)} (no kill: {fmt([x['hp_end'] for x in X if not x['kill']], 2)}); recall within 10 rounds {100 * sum(x['recall10'] for x in X) / n:.0f}%")
        tot_items = sum(items[ch].values())
        P(f"- items by round 200 ({games_with[ch]} games): " + ', '.join(f"{k} {v / max(1, games_with[ch]):.1f}" for k, v in items[ch].most_common(5)) + '\n')
    firsts = {}
    for x in E:
        if x['game'] not in firsts or x['r0'] < firsts[x['game']]['r0']:
            firsts[x['game']] = x
    F = list(firsts.values())
    P('First engagement per game: round ' + fmt([x['r0'] for x in F]) + f"; in our half of the map {100 * sum(1 for x in F if x.get('our_half')) / max(1, len(F)):.0f}%; by " +
      ', '.join(f'{k} {v}' for k, v in collections.Counter(x['champ'] for x in F).most_common(4)))
    P(f"All engagements in our half of the map: {100 * sum(1 for x in E if x.get('our_half')) / max(1, len(E)):.0f}%")
    return E


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    teams = None
    if '--teams' in args:
        i = args.index('--teams'); teams = set(args[i + 1].split(',')); del args[i:i + 2]
    main(*args, teams=teams)
