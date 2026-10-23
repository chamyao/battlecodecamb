"""Second loss analysis (v3): what decides games, especially those that go to round 2000.

Usage: python3 v3_analysis.py EXDIR FETCHDIR [TEAM]
FETCHDIR is fetch_mine.py's output (sides.json from ladder_prep.py, summaries/).
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo
from analyse import CAMP, camp_groups, gname


def med(x):
    return statistics.median(x) if x else 0


def side_stats(d, us_t, sp):
    """Per-team numbers for one game (team 0/1 = side A/B)."""
    team = {c['i']: c['team'] for c in d['champions']}
    ct = {c['i']: CAMP[c['type']] for c in d['camps']}
    out = [collections.Counter(), collections.Counter()]
    killers = [collections.Counter(), collections.Counter()]
    acted = collections.defaultdict(set)
    for e in d['events']:
        r, k = e['r'], e['k']
        if e['a'][0] == 1:
            ai = e['a'][1]
            if k in ('Attack', 'Cast ability', 'Submit gems', 'Gems submitted', 'Recall', 'Shop', 'Place ward'):
                acted[ai].add(r)
            tg = e.get('tg')
            if k == 'Attack' and tg and tg[0] == 'M' and ct.get(tg[1]) in ('monolith', 'golem'):
                out[team[ai]]['hits_on_monolith_golem'] += 1
        for x in e.get('d', []):
            if x.get('alive') == 0:
                t = team[x['i']]
                out[t]['deaths'] += 1
                killers[t][ct.get(e['a'][1], '?') if e['a'][0] == 2 else 'champion'] += 1
                out[t]['gems_lost_dying'] += -x.get('gems', 0)
    R = d['rounds']
    for i, t in team.items():
        run, prev = 0, None
        for r, _, _, cs in R:
            c = cs[i]
            if not c[2]:
                out[t]['dead_rounds'] += 1
                run, prev = 0, None
                continue
            out[t]['alive_rounds'] += 1
            p = (c[4], c[5])
            on_spawn = p in sp[t]
            if on_spawn:
                out[t]['spawn_rounds'] += 1
                if c[6] < c[7]:
                    out[t]['spawn_healing_rounds'] += 1
            if p == prev and not on_spawn and r not in acted[i]:
                run += 1
                if run >= 15:
                    out[t]['idle_rounds'] += 1
            else:
                run = 0
            prev = p
    last = R[-1][3]
    for i, t in team.items():
        out[t]['gems_carried_at_end'] += last[i][1]
    return out, killers


def main(exdir, fetchdir, me='Master'):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    rows = []
    for key, v in sides.items():
        d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
        summ = json.load(open(os.path.join(fetchdir, 'summaries', v['file'])))
        us_t = 0 if v['A'] == me else 1
        m = mapinfo.replay_map(d['file'])
        sp = [set((x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])) for a in m['spawn']]
        st = analyse.game_stats(d, (v['A'], v['B']))
        extra, killers = side_stats(d, us_t, sp)
        gold = collections.Counter()
        for c in summ['champions']:
            gold[0 if c['team'] == 'teamA' else 1] += int(c['metrics']['earnedGold'])
        win = (d['outcome'] == 1) == (us_t == 0)
        sub = d['submitted']
        end = 'reached 1000' if max(sub) >= 1000 else ('gems tiebreak' if sub[0] != sub[1] else 'gold tiebreak')
        rows.append(dict(map=v['map'], opp=v['B'] if us_t == 0 else v['A'], win=win, rounds=d['rounds_played'], end=end,
                         us=dict(st[us_t], **extra[us_t], gold=gold[us_t], killers=killers[us_t]),
                         them=dict(st[1 - us_t], **extra[1 - us_t], gold=gold[1 - us_t], killers=killers[1 - us_t]),
                         sub=(sub[us_t], sub[1 - us_t])))
    rows.sort(key=lambda r: (r['opp'], r['map']))
    P = print
    W = sum(r['win'] for r in rows)
    P(f'{len(rows)} games, {W}-{len(rows) - W}\n')
    P('| map | opponent | result | how it ended | gems us-them | gold us-them | rounds | deaths us-them | idle rds us | gems carried at end us-them |')
    P('|---|---|---|---|---|---|---|---|---|---|')
    for r in rows:
        u, t = r['us'], r['them']
        P(f"| {r['map']} | {r['opp']} | {'W' if r['win'] else 'L'} | {r['end']} | {r['sub'][0]}-{r['sub'][1]} | {u['gold']}-{t['gold']} | {r['rounds']} | "
          f"{u.get('deaths', 0)}-{t.get('deaths', 0)} | {u.get('idle_rounds', 0)} | {u.get('gems_carried_at_end', 0)}-{t.get('gems_carried_at_end', 0)} |")
    P('\nHow games ended: ' + ', '.join(f"{k}: {sum(1 for r in rows if r['end'] == k and r['win'])}-{sum(1 for r in rows if r['end'] == k and not r['win'])}"
                                        for k in ('reached 1000', 'gems tiebreak', 'gold tiebreak')))

    def agg(sel, who, key, per=None):
        xs = [r[who].get(key, 0) / (r['rounds'] / per if per else 1) for r in rows if sel(r)]
        return sum(xs) / len(xs) if xs else 0
    keys = [('tributed', 1000), ('gold', 1000), ('captures', 1000), ('capture_gems', 1000), ('deaths', 1000), ('kills', 1000),
            ('gems_stolen', None), ('gems_lost_dying', None), ('tribute_starts', 1000), ('idle_rounds', None),
            ('spawn_healing_rounds', None), ('dead_rounds', None), ('hits_on_monolith_golem', None), ('gold_spent', None)]
    P('\nPer game (rates per 1,000 rounds where marked):\n')
    P('| metric | us in losses | them in losses | us in wins | them in wins |\n|---|---|---|---|---|')
    for k, per in keys:
        lab = k + (' /1000 rds' if per else '')
        P(f"| {lab} | {agg(lambda r: not r['win'], 'us', k, per):.1f} | {agg(lambda r: not r['win'], 'them', k, per):.1f} | "
          f"{agg(lambda r: r['win'], 'us', k, per):.1f} | {agg(lambda r: r['win'], 'them', k, per):.1f} |")
    for lab, sel in (('losses', lambda r: not r['win']), ('wins', lambda r: r['win'])):
        ku, kt = collections.Counter(), collections.Counter()
        bu, bt = [], []
        for r in rows:
            if sel(r):
                ku.update(r['us']['killers']); kt.update(r['them']['killers'])
                bu += [x[1] for x in r['us']['lists'].get('tribute', [])]; bt += [x[1] for x in r['them']['lists'].get('tribute', [])]
        P(f"\nIn {lab}: our deaths by killer {dict(ku.most_common())}; theirs {dict(kt.most_common())}; "
          f"median bag us {med(bu)} them {med(bt)}")
    # gem curves
    P('\nMedian tributed gems by round (us vs them), losses / wins:\n')
    P('| round | us (L) | them (L) | us (W) | them (W) |\n|---|---|---|---|---|')
    for rd in (250, 500, 750, 1000, 1250, 1500, 1750, 2000):
        def at(r, who):
            ks = [int(k) for k in r[who]['curve'] if int(k) <= rd]
            return r[who]['curve'][max(ks)]['sub'] if ks else 0
        P(f"| {rd} | {med([at(r, 'us') for r in rows if not r['win']])} | {med([at(r, 'them') for r in rows if not r['win']])} | "
          f"{med([at(r, 'us') for r in rows if r['win']])} | {med([at(r, 'them') for r in rows if r['win']])} |")
    json.dump([{k: v for k, v in r.items() if k not in ('us', 'them')} | {'us': {k: v for k, v in r['us'].items() if k not in ('lists', 'builds', 'curve')},
               'them': {k: v for k, v in r['them'].items() if k not in ('lists', 'builds', 'curve')}} for r in rows],
              open(os.path.join(fetchdir, 'v3_rows.json'), 'w'), default=str)


if __name__ == '__main__':
    main(*sys.argv[1:])
