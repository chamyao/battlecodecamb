"""Why are we out-raced to 1000? Per-game race diagnostics for our losses.

Usage: python3 race_analysis.py EXDIR FETCHDIR [TEAM] [--opp NAME] [--map MAP]
Per game and side: tributed gems at rounds 250/500/750/1000, gems per capture and by source
(monolith / golem / groups with gem clusters / elk-only / wolf / gold-only), median bag,
tributes, deaths and kills, share of alive time within 4 tiles of an altar, kills within 6 tiles
of an altar, gems lost dying, draft.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo
from analyse import CAMP, DRAFT


def med(x):
    return statistics.median(x) if x else 0


def source(gn, gems):
    if 'monolith' in gn:
        return 'monolith'
    if 'golem' in gn:
        return 'golem'
    if gems == 0:
        return 'gold-only'
    if 'gem' in gn:
        return 'gem groups'
    if 'elk' in gn:
        return 'elk groups'
    return 'wolf'


def side_numbers(d, st, t, m, team):
    x = st[t]
    caps = x['lists'].get('capture', [])
    tr = x['lists'].get('tribute', [])
    src = collections.Counter()
    for c in caps:
        src[source(c[1], c[2])] += c[2]
    near = alive = 0
    for r, _, _, cs in d['rounds']:
        for i, c in enumerate(cs):
            if team[i] == t and c[2]:
                alive += 1
                if min(max(abs(a[0] - c[4]), abs(a[1] - c[5])) for a in m['altars']) <= 4:
                    near += 1
    kills_near = 0
    for e in d['events']:
        if e['a'][0] == 1 and team.get(e['a'][1]) == t:
            for y in e.get('d', []):
                if y.get('alive') == 0 and team[y['i']] != t:
                    p = y.get('p', (-1, -1))
                    kills_near += min(max(abs(a[0] - p[0]), abs(a[1] - p[1])) for a in m['altars']) <= 6
    curve = {}
    for rd in (250, 500, 750, 1000):
        ks = [int(k) for k in x['curve'] if int(k) <= rd]
        curve[rd] = x['curve'][max(ks)]['sub'] if ks else 0
    return dict(caps=len(caps), gems_cap=sum(c[2] for c in caps), src=dict(src.most_common()),
                gpc=sum(c[2] for c in caps) / max(1, len(caps)), bag=med([q[1] for q in tr]), tributes=len(tr),
                deaths=x.get('deaths', 0), kills=x.get('kills', 0), lost=x.get('gems_lost_on_death', 0),
                near=near / max(1, alive), kills_near=kills_near, gold=x.get('gold_earned', 0), curve=curve,
                first_trib=min([q[0] for q in tr]) if tr else None)


def main(exdir, fetchdir, me='Master', opp=None, mp=None):
    sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
    out = []
    for key, v in sides.items():
        path = os.path.join(exdir, 'ladder', v['file'])
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        us = 0 if v['A'] == me else 1
        o = v['B'] if us == 0 else v['A']
        if (opp and o != opp) or (mp and v['map'] != mp):
            continue
        win = (d['outcome'] == 1) == (us == 0)
        m = mapinfo.replay_map(d['file'])
        team = {c['i']: c['team'] for c in d['champions']}
        st = analyse.game_stats(d, (v['A'], v['B']))
        u, t = side_numbers(d, st, us, m, team), side_numbers(d, st, 1 - us, m, team)
        out.append(dict(map=v['map'], opp=o, win=win, sub=(d['submitted'][us], d['submitted'][1 - us]), rounds=d['rounds_played'],
                        us=u, them=t, draft=' '.join(DRAFT[x].split()[0] for x in d['drafts'][us] if x >= 0),
                        odraft=' '.join(DRAFT[x].split()[0] for x in d['drafts'][1 - us] if x >= 0), n_altars=len(m['altars'])))
    return out


def report(rows):
    P = print
    L = [r for r in rows if not r['win']]
    W = [r for r in rows if r['win']]
    P(f'{len(rows)} games, {len(W)}-{len(L)}\n')
    P('| map | opponent | gems us-them | rounds | tributed at 250/500/750/1000 us : them | gems/capture us/them | captures us/them | bag us/them | deaths us/them | altar-zone time us/them | kills near altar us/them | gem sources (them) |')
    P('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for r in sorted(L, key=lambda r: (r['opp'], r['map'])):
        u, t = r['us'], r['them']
        cu = '/'.join(str(u['curve'][k]) for k in (250, 500, 750, 1000)); ct = '/'.join(str(t['curve'][k]) for k in (250, 500, 750, 1000))
        P(f"| {r['map']} | {r['opp']} | {r['sub'][0]}-{r['sub'][1]} | {r['rounds']} | {cu} : {ct} | {u['gpc']:.1f}/{t['gpc']:.1f} | {u['caps']}/{t['caps']} | "
          f"{u['bag']}/{t['bag']} | {u['deaths']}/{t['deaths']} | {100 * u['near']:.0f}%/{100 * t['near']:.0f}% | {u['kills_near']}/{t['kills_near']} | {t['src']} |")

    def mean(sel, who, k):
        xs = [r[who][k] for r in sel]
        return sum(xs) / len(xs) if xs else 0
    P('\n| per game | us in losses | them in losses | us in wins | them in wins |\n|---|---|---|---|---|')
    for k in ('gems_cap', 'caps', 'gpc', 'bag', 'tributes', 'deaths', 'kills', 'lost', 'near', 'kills_near', 'gold'):
        P(f"| {k} | {mean(L, 'us', k):.2f} | {mean(L, 'them', k):.2f} | {mean(W, 'us', k):.2f} | {mean(W, 'them', k):.2f} |")
    src_u, src_t = collections.Counter(), collections.Counter()
    for r in L:
        src_u.update(r['us']['src']); src_t.update(r['them']['src'])
    P(f"\nGem sources in losses, us: {dict(src_u.most_common())}; them: {dict(src_t.most_common())}")
    P('Opponent drafts in losses: ' + ', '.join(f'{k} ({v})' for k, v in collections.Counter(r['odraft'] for r in L).most_common(6)))
    P('Our drafts: ' + ', '.join(f'{k} ({v})' for k, v in collections.Counter(r['draft'] for r in rows).most_common(3)))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    kw = {}
    for flag in ('--opp', '--map'):
        if flag in sys.argv:
            kw[flag[2:].replace('map', 'mp')] = sys.argv[sys.argv.index(flag) + 1]
            args.remove(kw[flag[2:].replace('map', 'mp')])
    report(main(*args, **kw))
