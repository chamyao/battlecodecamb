"""Carrier stalls: one of our champions holding 20+ gems that stays within 2 tiles of one spot for 60+
rounds while alive (stuck instead of banking). Per game and per map, with champion-rounds lost.

Usage: python3 stalls.py LIVEDIR EXDIR [VERSIONS comma-separated]
"""
import collections, json, os, sys


def stalls(d, us, minlen=60, radius=2, bag=20):
    team = {c['i']: c['team'] for c in d['champions']}
    R = [cs for _, _, _, cs in sorted(d['rounds'], key=lambda x: x[0])]
    out = []
    for i in (i for i in team if team[i] == us):
        k = 0
        while k < len(R):
            c = R[k][i]
            if not (c[2] and c[1] >= bag):
                k += 1
                continue
            j = k
            while j + 1 < len(R) and R[j + 1][i][2] and R[j + 1][i][1] >= bag and max(abs(R[j + 1][i][4] - c[4]), abs(R[j + 1][i][5] - c[5])) <= radius:
                j += 1
            if j - k >= minlen:
                out.append(dict(champ=i, start=k, length=j - k, pos=(c[4], c[5]), bag=c[1]))
                k = j + 1
            else:
                k += 1
    return out


def main(livedir, exdir, versions=None):
    vs = set(versions.split(',')) if versions else None
    sides = json.load(open(os.path.join(livedir, 'sides.json')))
    by_map, n, hit, tot, ex = collections.Counter(), 0, 0, 0, []
    for v in sides.values():
        if vs and v['version'] not in vs:
            continue
        p = os.path.join(exdir, 'ladder', v['file'])
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        us = 0 if v['A'] == 'Master' else 1
        n += 1
        S = stalls(d, us)
        if S:
            hit += 1
            by_map[v['map']] += 1
            L = sum(x['length'] for x in S)
            tot += L
            win = (d['outcome'] == 1) == (us == 0)
            ex.append((L, v['map'], v['kind'], v['created'][11:16], 'W' if win else 'L', [(x['pos'], x['bag'], x['start'], x['length']) for x in S][:3]))
    print(f'{n} games; {hit} with a carrier stall; {tot} champion-rounds stalled')
    print('by map:', by_map.most_common())
    for e in sorted(ex, reverse=True)[:12]:
        print(e)


if __name__ == '__main__':
    main(*sys.argv[1:])
