"""What band opponents do around our deaths and over the game (real replays), to spec stress opponents.

Usage: python3 -I genome/intel/opp_patterns.py ANALYSIS_DIR FETCHDIR EXDIR [--losses-only]
Per death of ours to a champion: enemies within 5 at death and 10 rounds before (pack size, growth), distinct
enemy hitters in the last 3 rounds (focus fire), whether the killer had walked 6+ tiles toward the victim in
the 10 rounds before (chase), and where it happened (within 3 of an altar, within 6 of our spawn, carrying).
Per game: share of enemy champion-rounds within 3 of an altar / within 6 of our spawn region, against ours,
and the mean distance between enemy champions (grouping).
"""
import collections, json, os, statistics, sys


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main(argv):
    adir, fd, ex = argv[:3]
    lonly = '--losses-only' in argv
    sys.path.insert(0, os.path.abspath(adir))
    import mapinfo
    D = collections.Counter(); N = 0
    G = collections.defaultdict(list)
    for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
        d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
        us = 0 if v['A'] == 'Master' else 1
        win = (d['outcome'] == 1) == (us == 0)
        if lonly and win:
            continue
        m = mapinfo.replay_map(d['file'])
        team = {c['i']: c['team'] for c in d['champions']}
        ours = [i for i in team if team[i] == us]; theirs = [i for i in team if team[i] != us]
        R = {r: cs for r, _, _, cs in d['rounds']}
        alt = [tuple(a) for a in m['altars']]
        sp = m['spawn'][us]; spawn = [(x, y) for x in range(sp[0], sp[2]) for y in range(sp[1], sp[3])]
        pos = lambda cs, i: (cs[i][4], cs[i][5])
        hits = collections.defaultdict(list)
        for e in d['events']:
            if e['k'] in ('Attack', 'Cast ability') and e['a'][0] == 1 and team.get(e['a'][1]) not in (None, us):
                for y in e.get('d', []):
                    if team.get(y['i']) == us and y.get('hp', 0) < 0:
                        hits[y['i']].append((e['r'], e['a'][1]))
        for e in d['events']:
            if e['a'][0] != 1 or team.get(e['a'][1]) in (None, us):
                continue
            for y in e.get('d', []):
                if y.get('alive') != 0 or team.get(y['i']) != us:
                    continue
                r, vi, k = e['r'], y['i'], e['a'][1]
                a, b = R.get(r - 1), R.get(r - 11)
                if not a or not b:
                    continue
                vp = pos(a, vi)
                n0 = sum(1 for j in theirs if a[j][2] and cheb(pos(a, j), vp) <= 5)
                n10 = sum(1 for j in theirs if b[j][2] and cheb(pos(b, j), pos(b, vi)) <= 5)
                u0 = sum(1 for j in ours if j != vi and a[j][2] and cheb(pos(a, j), vp) <= 5)
                hitters = {h for rr, h in hits[vi] if r - 3 <= rr <= r}
                N += 1
                D['pack3+'] += n0 >= 3; D['pack2+'] += n0 >= 2; D['grew'] += n0 > n10
                D['focus2+'] += len(hitters) >= 2; D['focus3+'] += len(hitters) >= 3
                D['chase'] += b[k][2] and cheb(pos(b, k), pos(b, vi)) - cheb(pos(a, k), vp) >= 6
                D['near_altar'] += min(cheb(vp, t) for t in alt) <= 3
                D['near_our_spawn'] += min(cheb(vp, t) for t in spawn) <= 6
                D['carrying'] += a[vi][1] > 0
                D['alone'] += u0 == 0
                G['pack'].append(n0); G['allies'].append(u0)
        # whole-game positioning
        ea = eb = oa = ob = en = on = 0; gd = []
        for r, cs in R.items():
            if r % 5:
                continue
            E = [pos(cs, j) for j in theirs if cs[j][2]]; O = [pos(cs, j) for j in ours if cs[j][2]]
            for p in E:
                en += 1; ea += min(cheb(p, t) for t in alt) <= 3; eb += min(cheb(p, t) for t in spawn) <= 6
            for p in O:
                on += 1; oa += min(cheb(p, t) for t in alt) <= 3
            if len(E) >= 2:
                gd.append(statistics.mean(cheb(E[x], E[y]) for x in range(len(E)) for y in range(x + 1, len(E))))
        G['enemy_at_altar'].append(ea / max(1, en)); G['our_at_altar'].append(oa / max(1, on))
        G['enemy_near_our_spawn'].append(eb / max(1, en)); G['enemy_spread'].append(statistics.mean(gd) if gd else 0)
    print(f"{N} deaths of ours to champions{' (losses only)' if lonly else ''}:")
    for k in ('pack2+', 'pack3+', 'grew', 'focus2+', 'focus3+', 'chase', 'alone', 'carrying', 'near_altar', 'near_our_spawn'):
        print(f'- {k}: {100 * D[k] / max(1, N):.0f}%')
    print(f"- enemies within 5 at death: mean {statistics.mean(G['pack']):.2f}; our allies within 5: {statistics.mean(G['allies']):.2f}")
    print(f"Positioning (champion-rounds): enemy within 3 of an altar {100 * statistics.mean(G['enemy_at_altar']):.0f}% (ours {100 * statistics.mean(G['our_at_altar']):.0f}%), "
          f"enemy within 6 of our spawn {100 * statistics.mean(G['enemy_near_our_spawn']):.0f}%, mean distance between enemy champions {statistics.mean(G['enemy_spread']):.1f}")


if __name__ == '__main__':
    main(sys.argv[1:])
