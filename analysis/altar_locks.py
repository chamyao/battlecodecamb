"""Altar locks and altar fights per version (same unranked groups or ranked sets).

Usage: python3 altar_locks.py LABEL=EXDIR,FETCHDIR [...]
Per game, us / them: locks placed, basic attacks on locks (untargeted attacks at an altar tile),
tribute starts vs completions (a lock, a stun or death cancels a tribute), champion deaths within
6 tiles of an altar, and the round of the first lock.
"""
import json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapinfo


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def game(d, us, m):
    team = {c['i']: c['team'] for c in d['champions']}
    altars = [tuple(a) for a in m['altars']]
    side = lambda i: 0 if team[i] == us else 1
    x = [dict(locks=0, lock_hits=0, starts=0, done=0, deaths_altar=0, first_lock=None) for _ in range(2)]
    for e in d['events']:
        if e['a'][0] != 1 or e['a'][1] not in team:
            continue
        s = side(e['a'][1])
        if e['k'] == 'Place altar lock':
            x[s]['locks'] += 1
            if x[s]['first_lock'] is None:
                x[s]['first_lock'] = e['r']
        elif e['k'] == 'Attack' and not e.get('tg') and e.get('t') and tuple(e['t']) in altars:
            x[s]['lock_hits'] += 1
        elif e['k'] == 'Submit gems':
            x[s]['starts'] += 1
        elif e['k'] == 'Gems submitted':
            x[s]['done'] += 1
        for y in e.get('d', []):
            if y.get('alive') == 0 and 'p' in y and min(cheb(y['p'], a) for a in altars) <= 6:
                x[side(y['i'])]['deaths_altar'] += 1
    return x


def main(*specs):
    P = print
    P('| per game, us / them | ' + ' | '.join(s.split('=')[0] for s in specs) + ' |')
    P('|---|' + '---|' * len(specs))
    res = []
    for s in specs:
        ex, fd = s.split('=', 1)[1].split(',')
        rows = []
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            p = os.path.join(ex, 'ladder', v['file'])
            if not os.path.exists(p):
                continue
            d = json.load(open(p))
            rows.append(game(d, 0 if v['A'] == 'Master' else 1, mapinfo.replay_map(d['file'])))
        res.append(rows)
    mean = lambda xs: sum(xs) / len(xs) if xs else 0
    for k, name in (('locks', 'locks placed'), ('lock_hits', 'basic attacks on altar locks'), ('starts', 'tribute starts'),
                    ('done', 'tributes completed'), ('deaths_altar', 'champion deaths within 6 of an altar')):
        P(f'| {name} | ' + ' | '.join(f"{mean([g[0][k] for g in rows]):.1f} / {mean([g[1][k] for g in rows]):.1f}" for rows in res) + ' |')
    P('| tribute starts not completed | ' + ' | '.join(
        f"{100 * (1 - sum(g[0]['done'] for g in rows) / max(1, sum(g[0]['starts'] for g in rows))):.0f}% / "
        f"{100 * (1 - sum(g[1]['done'] for g in rows) / max(1, sum(g[1]['starts'] for g in rows))):.0f}%" for rows in res) + ' |')
    P('| games with a lock, us / them; median first-lock round | ' + ' | '.join(
        f"{sum(1 for g in rows if g[0]['locks'])} / {sum(1 for g in rows if g[1]['locks'])}; "
        f"{statistics.median([g[0]['first_lock'] for g in rows if g[0]['first_lock']] or [0]):.0f} / "
        f"{statistics.median([g[1]['first_lock'] for g in rows if g[1]['first_lock']] or [0]):.0f}" for rows in res) + ' |')


if __name__ == '__main__':
    main(*sys.argv[1:])
