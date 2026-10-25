"""Rich-group contest in real games: who takes the rich gem groups, how early, and what happens when we are there.

Usage: python3 -I genome/intel/yield_contest.py ANALYSIS_DIR FETCHDIR EXDIR [--min-gems 14]
A rich group pays --min-gems or more per capture. Per game (split by our wins and losses): rich captures us / them,
the round of each side's first rich capture, our share of rich-group gems; then, for each of our deaths within 3 tiles
of a rich group's spawn tiles, the enemy pack within 5 and whether we had captured that group before. Also the
distance from each side's spawn to its nearest rich group (map asymmetry check).
"""
import collections, json, os, statistics, sys


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main(argv):
    adir, fd, ex = argv[:3]
    k = argv.index('--min-gems') if '--min-gems' in argv else None
    MIN = int(argv[k + 1]) if k else 14
    sys.path.insert(0, os.path.abspath(adir))
    import analyse, mapinfo
    rows = []; deaths = collections.defaultdict(list)
    for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
        d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
        us = 0 if v['A'] == 'Master' else 1; th = 1 - us
        win = (d['outcome'] == 1) == (us == 0)
        st = analyse.game_stats(d, (v['A'], v['B']))
        m = mapinfo.replay_map(d['file'])
        groups = analyse.camp_groups(d['camps'])
        rich_tiles = set()
        cap_by = {us: collections.Counter(), th: collections.Counter()}
        first = {us: 2000, th: 2000}; gems = {us: 0, th: 0}; n = {us: 0, th: 0}
        for t in (us, th):
            for c in st[t]['lists'].get('capture', []):
                if c[2] >= MIN:
                    n[t] += 1; gems[t] += c[2]; first[t] = min(first[t], c[0]); cap_by[t][c[1]] += 1
        for g in groups:
            # a group is rich if any capture of its name paid MIN+ (names identify groups by composition)
            rich_tiles |= {(c['x'], c['y']) for c in g} if any(nm == analyse.gname(g) for nm in list(cap_by[us]) + list(cap_by[th])) else set()
        sp = [[(x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])] for a in m['spawn']]
        near_rich = lambda t: min((cheb(p, r) for p in sp[t] for r in rich_tiles), default=99)
        rows.append(dict(win=win, n_us=n[us], n_them=n[th], first_us=first[us], first_them=first[th],
                         share=gems[us] / max(1, gems[us] + gems[th]), dist_us=near_rich(us), dist_them=near_rich(th)))
        team = {c['i']: c['team'] for c in d['champions']}
        R = {r: cs for r, _, _, cs in d['rounds']}
        caps_us = sorted(c[0] for c in st[us]['lists'].get('capture', []) if c[2] >= MIN)
        for e in d['events']:
            for y in e.get('d', []):
                if y.get('alive') == 0 and team.get(y['i']) == us:
                    cs = R.get(e['r'] - 1)
                    if not cs:
                        continue
                    p = (cs[y['i']][4], cs[y['i']][5])
                    if rich_tiles and min(cheb(p, r) for r in rich_tiles) <= 3:
                        pack = sum(1 for j in team if team[j] == th and cs[j][2] and cheb((cs[j][4], cs[j][5]), p) <= 5)
                        deaths['win' if win else 'loss'].append(dict(r=e['r'], pack=pack, to_champ=e['a'][0] == 1 and team.get(e['a'][1]) == th,
                                                                     had_captured=any(c < e['r'] for c in caps_us)))
    for lab, sel in (('wins', True), ('losses', False)):
        R_ = [r for r in rows if r['win'] == sel]
        if not R_:
            continue
        m_ = lambda k_: statistics.mean(r[k_] for r in R_); md = lambda k_: statistics.median(r[k_] for r in R_)
        print(f"{lab} ({len(R_)}): rich captures us/them {m_('n_us'):.1f}/{m_('n_them'):.1f}; our share of rich gems {100 * m_('share'):.0f}%; "
              f"first rich capture us/them r{md('first_us'):.0f}/r{md('first_them'):.0f}; spawn→nearest rich group us/them {m_('dist_us'):.1f}/{m_('dist_them'):.1f}")
        D = deaths['win' if sel else 'loss']
        if D:
            print(f"   our deaths within 3 of a rich group: {len(D) / len(R_):.1f} per game, to champions {100 * sum(x['to_champ'] for x in D) / len(D):.0f}%, "
                  f"enemy pack within 5 {statistics.mean(x['pack'] for x in D):.1f}, before r500 {100 * sum(x['r'] <= 500 for x in D) / len(D):.0f}%")


if __name__ == '__main__':
    main(sys.argv[1:])
