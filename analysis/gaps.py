"""Gap list: specific, measurable behaviours of OUR bot in real games, with frequency, cost and
standard errors, split by wins and losses.

Usage: python3 gaps.py LABEL=EXDIR,FETCHDIR [...] [--json OUT]
All LABEL datasets are pooled (e.g. the band games of one version). Per game it measures our deaths
(to champions) by context, low-HP crossings and what followed, the state before each crossing, and
both sides' max HP / strength / focus at rounds 200, 400 and 600. Standard errors are bootstrap
(1000 resamples of games). Champion damage is post-shield HP lost by enemy champions (replay diffs),
the sim's TeamState.champ_damage without overkill.
"""
import collections, json, os, random, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, fight_dump, mapinfo
from analyse import CH


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def game(d, us, m, summ):
    team = {c['i']: c['team'] for c in d['champions']}
    name = {c['i']: CH[c['type']] for c in d['champions']}
    R = {r: cs for r, _, _, cs in d['rounds']}
    spawn = [set((x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])) for a in m['spawn']]
    altars = [tuple(a) for a in m['altars']]
    ours = [i for i in team if team[i] == us]
    theirs = [i for i in team if team[i] != us]
    g = collections.Counter()
    lists = collections.defaultdict(list)
    # per-round action index
    recall_r = collections.defaultdict(set)
    camp_r = collections.defaultdict(set)
    tribute_r = collections.defaultdict(set)
    hits = []                                    # (round, attacker, victim, dmg)
    for e in d['events']:
        if e['a'][0] != 1 or e['a'][1] not in team:
            continue
        a = e['a'][1]
        if e['k'] == 'Recall':
            recall_r[a].add(e['r'])
        elif e['k'] == 'Submit gems':
            tribute_r[a].add(e['r'])
        elif e['k'] == 'Attack' and (e.get('tg') or [None])[0] == 'M':
            camp_r[a].add(e['r'])
        if e['k'] in ('Attack', 'Cast ability'):
            for y in e.get('d', []):
                if y['i'] in team and team[y['i']] != team[a] and y.get('hp', 0) < 0:
                    hits.append((e['r'], a, y['i'], -y['hp']))
    g['dmg_us'] = sum(h[3] for h in hits if team[h[1]] == us)
    g['dmg_them'] = sum(h[3] for h in hits if team[h[1]] != us)
    hits_on = collections.defaultdict(list)
    for h in hits:
        hits_on[h[2]].append(h)
    # deaths to champions
    first_kill = None
    for e in d['events']:
        if e['a'][0] != 1 or e['a'][1] not in team or team[e['a'][1]] == us:
            continue
        for y in e.get('d', []):
            if y.get('alive') != 0 or y['i'] not in team or team[y['i']] != us:
                continue
            r, v = e['r'], y['i']
            cs = R.get(r - 1)
            if not cs:
                continue
            vp = (cs[v][4], cs[v][5])
            n_them = sum(1 for j in theirs if cs[j][2] and cheb((cs[j][4], cs[j][5]), vp) <= 5)
            n_us = sum(1 for j in ours if j != v and cs[j][2] and cheb((cs[j][4], cs[j][5]), vp) <= 5)
            bag = cs[v][1]
            g['deaths'] += 1
            g['d_outnumbered'] += n_them >= 2
            g['d_outnumbered_strict'] += n_them > n_us + 1
            g['d_carrying'] += bag > 0
            g['gems_lost'] += bag
            g['d_mid_recall'] += any(r - 5 <= k <= r for k in recall_r[v])
            g['d_farming_enemy_seen'] += any(r - 5 <= k < r for k in camp_r[v])
            if bag > 0:
                lists['altar_dist_carrier_death'].append(min(cheb(vp, a) for a in altars))
            if first_kill is None:
                first_kill = r
                lists['first_kill'] = [dict(round=r, bag=bag, hp_frac=None, n_them=n_them, n_us=n_us)]
    g['first_kill_round'] = first_kill or 0
    g['has_first_kill'] = first_kill is not None
    # low-HP crossings: what followed and what came before
    for r in sorted(R):
        a, b = R.get(r - 1), R[r]
        if not a:
            continue
        for i in ours:
            c = b[i]
            if not (c[2] and a[i][2] and c[7] and a[i][6] / a[i][7] >= 0.5 and c[6] / c[7] < 0.5):
                continue
            ip = (c[4], c[5])
            if not any(b[j][2] and cheb((b[j][4], b[j][5]), ip) <= 5 for j in theirs):
                continue
            g['crossings'] += 1
            died_at = next((k for k in range(r + 1, r + 16) if R.get(k) and not R[k][i][2]), None)
            home = next((k for k in range(r + 1, r + 16) if R.get(k) and R[k][i][2] and (R[k][i][4], R[k][i][5]) in spawn[us]), None)
            if died_at and not (home and home < died_at):
                g['cross_died'] += 1
                if died_at - r <= 2:
                    g['cross_burst'] += 1
                elif any(r <= k < died_at for k in recall_r[i]):
                    g['cross_mid_recall'] += 1
                else:
                    sp = min(spawn[us], key=lambda t: cheb(t, ip))
                    p1 = R.get(died_at - 1)
                    if p1 and cheb((p1[i][4], p1[i][5]), sp) < cheb(ip, sp) - 1:
                        g['cross_going_home'] += 1
                    else:
                        g['cross_other'] += 1
            # the engagement that led here: first damage between this champion and an enemy in the 20 rounds before
            H = [h for h in hits if r - 20 <= h[0] <= r and (h[2] == i or h[1] == i)]
            if not H:
                continue
            h0 = min(H)
            r0 = h0[0]
            cs = R.get(r0 - 1)
            if not cs:
                continue
            p0 = (cs[i][4], cs[i][5])
            foe = h0[1] if h0[2] == i else h0[2]
            pre = dict(
                died=bool(died_at and not (home and home < died_at)),
                they_first=h0[2] == i, range=cheb((cs[h0[1]][4], cs[h0[1]][5]), (cs[h0[2]][4], cs[h0[2]][5])),
                n_them=sum(1 for j in theirs if cs[j][2] and cheb((cs[j][4], cs[j][5]), p0) <= 5),
                n_us=1 + sum(1 for j in ours if j != i and cs[j][2] and cheb((cs[j][4], cs[j][5]), p0) <= 5),
                carrying=cs[i][1] > 0, farming=any(r0 - 3 <= k <= r0 for k in camp_r[i]),
                channel=any(r0 - 5 <= k <= r0 for k in recall_r[i] | tribute_r[i]),
                hp=cs[i][6] / cs[i][7], foe_hp=cs[foe][6] / cs[foe][7] if cs[foe][7] else 1,
                maxhp_gap=cs[foe][7] - cs[i][7])
            allies = [j for j in ours if j != i and cs[j][2] and cheb((cs[j][4], cs[j][5]), p0) <= 5]
            pre['ally_near'] = bool(allies)
            pre['ally_joined'] = any(h[1] in allies and r0 <= h[0] <= r for h in hits)
            lists['pre'].append(pre)
    # stat snowball
    hist = fight_dump.inventories(d)
    for rr in (200, 400, 600):
        cs = R.get(rr)
        if not cs:
            continue
        for side, ids in (('us', ours), ('them', theirs)):
            S = [fight_dump.stats_from_items(name[i], fight_dump.inv_at(hist, i, rr)) for i in ids]
            lists[f'maxhp_{rr}_{side}'] = [statistics.mean(cs[i][7] for i in ids)]
            lists[f'str_{rr}_{side}'] = [statistics.mean(s['str'] for s in S)]
            lists[f'foc_{rr}_{side}'] = [statistics.mean(s['focus'] for s in S)]
            lists[f'pts_{rr}_{side}'] = [statistics.mean(sum(s['pts'].values()) for s in S)]
    return g, lists


