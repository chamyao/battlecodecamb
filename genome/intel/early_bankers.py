"""What early-banking opponents do after their first bank (real replays), for stress/rushbank-v2.

Usage: python3 -I genome/intel/early_bankers.py ANALYSIS_DIR OPP_SUBSTRING LABEL=FETCHDIR,EXDIR [...]
Per game vs the opponent: their first tribute, their first kill on us, kill bounties (gold credited with a kill) by
r500, our deaths before r500; and for each such death, the round relative to their first tribute and to OUR first
tribute, whether the victim carried gems, was alone (no ally within 5), the enemy pack within 5, and where: our or
their half (nearer our or their spawn), within 2 of a camp spawn, within 3 of an altar.
"""
import collections, json, os, statistics, sys


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main(argv):
    adir, sub = argv[0], argv[1]
    sys.path.insert(0, os.path.abspath(adir))
    import analyse, mapinfo
    G = []; D = []
    for spec in argv[2:]:
        label, dirs = spec.split('=', 1); fd, ex = dirs.split(',')
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            opp = v['B'] if v['A'] == 'Master' else v['A']
            if sub.lower() not in opp.lower():
                continue
            d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1; th = 1 - us
            m = mapinfo.replay_map(d['file'])
            st = analyse.game_stats(d, (v['A'], v['B']))
            team = {c['i']: c['team'] for c in d['champions']}
            ours = [i for i in team if team[i] == us]; theirs = [i for i in team if team[i] == th]
            R = {r: cs for r, _, _, cs in d['rounds']}
            sp = [[(x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])] for a in m['spawn']]
            camps = [(c['x'], c['y']) for c in d['camps']]; alt = [tuple(a) for a in m['altars']]
            ft_them = min([t[0] for t in st[th]['lists'].get('tribute', [])], default=2000)
            ft_us = min([t[0] for t in st[us]['lists'].get('tribute', [])], default=2000)
            bounty = 0; first_kill = None; nd = 0
            for e in d['events']:
                if e['a'][0] != 1 or team.get(e['a'][1]) != th:
                    continue
                for y in e.get('d', []):
                    if y.get('kills', 0) > 0 and team.get(y['i']) == th and e['r'] <= 500:
                        bounty += max(0, y.get('gold', 0))
                for y in e.get('d', []):
                    if y.get('alive') == 0 and team.get(y['i']) == us:
                        r = e['r']; first_kill = first_kill or r
                        if r > 500:
                            continue
                        cs = R.get(r - 1)
                        if not cs:
                            continue
                        nd += 1
                        p = (cs[y['i']][4], cs[y['i']][5])
                        D.append(dict(after_their=r - ft_them, after_ours=r - ft_us, carrying=cs[y['i']][1] > 0,
                                      alone=not any(j != y['i'] and cs[j][2] and cheb((cs[j][4], cs[j][5]), p) <= 5 for j in ours),
                                      pack=sum(1 for j in theirs if cs[j][2] and cheb((cs[j][4], cs[j][5]), p) <= 5),
                                      our_half=min(cheb(p, t) for t in sp[us]) < min(cheb(p, t) for t in sp[th]),
                                      at_camp=any(cheb(p, c) <= 2 for c in camps), at_altar=any(cheb(p, a) <= 3 for a in alt)))
            G.append(dict(label=label, map=v['map'], win=(d['outcome'] == 1) == (us == 0), ft_them=ft_them, ft_us=ft_us,
                          first_kill=first_kill or 2000, bounty=bounty, deaths500=nd))
    if not G:
        print('no games'); return
    md = lambda k: statistics.median(g[k] for g in G); mn = lambda k: statistics.mean(g[k] for g in G)
    print(f"{sub}: {len(G)} games, our record {sum(g['win'] for g in G)}-{sum(not g['win'] for g in G)}")
    print(f"- their first tribute: median r{md('ft_them'):.0f} (ours r{md('ft_us'):.0f}); their first kill on us: median r{md('first_kill'):.0f}")
    print(f"- by r500: our deaths to them {mn('deaths500'):.1f} per game; kill bounties {mn('bounty'):.0f} gold per game")
    if D:
        n = len(D); pc = lambda f: f'{100 * sum(1 for x in D if f(x)) / n:.0f}%'
        print(f"- our {n} deaths before r500: carrying {pc(lambda x: x['carrying'])}, alone {pc(lambda x: x['alone'])}, "
              f"pack within 5 {statistics.mean(x['pack'] for x in D):.1f}, in our half {pc(lambda x: x['our_half'])}, "
              f"at a camp {pc(lambda x: x['at_camp'])}, at an altar {pc(lambda x: x['at_altar'])}")
        print(f"  rounds after THEIR first tribute: median {statistics.median(x['after_their'] for x in D):.0f}; "
              f"after OUR first tribute: median {statistics.median(x['after_ours'] for x in D):.0f}; "
              f"before our first tribute: {pc(lambda x: x['after_ours'] < 0)}")
    for g in sorted(G, key=lambda g: (g['map'], g['label'])):
        print(f"  {g['label']} {g['map']:18s} {'W' if g['win'] else 'L'} their ft r{g['ft_them']} ours r{g['ft_us']} first kill r{g['first_kill']} bounty500 {g['bounty']} deaths500 {g['deaths500']}")


if __name__ == '__main__':
    main(sys.argv[1:])
