"""Champion fights in real games: what the band does in fights that we don't (for fight rules / a stress fighter).

Usage: python3 -I genome/intel/fight_study.py ANALYSIS_DIR LABEL=FETCHDIR,EXDIR [...] [--after 500] [--near-rich 6] [--all]
An engagement is a run of champion-on-champion hits (either side) with gaps of at most 10 rounds, starting after
--after, whose first hit is within --near-rich tiles of a rich group's spawn tiles (14+ gems per capture; --all drops
this filter). Per engagement, for each side: champions involved (dealt or took champion damage), HP and item points
summed at the first hit, casts per involved champion, focus fire (the share of the side's hits on its single most-hit
target), retreats (an involved champion under 50% HP that ends 4+ tiles farther from the fight than it was), the
hits taken in the first 3 rounds, and deaths. Split by game result (our wins / losses) and by engagement outcome.
"""
import collections, json, os, statistics, sys


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main(argv):
    adir = argv[0]
    after = int(argv[argv.index('--after') + 1]) if '--after' in argv else 500
    nr = int(argv[argv.index('--near-rich') + 1]) if '--near-rich' in argv else 6
    use_all = '--all' in argv
    sys.path.insert(0, os.path.abspath(adir))
    import analyse, fight_dump
    from analyse import CH
    E = []
    for spec in [a for a in argv[1:] if '=' in a]:
        label, dirs = spec.split('=', 1); fd, ex = dirs.split(',')
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1
            win = (d['outcome'] == 1) == (us == 0)
            team = {c['i']: c['team'] for c in d['champions']}; name = {c['i']: CH[c['type']] for c in d['champions']}
            st = analyse.game_stats(d, (v['A'], v['B']))
            rich_names = {c[1] for t in (0, 1) for c in st[t]['lists'].get('capture', []) if c[2] >= 14}
            rich = {(c['x'], c['y']) for g in analyse.camp_groups(d['camps']) if analyse.gname(g) in rich_names for c in g}
            R = {r: cs for r, _, _, cs in d['rounds']}
            hist = fight_dump.inventories(d)
            H = []; casts = []; deaths = []
            for e in d['events']:
                if e['a'][0] != 1 or e['a'][1] not in team:
                    continue
                a = e['a'][1]
                if e['k'] == 'Cast ability':
                    casts.append((e['r'], a))
                if e['k'] in ('Attack', 'Cast ability'):
                    for y in e.get('d', []):
                        if y['i'] in team and team[y['i']] != team[a] and y.get('hp', 0) < 0:
                            H.append((e['r'], a, y['i']))
                for y in e.get('d', []):
                    if y.get('alive') == 0 and y['i'] in team and team[y['i']] != team[a]:
                        deaths.append((e['r'], y['i']))
            H.sort()
            runs = []
            for h in H:
                if runs and h[0] - runs[-1][-1][0] <= 10:
                    runs[-1].append(h)
                else:
                    runs.append([h])
            for run in runs:
                r0, r1 = run[0][0], run[-1][0]
                if r0 <= after:
                    continue
                cs = R.get(r0 - 1)
                if not cs:
                    continue
                p0 = (cs[run[0][2]][4], cs[run[0][2]][5])
                if not use_all and (not rich or min(cheb(p0, t) for t in rich) > nr):
                    continue
                inv = {i for h in run for i in (h[1], h[2])}
                cen = (statistics.mean(cs[i][4] for i in inv), statistics.mean(cs[i][5] for i in inv))
                end = R.get(min(r1 + 3, max(R)))
                row = dict(win=win, label=label)
                for side, t in (('us', us), ('them', 1 - us)):
                    ids = [i for i in inv if team[i] == t]
                    row[f'{side}_n'] = len(ids)
                    row[f'{side}_hp'] = sum(cs[i][6] for i in ids)
                    row[f'{side}_pts'] = sum(sum(fight_dump.stats_from_items(name[i], fight_dump.inv_at(hist, i, r0))['pts'].values()) for i in ids)
                    row[f'{side}_casts'] = sum(1 for r, a in casts if r0 <= r <= r1 and a in ids) / max(1, len(ids))
                    mine = [h for h in run if team[h[1]] == t]
                    row[f'{side}_focus'] = (collections.Counter(h[2] for h in mine).most_common(1)[0][1] / len(mine)) if mine else 0
                    row[f'{side}_hits'] = len(mine)
                    row[f'{side}_early_hits'] = sum(1 for h in mine if h[0] <= r0 + 2)
                    row[f'{side}_deaths'] = sum(1 for r, i in deaths if r0 <= r <= r1 + 3 and team[i] == t)
                    ret = 0
                    if end:
                        for i in ids:
                            if end[i][2] and cs[i][7] and end[i][6] / end[i][7] < 0.5 and cheb((end[i][4], end[i][5]), cen) >= cheb((cs[i][4], cs[i][5]), cen) + 4:
                                ret += 1
                    row[f'{side}_retreats'] = ret
                row['first_hit_by_us'] = team[run[0][1]] == us
                row['rounds'] = r1 - r0 + 1
                E.append(row)
    if not E:
        print('no engagements'); return
    m = lambda X, k: statistics.mean(x[k] for x in X) if X else 0
    def table(title, groups):
        print(f'\n{title}\n')
        print('| group | n | champions us/them | HP at first hit us/them | item points us/them | casts per champion us/them | focus us/them | hits in first 3 rounds us/them | retreats under 50% us/them | deaths us/them | we hit first |')
        print('|---|---|---|---|---|---|---|---|---|---|---|')
        for g, X in groups:
            if X:
                print(f"| {g} | {len(X)} | {m(X,'us_n'):.1f}/{m(X,'them_n'):.1f} | {m(X,'us_hp'):.0f}/{m(X,'them_hp'):.0f} | {m(X,'us_pts'):.0f}/{m(X,'them_pts'):.0f} | "
                      f"{m(X,'us_casts'):.2f}/{m(X,'them_casts'):.2f} | {100*m(X,'us_focus'):.0f}%/{100*m(X,'them_focus'):.0f}% | {m(X,'us_early_hits'):.1f}/{m(X,'them_early_hits'):.1f} | "
                      f"{m(X,'us_retreats'):.2f}/{m(X,'them_retreats'):.2f} | {m(X,'us_deaths'):.2f}/{m(X,'them_deaths'):.2f} | {100*sum(x['first_hit_by_us'] for x in X)/len(X):.0f}% |")
    table('By game result', [('our wins', [x for x in E if x['win']]), ('our losses', [x for x in E if not x['win']])])
    lost = [x for x in E if x['us_deaths'] > x['them_deaths']]; won = [x for x in E if x['us_deaths'] < x['them_deaths']]
    even = [x for x in E if x['us_deaths'] == x['them_deaths']]
    table('By engagement outcome (deaths)', [('fights we lost', lost), ('even', even), ('fights we won', won)])


if __name__ == '__main__':
    main(sys.argv[1:])
