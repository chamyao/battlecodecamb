"""Economy mechanism in real games: gold income by source per 50 rounds, gold per capture, purchases to r500.

Usage: python3 -I genome/intel/econ_source.py ANALYSIS_DIR FETCHDIR EXDIR [--opp SUBSTRING] [--to 500]
Per side (us / them), averaged over games and split by our wins and losses (or only games vs --opp):
- gold per 50-round bin from captures, from kills, and other (any other positive gold diff: passives, camp kills);
- capture gold per capture and per gem-capture (the same group pays more with gold passives such as Treasure);
- shards bought by family up to --to (Treasure, Power, ...), gold spent, the round of each side's first Treasure
  emblem (5 Treasure shards of one stat on one champion), and whether the side drafted Vesper Vale.
"""
import collections, json, os, statistics, sys

FAM = ['Monster', 'Power', 'Durability', 'Treasure', 'Jungle', 'Home', 'Bruiser']


def main(argv):
    adir, fd, ex = argv[:3]
    opp = argv[argv.index('--opp') + 1] if '--opp' in argv else None
    TO = int(argv[argv.index('--to') + 1]) if '--to' in argv else 500
    sys.path.insert(0, os.path.abspath(adir))
    import analyse
    from analyse import CH
    rows = []
    for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
        o = v['B'] if v['A'] == 'Master' else v['A']
        if opp and opp.lower() not in o.lower():
            continue
        d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
        us = 0 if v['A'] == 'Master' else 1
        team = {c['i']: c['team'] for c in d['champions']}; name = {c['i']: CH[c['type']] for c in d['champions']}
        row = dict(win=(d['outcome'] == 1) == (us == 0))
        for side, t in (('us', us), ('them', 1 - us)):
            bins = collections.defaultdict(lambda: collections.Counter())
            shards = collections.Counter(); spent = 0; caps = 0; capg = 0
            tre = collections.Counter(); first_emblem = 2000
            for e in d['events']:
                r = e['r']
                for x in e.get('d', []):
                    if x['i'] not in team or team[x['i']] != t:
                        continue
                    g = x.get('gold', 0)
                    if e['k'] == 'Shop':
                        if r <= TO:
                            spent += -g
                            for it, n in x.get('items', []):
                                fam = FAM[it // 6] if it // 6 < len(FAM) else '?'
                                shards[fam] += n
                                if fam == 'Treasure' and (it % 6) % 2 == 0:
                                    tre[(x['i'], it)] += n
                                    if tre[(x['i'], it)] >= 5:
                                        first_emblem = min(first_emblem, r)
                        continue
                    if g <= 0 or e['k'] == 'Sell item':
                        continue
                    src = 'capture' if e['k'] == 'Capture' else 'kills' if x.get('kills', 0) > 0 else 'other'
                    if src == 'capture':
                        caps += 1; capg += g
                    if r <= TO:
                        bins[min(r // 50, TO // 50 - 1)][src] += g
            row[side] = dict(bins=bins, shards=shards, spent=spent, cap_per=capg / max(1, caps), first_emblem=first_emblem,
                             vesper=any(name[i] == 'Vesper Vale' for i in team if team[i] == t),
                             cap_total=sum(b['capture'] for b in bins.values()), kill_total=sum(b['kills'] for b in bins.values()),
                             other_total=sum(b['other'] for b in bins.values()))
        rows.append(row)
    if not rows:
        print('no games'); return
    groups = [('vs ' + opp, rows)] if opp else [('our wins', [r for r in rows if r['win']]), ('our losses', [r for r in rows if not r['win']])]
    for g, R in groups:
        if not R:
            continue
        m = lambda s, k: statistics.mean(r[s][k] for r in R)
        print(f'\n## {g} ({len(R)} games), up to r{TO}\n')
        print('| per game | us | them |')
        print('|---|---|---|')
        for k, nm in (('cap_total', 'gold from captures'), ('kill_total', 'gold from kills'), ('other_total', 'other gold (passives etc.)'),
                      ('cap_per', 'gold per capture (whole game; receiving champions)'), ('spent', 'gold spent in the shop')):
            print(f'| {nm} | {m("us", k):.0f} | {m("them", k):.0f} |')
        print(f'| first Treasure emblem (median round) | r{statistics.median(r["us"]["first_emblem"] for r in R):.0f} | r{statistics.median(r["them"]["first_emblem"] for r in R):.0f} |')
        print(f'| drafted Vesper Vale | {100 * sum(r["us"]["vesper"] for r in R) / len(R):.0f}% | {100 * sum(r["them"]["vesper"] for r in R) / len(R):.0f}% |')
        fams = sorted({f for r in R for s in ('us', 'them') for f in r[s]['shards']})
        for f in fams:
            print(f'| {f} shards bought | {statistics.mean(r["us"]["shards"][f] for r in R):.1f} | {statistics.mean(r["them"]["shards"][f] for r in R):.1f} |')
        print('\n| rounds | capture us / them | kills us / them | other us / them |')
        print('|---|---|---|---|')
        for b in range(TO // 50):
            c = lambda s, k: statistics.mean(r[s]['bins'][b][k] for r in R)
            print(f'| {50 * b}-{50 * b + 49} | {c("us", "capture"):.0f} / {c("them", "capture"):.0f} | {c("us", "kills"):.0f} / {c("them", "kills"):.0f} | {c("us", "other"):.0f} / {c("them", "other"):.0f} |')


if __name__ == '__main__':
    main(sys.argv[1:])
