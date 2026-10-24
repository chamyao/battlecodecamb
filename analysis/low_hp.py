"""What champions do after dropping below half HP with an enemy champion within 5 tiles.

Usage: python3 low_hp.py TEAM LABEL=EXDIR,FETCHDIR [...]
For each crossing (HP fraction >= 0.5 the round before, < 0.5 now, an enemy within 5), the outcome
within 15 rounds: died; got home (recall or walked onto spawn) alive; broke contact (no enemy
within 8 for the last 3 rounds) alive; or still in contact. Reported for TEAM's champions and for
ours in the same games, plus the median rounds to death and the tiles moved away in 5 rounds.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapinfo


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def main(team_name, *specs):
    out = {'them': collections.Counter(), 'us': collections.Counter()}
    away = {'them': [], 'us': []}
    recall_started = {'them': 0, 'us': 0}
    for s in specs:
        ex, fd = s.split('=', 1)[1].split(',')
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            o = v['B'] if v['A'] == 'Master' else v['A']
            if o != team_name:
                continue
            d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1
            m = mapinfo.replay_map(d['file'])
            spawn = [set((x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])) for a in m['spawn']]
            team = {c['i']: c['team'] for c in d['champions']}
            R = {r: cs for r, _, _, cs in d['rounds']}
            rec = collections.defaultdict(set)
            for e in d['events']:
                if e['k'] == 'Recall' and e['a'][0] == 1:
                    rec[e['a'][1]].add(e['r'])
            for r in sorted(R):
                a, b = R.get(r - 1), R[r]
                if not a:
                    continue
                for i, c in enumerate(b):
                    if not (c[2] and a[i][2] and c[7] and a[i][6] / a[i][7] >= 0.5 and c[6] / c[7] < 0.5):
                        continue
                    foes = [j for j, x in enumerate(b) if team[j] != team[i] and x[2]]
                    if not any(cheb((b[j][4], b[j][5]), (c[4], c[5])) <= 5 for j in foes):
                        continue
                    who = 'us' if team[i] == us else 'them'
                    own = spawn[team[i]]
                    res = 'in contact'
                    for k in range(r + 1, r + 16):
                        x = R.get(k)
                        if not x:
                            break
                        if not x[i][2]:
                            res = 'died'; break
                        if (x[i][4], x[i][5]) in own:
                            res = 'got home'; break
                    if res == 'in contact':
                        last = [R.get(k) for k in range(r + 13, r + 16)]
                        if all(x and not any(x[j][2] and cheb((x[j][4], x[j][5]), (x[i][4], x[i][5])) <= 8 for j in foes) for x in last):
                            res = 'broke contact'
                    out[who][res] += 1
                    if any(r <= k <= r + 5 for k in rec[i]):
                        recall_started[who] += 1
                    x5 = R.get(r + 5)
                    if x5 and x5[i][2]:
                        near = min(foes, key=lambda j: cheb((b[j][4], b[j][5]), (c[4], c[5])))
                        away[who].append(cheb((x5[i][4], x5[i][5]), (x5[near][4], x5[near][5])) - cheb((c[4], c[5]), (b[near][4], b[near][5])))
    for who in ('them', 'us'):
        n = sum(out[who].values())
        print(f"{team_name if who == 'them' else 'us'}: {n} crossings; " + ', '.join(f"{k} {100 * v / max(1, n):.0f}%" for k, v in out[who].most_common()) +
              f"; recall started within 5 rounds {100 * recall_started[who] / max(1, n):.0f}%; distance gained from the nearest enemy in 5 rounds (median) {statistics.median(away[who]) if away[who] else '-'}")


if __name__ == '__main__':
    main(*sys.argv[1:])
