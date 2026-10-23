"""Monolith takes and Heart of Ruin behaviour in the ladder games.

Usage: python3 ladder_followup.py EXDIR SIDES.json
An attempt = a run of champion damage on one monolith with no gap > 20 rounds.
Success = that team captures the monolith's group within 30 rounds of the last hit.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import CH, camp_groups

TOP4 = {'prism best girl', 'Intercontinental Fish', 'policy wonk', 'procless'}
HOR = CH.index('Heart of Ruin')


def med(x):
    return statistics.median(x) if x else None


def pct(x, n):
    return f"{100 * x / n:.0f}%" if n else '-'


def main(exdir, sides_path):
    sides = json.load(open(sides_path))
    attempts = []
    hor = collections.defaultdict(list)
    for key, v in sides.items():
        d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
        names = (v['A'], v['B'])
        champ = {c['i']: c for c in d['champions']}
        team = {c['i']: c['team'] for c in d['champions']}
        mono = {c['i'] for c in d['camps'] if c['type'] == 4}
        groups = camp_groups(d['camps'])
        mono_tiles = {(c['x'], c['y']): gi for gi, g in enumerate(groups) for c in g if c['type'] == 4}
        hp, pos, gold = {}, {}, {}
        for r, sa, sb, cs in d['rounds']:
            for i, c in enumerate(cs):
                hp[(r, i)] = c[6] / c[7] if c[7] else 0
                pos[(r, i)] = (c[4], c[5])
                gold[(r, i)] = c[0]
        shards = collections.Counter()      # champion -> shards bought so far
        shard_at = {}                       # (round, i) -> shard count after that round's purchases
        runs = {}                           # (team, monolith) -> current attempt
        caps = []                           # (round, team, group)
        winner = 0 if d['outcome'] == 1 else 1
        for e in d['events']:
            r, k = e['r'], e['k']
            if k == 'Shop':
                for x in e.get('d', []):
                    shards[x['i']] += sum(n for j, n in x.get('items', []) if n > 0 and j % 2 == 0)
            for i in champ:
                shard_at[(r, i)] = shards[i]
            if k == 'Capture':
                for x in e.get('d', []):
                    g = mono_tiles.get(tuple(x.get('p', (-1, -1))))
                    if g is not None and x.get('gems', 0) > 0:
                        caps.append((r, team[x['i']], g))
            if k in ('Attack', 'Cast ability') and e['a'][0] == 1:
                ai = e['a'][1]
                hit = [c for c, dmg in e.get('cd', []) if c in mono and dmg < 0]
                for m in hit:
                    t = team[ai]
                    run = runs.get((t, m))
                    if run is None or r - run['last'] > 20:
                        run = dict(team=t, mono=m, start=r, last=r, champs=set(), dmg=0, deaths=0, recalls=0,
                                   enemy_hits=0, game=key, winner=winner, names=names)
                        runs[(t, m)] = run
                        attempts.append(run)
                    run['last'] = r
                    run['champs'].add(ai)
                    run['dmg'] += -sum(dmg for c, dmg in e['cd'] if c == m)
            # deaths/recalls/enemy damage involving attempt champions
            for run in [x for x in runs.values() if r - x['last'] <= 20]:
                for x in e.get('d', []):
                    if x['i'] in run['champs'] and x.get('alive') == 0:
                        run['deaths'] += 1
                if k == 'Recall' and e['a'][1] in run['champs']:
                    run['recalls'] += 1
                if k in ('Attack', 'Cast ability') and e['a'][0] == 1 and team[e['a'][1]] != run['team']:
                    tg = e.get('tg')
                    if tg and tg[0] == 'C' and tg[1] in run['champs']:
                        run['enemy_hits'] += 1
            # Heart of Ruin
            if e['a'][0] == 1 and champ.get(e['a'][1], {}).get('type') == HOR:
                i = e['a'][1]
                h = hp.get((r - 1, i))
                if h is None:
                    continue
                rec = hor[names[team[i]] in TOP4]
                tg = e.get('tg')
                if k == 'Attack':
                    rec.append(('atk_' + ('champ' if tg and tg[0] == 'C' else 'camp'), h))
                elif k == 'Cast ability':
                    if e['sl'] == 0:
                        rec.append(('shield', h))
                    else:
                        hit_enemy = any(team[x['i']] != team[i] and x.get('hp', 0) < 0 for x in e.get('d', []))
                        hit_camp = bool(e.get('cd'))
                        rec.append(('dash_' + ('enemy' if hit_enemy else 'camp' if hit_camp else 'move'), h))
                elif k == 'Recall':
                    rec.append(('recall', h))
            for x in e.get('d', []):
                if x.get('alive') == 0 and champ[x['i']]['type'] == HOR:
                    hor[names[team[x['i']]] in TOP4].append(('death', 0))
        # resolve attempts of this game
        for run in [a for a in attempts if a['game'] == key]:
            m = run['mono']
            g = next(gi for gi, gg in enumerate(groups) for c in gg if c['i'] == m)
            run['success'] = any(t == run['team'] and gg == g and run['start'] <= r <= run['last'] + 30 for r, t, gg in caps)
            cs = sorted(run['champs'])
            run['n'] = len(cs)
            run['hp0'] = [hp.get((run['start'] - 1, i), 1) for i in cs]
            run['shards'] = [shard_at.get((run['start'], i), 0) for i in cs]
            run['types'] = [CH[champ[i]['type']] for i in cs]
            run['team_name'] = run['names'][run['team']]
            run['won_game'] = run['team'] == run['winner']
            run['dur'] = run['last'] - run['start']
    P = print
    # ---- monoliths
    for label, sel in [('all teams', lambda a: True), ('top 4', lambda a: a['team_name'] in TOP4)]:
        A = [a for a in attempts if sel(a) and a['dmg'] >= 2000]   # ignore stray hits
        S = [a for a in A if a['success']]; F = [a for a in A if not a['success']]
        P(f"\n### Monolith attempts, {label}: {len(A)} (>=2000 damage), {len(S)} captured ({pct(len(S), len(A))})")
        for name, X in (('captured', S), ('failed', F)):
            if not X:
                continue
            P(f"- {name}: median start round {med([a['start'] for a in X])}, champions {dict(sorted(collections.Counter(a['n'] for a in X).items()))}, "
              f"median duration {med([a['dur'] for a in X])} rounds, median shards per attacker {med([statistics.mean(a['shards']) for a in X]):.1f}, "
              f"median min attacker hp at start {med([min(a['hp0']) for a in X]):.2f}, "
              f"deaths/attempt {statistics.mean([a['deaths'] for a in X]):.2f}, recalls/attempt {statistics.mean([a['recalls'] for a in X]):.2f}, "
              f"attempts with enemy hits on attackers {pct(sum(1 for a in X if a['enemy_hits']), len(X))}, damage dealt median {med([a['dmg'] for a in X])}")
        tc = collections.Counter(t for a in S for t in a['types'])
        P(f"- champions in captured attempts: " + ', '.join(f"{k} {v}" for k, v in tc.most_common(8)))
        bins = [(0, 5), (5, 10), (10, 15), (15, 100)]
        P('- success by mean shards per attacker: ' + ', '.join(
            f"{lo}-{hi}: {pct(sum(1 for a in A if lo <= statistics.mean(a['shards']) < hi and a['success']), sum(1 for a in A if lo <= statistics.mean(a['shards']) < hi))} of {sum(1 for a in A if lo <= statistics.mean(a['shards']) < hi)}" for lo, hi in bins))
        P('- success by attackers: ' + ', '.join(
            f"{n}: {pct(sum(1 for a in A if a['n'] == n and a['success']), sum(1 for a in A if a['n'] == n))} of {sum(1 for a in A if a['n'] == n)}" for n in sorted({a['n'] for a in A})))
        P('- success by start round: ' + ', '.join(
            f"{lo}-{hi}: {pct(sum(1 for a in A if lo <= a['start'] < hi and a['success']), sum(1 for a in A if lo <= a['start'] < hi))} of {sum(1 for a in A if lo <= a['start'] < hi)}" for lo, hi in [(0, 400), (400, 700), (700, 1000), (1000, 1400), (1400, 2001)]))
        P(f"- team that captured a monolith won the game: {pct(sum(1 for a in S if a['won_game']), len(S))} of {len(S)}")
    # ---- heart of ruin
    for top, rec in sorted(hor.items(), reverse=True):
        P(f"\n### Heart of Ruin ({'top 4' if top else 'other teams'})")
        c = collections.Counter(k for k, _ in rec)
        P('- actions: ' + ', '.join(f"{k} {v}" for k, v in c.most_common()))
        for k in ('atk_champ', 'atk_camp', 'shield', 'dash_enemy', 'dash_camp', 'dash_move', 'recall'):
            h = [x for kk, x in rec if kk == k]
            if h:
                P(f"- {k}: median hp {med(h):.2f}, at <30% hp {pct(sum(1 for x in h if x < 0.3), len(h))}, at <50% {pct(sum(1 for x in h if x < 0.5), len(h))}")


if __name__ == '__main__':
    main(*sys.argv[1:3])
