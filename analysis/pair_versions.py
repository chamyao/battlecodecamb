"""Paired band-batch comparison: newest version vs older ones on the same (opponent, map) unranked games.

Usage: python3 pair_versions.py LIVEDIR EXDIR NEW OLD [OLD...]
Prints record, gem and margin deltas with SE, flips, and per-version death/yield/fuel/cause summaries.
"""
import json, sys, statistics as S, collections
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_digest as L
LIVE, EX = sys.argv[1], sys.argv[2]
s = json.load(open(LIVE+'/sides.json'))
def batch(ver, kind='unranked'):
    out = {}
    for v in s.values():
        if v['version'] == ver and v['kind'] == kind:
            try: g = L.digest(EX, v, LIVE)
            except Exception as e: print('err', v['file'], e); continue
            out[(g['opp'], g['map'])] = g
    return out
vers = sys.argv[3:]
B = {x: batch(x) for x in vers}
new = vers[0]
for old in vers[1:]:
    keys = sorted(set(B[new]) & set(B[old]))
    a = [B[new][k] for k in keys]; b = [B[old][k] for k in keys]
    d = [x['sub'][0]-x['sub'][1]-(y['sub'][0]-y['sub'][1]) for x, y in zip(a, b)]
    gu = [x['sub'][0]-y['sub'][0] for x, y in zip(a, b)]
    fl = sum(1 for x, y in zip(a, b) if x['win'] and not y['win']); fw = sum(1 for x, y in zip(a, b) if y['win'] and not x['win'])
    se = lambda z: S.stdev(z)/len(z)**.5
    print(f"{new} vs {old}: n={len(keys)} rec {sum(x['win'] for x in a)}-{len(a)-sum(x['win'] for x in a)} vs {sum(y['win'] for y in b)}-{len(b)-sum(y['win'] for y in b)} | our gems {S.mean(gu):+.0f}±{se(gu):.0f} margin {S.mean(d):+.0f}±{se(d):.0f} | flips L->W {fl} W->L {fw}")
    for k, x, y in zip(keys, a, b):
        if x['win'] != y['win']:
            print('   flip', k, 'new', 'W' if x['win'] else 'L', x['sub'], 'mono', x['deaths'][2], '| old', 'W' if y['win'] else 'L', y['sub'], 'mono', y['deaths'][2], x['causes'])
for x in vers:
    g = list(B[x].values()); n = len(g)
    m = lambda f: sum(f(z) for z in g)/n
    mono = collections.Counter()
    for z in g: mono[z['map']] += z['deaths'][2]
    print(f"{x}: n={n} {sum(z['win'] for z in g)}-{n-sum(z['win'] for z in g)} gems {m(lambda z:z['sub'][0]):.0f} vs {m(lambda z:z['sub'][1]):.0f} | champ/camp/mono deaths {m(lambda z:z['deaths'][0]):.1f}/{m(lambda z:z['deaths'][1]):.1f}/{m(lambda z:z['deaths'][2]):.2f} | gpc {m(lambda z:z['gpc'][0]):.1f} | ft {S.median([z['ft'][0] or 2000 for z in g])} | lost {m(lambda z:z['lost']):.0f} | fuel {m(lambda z:z['fuel'] or 0):.1f} faults {sum(z['faults'] or 0 for z in g)} | mono top {mono.most_common(3)}")
    print('   causes', collections.Counter(c for z in g for c in z['causes']).most_common())
