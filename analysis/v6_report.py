"""Loss report for a bot version window: v3 failure-mode checks, per-opponent summary.

Usage: python3 v6_report.py EXDIR FETCHDIR SPLIT_ISO [TEAM]
Games created before SPLIT_ISO are labelled 'v5d', after it 'v5d-fs2'.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo
from analyse import CAMP, CH, DRAFT


def med(x):
    return statistics.median(x) if x else 0


def main(exdir, fetchdir, split, me='Master'):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    created = {m['matchId']: m['createdAt'] for m in json.load(open(os.path.join(fetchdir, 'matches.json')))['matches']}
    rows = []
    for key, v in sides.items():
        mid = key.split('/')[1]
        d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
        us = 0 if v['A'] == me else 1
        m = mapinfo.replay_map(d['file'])
        team = {c['i']: c['team'] for c in d['champions']}
        ct = {c['i']: CAMP[c['type']] for c in d['camps']}
        st = analyse.game_stats(d, (v['A'], v['B']))
        sub = d['submitted']
        win = (d['outcome'] == 1) == (us == 0)
        # v3 failure modes
        locks = [e['r'] for e in d['events'] if e['k'] == 'Place altar lock' and team.get(e['a'][1]) != us]
        subs = {r: (sa, sb) for r, sa, sb, _ in d['rounds']}
        lock_stall = False
        if locks:
            g0 = subs.get(locks[0], (0, 0))[us]
            lock_stall = sub[us] - g0 < 50 and d['rounds_played'] - locks[0] > 300
        mono_tiles = [(c['x'], c['y']) for c in m['camps'] if c['type'] == 'monolith']
        mono_altar_deaths = 0
        killers = collections.Counter()
        for e in d['events']:
            for x in e.get('d', []):
                if x.get('alive') == 0 and team[x['i']] == us:
                    if e['a'][0] == 2:
                        killers[ct.get(e['a'][1], '?')] += 1
                        p = x.get('p', (-1, -1))
                        if ct.get(e['a'][1]) == 'monolith' and any(max(abs(a[0] - p[0]), abs(a[1] - p[1])) <= 3 for a in m['altars']):
                            mono_altar_deaths += 1
                    else:
                        killers['champion'] += 1
        acted = collections.defaultdict(set)
        for e in d['events']:
            if e['a'][0] == 1:
                acted[e['a'][1]].add(e['r'])
        sp = set((x, y) for a in [m['spawn'][us]] for x in range(a[0], a[2]) for y in range(a[1], a[3]))
        idle = 0
        for i, t in team.items():
            if t != us:
                continue
            prev, run = None, 0
            for r, _, _, cs in d['rounds']:
                c = cs[i]; p = (c[4], c[5])
                if c[2] and p == prev and p not in sp and r not in acted[i]:
                    run += 1
                    idle += run >= 15
                else:
                    run = 0
                prev = p if c[2] else None
        u, o = st[us], st[1 - us]
        rows.append(dict(ver='v5d' if created.get(mid, '') < split else 'v5d-fs2', map=v['map'], opp=v['B'] if us == 0 else v['A'],
                         win=win, rounds=d['rounds_played'], sub=(sub[us], sub[1 - us]),
                         end='reached 1000' if max(sub) >= 1000 else ('gems tiebreak' if sub[0] != sub[1] else 'gold tiebreak'),
                         lock_stall=lock_stall, locks=len(locks), mono_altar=mono_altar_deaths, zero_gem=sub[us] == 0, idle=idle,
                         deaths=sum(killers.values()), killers=dict(killers.most_common(4)), kills=u.get('kills', 0), opp_deaths=o.get('deaths', 0),
                         gold=(u.get('gold_earned', 0), o.get('gold_earned', 0)), caps=(u.get('captures', 0), o.get('captures', 0)),
                         bag=(med([x[1] for x in u['lists'].get('tribute', [])]), med([x[1] for x in o['lists'].get('tribute', [])])),
                         draft=' '.join(DRAFT[x].split()[0] for x in d['drafts'][us] if x >= 0),
                         opp_draft=' '.join(DRAFT[x].split()[0] for x in d['drafts'][1 - us] if x >= 0),
                         opp_locks_placed=locks, opp_mono_hits=o.get('atk_camp', 0)))
    P = print
    for ver in ('v5d', 'v5d-fs2'):
        X = [r for r in rows if r['ver'] == ver]
        if not X:
            continue
        W = sum(r['win'] for r in X)
        P(f"\n## {ver}: {len(X)} games, {W}-{len(X) - W}\n")
        P('How games ended (W-L): ' + ', '.join(f"{k} {sum(1 for r in X if r['end'] == k and r['win'])}-{sum(1 for r in X if r['end'] == k and not r['win'])}"
                                              for k in ('reached 1000', 'gems tiebreak', 'gold tiebreak')))
        L = [r for r in X if not r['win']]
        P(f"v3 failure modes in losses: lock stall {sum(r['lock_stall'] for r in L)}, monolith-at-altar deaths {sum(r['mono_altar'] for r in L)}, "
          f"0-gem games {sum(r['zero_gem'] for r in L)}, idle rounds {sum(r['idle'] for r in L)} (all games: lock stall {sum(r['lock_stall'] for r in X)}, "
          f"monolith-altar deaths {sum(r['mono_altar'] for r in X)}, 0-gem {sum(r['zero_gem'] for r in X)}, idle {sum(r['idle'] for r in X)})")
        P('\n| map | opponent | how it ended | gems us-them | rounds | deaths (killers) | K | gold us-them | captures | bag us/them | opp locks | idle |')
        P('|---|---|---|---|---|---|---|---|---|---|---|---|')
        for r in sorted(L, key=lambda r: (r['opp'], r['map'])):
            P(f"| {r['map']} | {r['opp']} | {r['end']} | {r['sub'][0]}-{r['sub'][1]} | {r['rounds']} | {r['deaths']} {r['killers']} | {r['kills']} | "
              f"{r['gold'][0]}-{r['gold'][1]} | {r['caps'][0]}-{r['caps'][1]} | {r['bag'][0]}/{r['bag'][1]} | {r['locks']} | {r['idle']} |")
    P('\n## Opponents (all games in the window)\n')
    P('| opponent | W-L | their drafts | our deaths/game | their deaths/game | gold us/them per game | captures us/them | bag us/them | locks they placed/game |')
    P('|---|---|---|---|---|---|---|---|---|')
    by = collections.defaultdict(list)
    for r in rows:
        by[r['opp']].append(r)
    for opp, X in sorted(by.items(), key=lambda kv: sum(not r['win'] for r in kv[1]) - sum(r['win'] for r in kv[1]), reverse=True):
        n = len(X)
        P(f"| {opp} | {sum(r['win'] for r in X)}-{sum(not r['win'] for r in X)} | {'; '.join(sorted(set(r['opp_draft'] for r in X))[:2])} | "
          f"{sum(r['deaths'] for r in X) / n:.1f} | {sum(r['opp_deaths'] for r in X) / n:.1f} | {sum(r['gold'][0] for r in X) / n:.0f}/{sum(r['gold'][1] for r in X) / n:.0f} | "
          f"{sum(r['caps'][0] for r in X) / n:.0f}/{sum(r['caps'][1] for r in X) / n:.0f} | {med([r['bag'][0] for r in X])}/{med([r['bag'][1] for r in X])} | "
          f"{sum(r['locks'] for r in X) / n:.1f} |")
    P('\nOur drafts: ' + ', '.join(f'{k} ({v})' for k, v in collections.Counter(r['draft'] for r in rows).most_common(4)))
    json.dump(rows, open(os.path.join(fetchdir, 'v6_rows.json'), 'w'), default=str)


if __name__ == '__main__':
    main(*sys.argv[1:])
