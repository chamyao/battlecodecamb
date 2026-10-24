"""Before/after on the TOP_TEAMS metrics: same unranked groups, two versions of our bot.

Usage: python3 top_compare.py LABEL=EXDIR,FETCHDIR [LABEL=EXDIR,FETCHDIR ...]
Per version: W-L, per-game deaths/kills, champion damage (official summaries), gems per capture,
tributes and median bag, gems submitted, gold, the share of our deaths with 2+ of their champions
within 5 tiles, and per-opponent W-L and gems. Uses top_teams.hunting for the deaths.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo, race_analysis, top_teams


def per_version(exdir, fetchdir, me='Master'):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    rows = {(r['opp'], r['map']): r for r in race_analysis.main(exdir, fetchdir, me)}
    out = []
    for key, v in sides.items():
        path = os.path.join(exdir, 'ladder', v['file'])
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        us = 0 if v['A'] == me else 1
        o = v['B'] if us == 0 else v['A']
        summ = json.load(open(os.path.join(fetchdir, 'summaries', v['file'])))
        dmg = collections.Counter()
        for c in summ['champions']:
            dmg[0 if c['team'] == 'teamA' else 1] += int(c['metrics']['championDamageDone'])
        hunts = top_teams.hunting(d, us, mapinfo.replay_map(d['file']))
        r = rows[(o, v['map'])]
        out.append(dict(r, dmg=(dmg[us], dmg[1 - us]), hunters=[h['hunters'] for h in hunts]))
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else 0


def main(*specs):
    V = {}
    for s in specs:
        label, dirs = s.split('=', 1)
        V[label] = per_version(*dirs.split(','))
    P = print
    P('| per game | ' + ' | '.join(V) + ' |')
    P('|---|' + '---|' * len(V))
    def row(name, f):
        P(f'| {name} | ' + ' | '.join(f(rs) for rs in V.values()) + ' |')
    row('games, W-L', lambda rs: f"{len(rs)}, {sum(r['win'] for r in rs)}-{sum(not r['win'] for r in rs)}")
    row('gems submitted us / them', lambda rs: f"{mean([r['sub'][0] for r in rs]):.0f} / {mean([r['sub'][1] for r in rs]):.0f}")
    row('deaths us / them', lambda rs: f"{mean([r['us']['deaths'] for r in rs]):.1f} / {mean([r['them']['deaths'] for r in rs]):.1f}")
    row('kills us / them', lambda rs: f"{mean([r['us']['kills'] for r in rs]):.1f} / {mean([r['them']['kills'] for r in rs]):.1f}")
    row('champion damage us / them', lambda rs: f"{mean([r['dmg'][0] for r in rs]) / 1000:.1f}k / {mean([r['dmg'][1] for r in rs]) / 1000:.1f}k")
    row('gems per capture us / them', lambda rs: f"{mean([r['us']['gpc'] for r in rs]):.1f} / {mean([r['them']['gpc'] for r in rs]):.1f}")
    row('captures us / them', lambda rs: f"{mean([r['us']['caps'] for r in rs]):.1f} / {mean([r['them']['caps'] for r in rs]):.1f}")
    row('tributes us / them', lambda rs: f"{mean([r['us']['tributes'] for r in rs]):.1f} / {mean([r['them']['tributes'] for r in rs]):.1f}")
    row('median bag us / them', lambda rs: f"{statistics.median([r['us']['bag'] for r in rs]):.0f} / {statistics.median([r['them']['bag'] for r in rs]):.0f}")
    row('gems lost dying us / them', lambda rs: f"{mean([r['us']['lost'] for r in rs]):.0f} / {mean([r['them']['lost'] for r in rs]):.0f}")
    row('gold earned us / them', lambda rs: f"{mean([r['us']['gold'] for r in rs]) / 1000:.1f}k / {mean([r['them']['gold'] for r in rs]) / 1000:.1f}k")
    def outnumbered(rs):
        h = [x for r in rs for x in r['hunters']]
        return f"{100 * sum(1 for x in h if x >= 2) / max(1, len(h)):.0f}% of {len(h)}"
    row('our deaths with 2+ of theirs within 5', outnumbered)
    P('\n| opponent | ' + ' | '.join(f'{k} W-L (gems us-them)' for k in V) + ' |')
    P('|---|' + '---|' * len(V))
    for o in sorted({r['opp'] for rs in V.values() for r in rs}):
        cells = []
        for rs in V.values():
            s = [r for r in rs if r['opp'] == o]
            cells.append(f"{sum(r['win'] for r in s)}-{sum(not r['win'] for r in s)} ({mean([r['sub'][0] for r in s]):.0f}-{mean([r['sub'][1] for r in s]):.0f})")
        P(f'| {o} | ' + ' | '.join(cells) + ' |')


if __name__ == '__main__':
    main(*sys.argv[1:])