def boot(games, f, n=1000):
    """Point estimate and bootstrap SE of a statistic over games."""
    est = f(games)
    rnd = random.Random(1)
    xs = []
    for _ in range(n):
        s = [games[rnd.randrange(len(games))] for _ in games]
        try:
            xs.append(f(s))
        except ZeroDivisionError:
            pass
    return est, statistics.pstdev(xs) if xs else 0


def main(*args):
    args = list(args)
    out = None
    if '--json' in args:
        k = args.index('--json'); out = args[k + 1]; del args[k:k + 2]
    G = []
    for s in args:
        label, dirs = s.split('=', 1)
        exdir, fd = dirs.split(',')
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            p = os.path.join(exdir, 'ladder', v['file'])
            if not os.path.exists(p):
                continue
            d = json.load(open(p))
            us = 0 if v['A'] == 'Master' else 1
            g, L = game(d, us, mapinfo.replay_map(d['file']), None)
            g['win'] = (d['outcome'] == 1) == (us == 0)
            g['gems_us'], g['gems_them'] = d['submitted'][us], d['submitted'][1 - us]
            st = analyse.game_stats(d, (v['A'], v['B']))
            for side, t in (('us', us), ('them', 1 - us)):
                x = st[t]
                caps = x['lists'].get('capture', [])
                g[f'captured_{side}'] = sum(c[2] for c in caps)
                g[f'captures_{side}'] = len(caps)
                g[f'tributes_{side}'] = len(x['lists'].get('tribute', []))
                g[f'camp_deaths_{side}'] = x.get('deaths_to_camp', 0)
                g[f'all_deaths_{side}'] = x.get('deaths', 0)
                g[f'gems_lost_all_{side}'] = x.get('gems_lost_on_death', 0)
                g[f'carried_end_{side}'] = x.get('gems_carried_at_end', 0)
            g['rounds'] = d['rounds_played']
            G.append(dict(g=g, L=L, label=label, opp=v['B'] if us == 0 else v['A'], map=v['map']))
    W = [x for x in G if x['g']['win']]
    Lo = [x for x in G if not x['g']['win']]
    P = print
    sumk = lambda gs, k: sum(x['g'][k] for x in gs)
    ratio = lambda k, base: (lambda gs: sumk(gs, k) / sumk(gs, base))
    per_game = lambda k: (lambda gs: sumk(gs, k) / len(gs))
    def fmt(f, gs, pct=False, nd=1):
        if not gs:
            return '-'
        e, se = boot(gs, f)
        return f"{100 * e:.0f}% ± {100 * se:.0f}" if pct else f"{e:.{nd}f} ± {se:.{nd}f}"
    P(f"{len(G)} games ({', '.join(sorted(set(x['label'] for x in G)))}), our record {len(W)}-{len(Lo)}\n")
    P('| metric | all games | in our wins | in our losses |')
    P('|---|---|---|---|')
    rows = [
        ('win rate', lambda gs: sum(x['g']['win'] for x in gs) / len(gs), True),
        ('gems submitted, us', per_game('gems_us'), False), ('gems submitted, them', per_game('gems_them'), False),
        ('our deaths to champions per game', per_game('deaths'), False),
        ('share of our deaths with 2+ of theirs within 5', ratio('d_outnumbered', 'deaths'), True),
        ('share of our deaths outnumbered by 2+ (theirs > ours + 1 within 5)', ratio('d_outnumbered_strict', 'deaths'), True),
        ('share of our deaths while carrying gems', ratio('d_carrying', 'deaths'), True),
        ('gems lost on death per game', per_game('gems_lost'), False),
        ('share of our deaths within 5 rounds of a recall start', ratio('d_mid_recall', 'deaths'), True),
        ('share of our deaths within 5 rounds of hitting a camp', ratio('d_farming_enemy_seen', 'deaths'), True),
        ('their first kill on us (round; games with one)', lambda gs: statistics.median([x['g']['first_kill_round'] for x in gs if x['g']['has_first_kill']]), False),
        ('champion damage (post-shield), us', per_game('dmg_us'), False), ('champion damage (post-shield), them', per_game('dmg_them'), False),
        ('low-HP crossings per game (ours, enemy within 5)', per_game('crossings'), False),
        ('  ... died within 15 rounds', ratio('cross_died', 'crossings'), True),
        ('  ... died within 2 rounds (burst)', ratio('cross_burst', 'crossings'), True),
        ('  ... died mid-recall (recall started after the crossing)', ratio('cross_mid_recall', 'crossings'), True),
        ('  ... died while heading home (walking or dashing)', ratio('cross_going_home', 'crossings'), True),
        ('  ... died otherwise (stayed in the fight)', ratio('cross_other', 'crossings'), True),
    ]
    rows += [
        ('our deaths to camps per game', per_game('camp_deaths_us'), False),
        ('gems lost on all deaths per game (champions + camps), us', per_game('gems_lost_all_us'), False),
        ('gems lost on all deaths per game, them', per_game('gems_lost_all_them'), False),
        ('gems captured per game, us', per_game('captured_us'), False), ('gems captured per game, them', per_game('captured_them'), False),
        ('gems per capture, us', ratio('captured_us', 'captures_us'), False), ('gems per capture, them', ratio('captured_them', 'captures_them'), False),
        ('share of captured gems submitted, us', ratio('gems_us', 'captured_us'), True), ('share of captured gems submitted, them', ratio('gems_them', 'captured_them'), True),
        ('tributes per game, us', per_game('tributes_us'), False), ('tributes per game, them', per_game('tributes_them'), False),
        ('rounds played', per_game('rounds'), False),
    ]
    res = {}
    for name, f, pct in rows:
        cells = [fmt(f, gs, pct) for gs in (G, W, Lo)]
        res[name] = cells
        P(f'| {name} | ' + ' | '.join(cells) + ' |')
    alt = [a for x in G for a in x['L'].get('altar_dist_carrier_death', [])]
    if alt:
        P(f"\nDistance to the nearest altar at our carrier deaths: median {statistics.median(alt)}, within 3: {100 * sum(1 for a in alt if a <= 3) / len(alt):.0f}%, 8+: {100 * sum(1 for a in alt if a >= 8) / len(alt):.0f}% (n={len(alt)})")
    # pre-crossing conditions
    pre = [p for x in G for p in x['L'].get('pre', [])]
    if pre:
        P(f"\nBefore each low-HP crossing ({len(pre)} with a first hit within 20 rounds): conditions at the first hit of that engagement, and the death rate after the crossing given the condition\n")
        P('| condition at the first hit | frequency | death rate if true | death rate if false |')
        P('|---|---|---|---|')
        conds = [('they hit first', lambda p: p['they_first']), ('first hit from range 3+', lambda p: p['range'] >= 3),
                 ('outnumbered within 5 (theirs > ours)', lambda p: p['n_them'] > p['n_us']), ('even or better numbers', lambda p: p['n_them'] <= p['n_us']),
                 ('we were carrying gems', lambda p: p['carrying']), ('we were hitting a camp (3 rounds before)', lambda p: p['farming']),
                 ('we were channelling (recall/tribute started 5 rounds before)', lambda p: p['channel']),
                 ('our HP below 0.75 at the first hit', lambda p: p['hp'] < 0.75), ('their max HP 200+ above ours', lambda p: p['maxhp_gap'] >= 200),
                 ('an ally within 5', lambda p: p['ally_near']), ('an ally within 5 that joined (damaged an enemy)', lambda p: p['ally_joined']),
                 ('an ally within 5 that did not join', lambda p: p['ally_near'] and not p['ally_joined'])]
        def se(k, n):
            return (k / n * (1 - k / n) / n) ** 0.5 if n else 0
        for cname, c in conds:
            T = [p for p in pre if c(p)]; F = [p for p in pre if not c(p)]
            dt = sum(p['died'] for p in T); df = sum(p['died'] for p in F)
            P(f"| {cname} | {100 * len(T) / len(pre):.0f}% ± {100 * se(len(T), len(pre)):.0f} | {100 * dt / max(1, len(T)):.0f}% ± {100 * se(dt, len(T)):.0f} (n={len(T)}) | {100 * df / max(1, len(F)):.0f}% ± {100 * se(df, len(F)):.0f} (n={len(F)}) |")
        P(f"\nAt the first hit (medians): our HP {statistics.median(p['hp'] for p in pre):.2f}, the foe's {statistics.median(p['foe_hp'] for p in pre):.2f}; numbers within 5, ours / theirs: {statistics.median(p['n_us'] for p in pre)} / {statistics.median(p['n_them'] for p in pre)}")
    P('\n| stat (mean per champion) | r200 us / them | r400 us / them | r600 us / them |')
    P('|---|---|---|---|')
    for k, nm in (('maxhp', 'max HP'), ('str', 'strength (basic attack damage)'), ('foc', 'focus (ability scaling)'), ('pts', 'item points')):
        cells = []
        for rr in (200, 400, 600):
            u = [x['L'][f'{k}_{rr}_us'][0] for x in G if f'{k}_{rr}_us' in x['L']]
            t = [x['L'][f'{k}_{rr}_them'][0] for x in G if f'{k}_{rr}_them' in x['L']]
            cells.append(f"{statistics.mean(u):.0f} / {statistics.mean(t):.0f} (n={len(u)})" if u else '-')
        P(f'| {nm} | ' + ' | '.join(cells) + ' |')
    if out:
        json.dump(dict(rows=res, games=[dict(x['g'], label=x['label'], opp=x['opp'], map=x['map']) for x in G]), open(out, 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
