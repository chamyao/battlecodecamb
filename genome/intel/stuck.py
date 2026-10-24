"""Stuck champions in real games: spells of 20+ rounds where one of our champions is alive, off spawn and
not on a camp spawn tile, logs no action (no attack, cast, ward, shop, tribute, recall) and either stands
still or steps back and forth between two tiles (a 2-cycle: the walk goal or field flips with the tile).

Usage: python3 -I genome/intel/frozen.py ANALYSIS_DIR FETCHDIR EXDIR [FETCHDIR EXDIR ...]
Per game: spells, frozen rounds, gems held while frozen (max bag of each spell), and per map; then the
distance from each spell's tile to the nearest altar.
"""
import collections, json, os, statistics, sys


def spells(d, us, m, minlen=20):
    team = {c['i']: c['team'] for c in d['champions']}
    camp_tiles = {(c['x'], c['y']) for c in d['camps']}
    spawn = [set((x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])) for a in m['spawn']]
    acted = collections.defaultdict(set)
    for e in d['events']:
        if e['a'][0] == 1:
            acted[e['a'][1]].add(e['r'])
    out = []
    for i in (i for i in team if team[i] == us):
        run = []
        prev = prev2 = None
        for r, _, _, cs in d['rounds']:
            c = cs[i]
            p = (c[4], c[5])
            still = c[2] and (p == prev or p == prev2) and r not in acted[i] and p not in spawn[us] and p not in camp_tiles
            if still:
                run.append((r, c[1], p))
            else:
                if len(run) >= minlen:
                    out.append(dict(champ=i, start=run[0][0], n=len(run), bag=max(x[1] for x in run), pos=run[0][2]))
                run = []
            prev2, prev = prev, (p if c[2] else None)
        if len(run) >= minlen:
            out.append(dict(champ=i, start=run[0][0], n=len(run), bag=max(x[1] for x in run), pos=run[0][2]))
    return out


def main(argv):
    adir, pairs = argv[0], argv[1:]
    sys.path.insert(0, os.path.abspath(adir))
    import mapinfo
    rows = []
    for fd, ex in zip(pairs[::2], pairs[1::2]):
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            p = os.path.join(ex, 'ladder', v['file'])
            if not os.path.exists(p):
                continue
            d = json.load(open(p))
            us = 0 if v['A'] == 'Master' else 1
            m = mapinfo.replay_map(d['file'])
            S = spells(d, us, m)
            alt = [tuple(a) for a in m['altars']]
            for s in S:
                s['altar_d'] = min(max(abs(a[0] - s['pos'][0]), abs(a[1] - s['pos'][1])) for a in alt)
            rows.append(dict(map=v['map'], win=(d['outcome'] == 1) == (us == 0), sub=d['submitted'][us], S=S))
    n = len(rows)
    with_s = [r for r in rows if r['S']]
    allS = [s for r in rows for s in r['S']]
    print(f'{n} games; games with a stuck spell: {len(with_s)} ({100 * len(with_s) / n:.0f}%); spells {len(allS)}, '
          f'stuck champion-rounds per game {sum(s["n"] for s in allS) / n:.0f}; spells carrying gems {sum(1 for s in allS if s["bag"] > 0)}, '
          f'mean bag {statistics.mean([s["bag"] for s in allS]) if allS else 0:.1f}')
    for k in ('win', 'loss'):
        R = [r for r in rows if r['win'] == (k == 'win')]
        if R:
            print(f'  in {k}es: {sum(1 for r in R if r["S"])}/{len(R)} games, stuck rounds per game {sum(s["n"] for r in R for s in r["S"]) / len(R):.0f}')
    print('altar distance at spells:', sorted(collections.Counter(min(s['altar_d'], 9) for s in allS).items()))
    by = collections.defaultdict(list)
    for r in rows:
        by[r['map']].append(r)
    print('| map | games | stuck spells | stuck rounds | max bag | submitted |')
    print('|---|---|---|---|---|---|')
    for mp, R in sorted(by.items(), key=lambda kv: -sum(s['n'] for r in kv[1] for s in r['S'])):
        S = [s for r in R for s in r['S']]
        if S:
            print(f'| {mp} | {len(R)} | {len(S)} | {sum(s["n"] for s in S)} | {max(s["bag"] for s in S)} | {" ".join(str(r["sub"]) for r in R)} |')


if __name__ == '__main__':
    main(sys.argv[1:])
