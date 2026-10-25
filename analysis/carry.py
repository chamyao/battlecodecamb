"""Item concentration per version: per game, our champions' item points (and strength) at rounds
400 and 600 — the max over our champions, the team mean, and the max/mean ratio.

Usage: python3 carry.py LIVEDIR EXDIR VERSION [VERSION ...]
"""
import json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fight_dump
from analyse import CH


def main(livedir, exdir, *versions):
    sides = json.load(open(os.path.join(livedir, 'sides.json')))
    for ver in versions:
        rows = {400: [], 600: []}
        for v in sides.values():
            if v['version'] != ver:
                continue
            d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1
            ours = [c['i'] for c in d['champions'] if c['team'] == us]
            hist = fight_dump.inventories(d)
            for r in rows:
                if d['rounds_played'] < r:
                    continue
                S = [fight_dump.stats_from_items(CH[d['champions'][i]['type']], fight_dump.inv_at(hist, i, r)) for i in ours]
                pts = [sum(s['pts'].values()) for s in S]
                rows[r].append((max(pts), statistics.mean(pts), max(s['str'] for s in S)))
        out = [f'{ver}:']
        for r, X in rows.items():
            if X:
                out.append(f"r{r} (n={len(X)}) max item points {statistics.mean(x[0] for x in X):.1f}, team mean {statistics.mean(x[1] for x in X):.1f}, "
                           f"max/mean {statistics.mean(x[0] / max(1, x[1]) for x in X):.2f}, max strength {statistics.mean(x[2] for x in X):.0f}")
        print(' | '.join(out))


if __name__ == '__main__':
    main(*sys.argv[1:])
