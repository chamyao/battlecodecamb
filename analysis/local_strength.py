"""Local strength at champion deaths: who was outnumbered when a champion died to a champion?

Usage: python3 local_strength.py EXDIR SIDES.json [TEAM]
For each death to an enemy champion, counts living champions of each side within R=5 tiles
(Chebyshev) of the victim and sums their current HP, at the end of the round 3 rounds earlier
(before the fight resolved). Ratio = victim side's HP sum / killer side's HP sum.
"""
import collections, json, os, sys

R, LAG = 5, 3


def main(exdir, sides_path, me='Master'):
    sides = json.load(open(sides_path))
    rows = []
    for key, v in sides.items():
        d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
        us = 0 if v['A'] == me else 1
        team = {c['i']: c['team'] for c in d['champions']}
        state = {r: cs for r, _, _, cs in d['rounds']}
        win = (d['outcome'] == 1) == (us == 0)
        for e in d['events']:
            if e['a'][0] != 1:
                continue
            for x in e.get('d', []):
                if x.get('alive') != 0 or team[x['i']] == team[e['a'][1]]:
                    continue
                cs = state.get(e['r'] - LAG)
                if not cs:
                    continue
                vp = cs[x['i']]
                if not vp[2]:
                    continue
                near = [(i, c) for i, c in enumerate(cs) if c[2] and max(abs(c[4] - vp[4]), abs(c[5] - vp[5])) <= R]
                vt = team[x['i']]
                n_v = sum(1 for i, c in near if team[i] == vt); n_k = sum(1 for i, c in near if team[i] != vt)
                hp_v = sum(c[6] for i, c in near if team[i] == vt); hp_k = sum(c[6] for i, c in near if team[i] != vt)
                rows.append(dict(victim='us' if vt == us else 'them', n_v=n_v, n_k=n_k, ratio=hp_v / max(1, hp_k), win=win,
                                 hpfrac=vp[6] / vp[7] if vp[7] else 0))
    for who in ('us', 'them'):
        X = [r for r in rows if r['victim'] == who]
        if not X:
            continue
        n = len(X)
        out = sum(1 for r in X if r['n_v'] < r['n_k']); even = sum(1 for r in X if r['n_v'] == r['n_k']); up = n - out - even
        fav = sum(1 for r in X if r['ratio'] >= 1.0)
        print(f"Deaths of {who} to champions: {n}. Victim side outnumbered {100 * out / n:.0f}%, even numbers {100 * even / n:.0f}%, "
              f"victim side had more champions {100 * up / n:.0f}%. Victim side had >= the killers' total HP nearby in {100 * fav / n:.0f}%. "
              f"Victim at >= 50% health {LAG} rounds before: {100 * sum(1 for r in X if r['hpfrac'] >= 0.5) / n:.0f}%")
        c = collections.Counter((r['n_v'], r['n_k']) for r in X)
        print('  (victim side, killer side) champions within 5 tiles: ' + ', '.join(f'{a}v{b}: {k}' for (a, b), k in c.most_common(8)))


if __name__ == '__main__':
    main(*sys.argv[1:])
