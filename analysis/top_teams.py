"""What the ladder's top teams do against us: openings, banking, carrier hunting, altar control.

Usage: python3 top_teams.py EXDIR FETCHDIR [TEAM]
Uses race_analysis for per-game race numbers, and adds per opponent:
- opening: first capture and first tribute rounds, which groups they capture first;
- banking: bag sizes, and whether one of our champions was within 8 tiles when they banked;
- carrier hunting: for each of their kills, our victim's bag, how many of their champions were
  within 5 tiles, distance from the nearest altar, and how far the killer had travelled in the
  10 rounds before (pursuit);
- altar control: share of time within 4 tiles of an altar.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo, race_analysis
from analyse import CH, DRAFT


def med(x):
    return statistics.median(x) if x else 0


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def hunting(d, us, m):
    team = {c['i']: c['team'] for c in d['champions']}
    pos = {r: cs for r, _, _, cs in d['rounds']}
    out = []
    for e in d['events']:
        if e['a'][0] != 1 or team.get(e['a'][1]) == us:
            continue
        k = e['a'][1]
        for y in e.get('d', []):
            if y.get('alive') != 0 or team[y['i']] != us:
                continue
            r = e['r']
            cs = pos.get(r - 1)
            if not cs:
                continue
            vp = (cs[y['i']][4], cs[y['i']][5])
            hunters = sum(1 for i, c in enumerate(cs) if team[i] != us and c[2] and cheb((c[4], c[5]), vp) <= 5)
            back = pos.get(r - 11)
            travel = cheb((back[k][4], back[k][5]), (cs[k][4], cs[k][5])) if back and back[k][2] else None
            out.append(dict(bag=-y.get('gems', 0), hunters=hunters, altar=min(cheb(vp, a) for a in m['altars']),
                            travel=travel, killer=CH[d['champions'][k]['type']], round=r))
    return out


def banking(d, us, m):
    """For each of their tributes: was one of our champions within 8 tiles of the banker?"""
    team = {c['i']: c['team'] for c in d['champions']}
    pos = {r: cs for r, _, _, cs in d['rounds']}
    res = []
    for e in d['events']:
        if e['k'] != 'Gems submitted':
            continue
        for y in e.get('d', []):
            if y.get('gems', 0) < 0 and team[y['i']] != us:
                cs = pos.get(e['r'] - 1)
                if not cs:
                    continue
                bp = (cs[y['i']][4], cs[y['i']][5])
                res.append((-y['gems'], any(team[i] == us and c[2] and cheb((c[4], c[5]), bp) <= 8 for i, c in enumerate(cs))))
    return res


def main(exdir, fetchdir, me='Master'):
    rows = race_analysis.main(exdir, fetchdir, me)
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    extra = collections.defaultdict(lambda: dict(kills=[], banks=[], first_cap=[], first_trib=[], first_groups=collections.Counter(), drafts=collections.Counter(), games=0, wl=[0, 0]))
    for key, v in sides.items():
        path = os.path.join(exdir, 'ladder', v['file'])
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        us = 0 if v['A'] == me else 1
        o = v['B'] if us == 0 else v['A']
        m = mapinfo.replay_map(d['file'])
        st = analyse.game_stats(d, (v['A'], v['B']))
        X = extra[o]
        X['games'] += 1
        X['wl'][0 if (d['outcome'] == 1) == (us == 0) else 1] += 1
        X['kills'] += hunting(d, us, m)
        X['banks'] += banking(d, us, m)
        caps = sorted(st[1 - us]['lists'].get('capture', []))
        tr = st[1 - us]['lists'].get('tribute', [])
        if caps:
            X['first_cap'].append(caps[0][0])
        if tr:
            X['first_trib'].append(min(t[0] for t in tr))
        for c in caps[:3]:
            X['first_groups'][c[1]] += 1
        X['drafts'][' '.join(DRAFT[x].split()[0] for x in d['drafts'][1 - us] if x >= 0)] += 1
    race_analysis.report(rows)
    P = print
    P('\n## Per opponent\n')
    P('| opponent | our W-L | their drafts | first capture / first tribute (median round) | first 3 captures | their median bag | banks with one of ours within 8 | kills on us | kills on carriers (bag > 0) | median victim bag | median hunters within 5 | kills within 6 of an altar | median killer travel (10 rds) |')
    P('|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for o, X in sorted(extra.items(), key=lambda kv: kv[0]):
        K = X['kills']
        carriers = [k for k in K if k['bag'] > 0]
        B = X['banks']
        P(f"| {o} | {X['wl'][0]}-{X['wl'][1]} | {'; '.join(k for k, _ in X['drafts'].most_common(2))} | {med(X['first_cap'])} / {med(X['first_trib'])} | "
          f"{', '.join(f'{k} {v}' for k, v in X['first_groups'].most_common(3))} | {med([b[0] for b in B])} | {100 * sum(1 for b in B if b[1]) / max(1, len(B)):.0f}% | "
          f"{len(K)} | {len(carriers)} ({100 * len(carriers) / max(1, len(K)):.0f}%) | {med([k['bag'] for k in carriers])} | {med([k['hunters'] for k in K])} | "
          f"{100 * sum(1 for k in K if k['altar'] <= 6) / max(1, len(K)):.0f}% | {med([k['travel'] for k in K if k['travel'] is not None])} |")
    allk = [k for X in extra.values() for k in X['kills']]
    c = collections.Counter(k['killer'] for k in allk)
    P(f"\nTheir kills on us by champion: {dict(c.most_common())}")
    P(f"Hunters within 5 at their kills: {dict(sorted(collections.Counter(min(k['hunters'], 4) for k in allk).items()))} (4 = 4+)")
    P(f"Victim bag at their kills: 0: {sum(1 for k in allk if k['bag'] == 0)}, 1-24: {sum(1 for k in allk if 0 < k['bag'] < 25)}, 25+: {sum(1 for k in allk if k['bag'] >= 25)}")


if __name__ == '__main__':
    main(*sys.argv[1:])
