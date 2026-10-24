"""Pair two batches game by game (same opponent, map and side) from batch_report.py --json outputs.

Usage: python3 genome/intel/paired.py BEFORE.json AFTER.json
Prints, over the pairs found: record before/after, flips, and per-game mean change (± SE) in gems submitted, stuck
champion-rounds, deaths to monoliths / camps / champions, gems lost on death and gems per capture.
"""
import json, statistics, sys


def main(a, b):
    A = {(g['opp'], g['map'], g['side']): g for g in json.load(open(a))['games']}
    B = {(g['opp'], g['map'], g['side']): g for g in json.load(open(b))['games']}
    keys = sorted(set(A) & set(B))
    print(f'{len(keys)} paired games; record before {sum(A[k]["win"] for k in keys)}-{sum(not A[k]["win"] for k in keys)}, '
          f'after {sum(B[k]["win"] for k in keys)}-{sum(not B[k]["win"] for k in keys)}; flips to win '
          f'{sum(B[k]["win"] and not A[k]["win"] for k in keys)}, to loss {sum(A[k]["win"] and not B[k]["win"] for k in keys)}')
    for f, nm in (('sub', 'gems submitted'), ('stuck', 'stuck champion-rounds'), ('d_mono', 'deaths to monoliths'),
                  ('d_camp', 'deaths to camps'), ('d_champ', 'deaths to champions'), ('lost', 'gems lost on death'),
                  ('ncap', 'captures'), ('cap', 'gems captured')):
        d = [B[k][f] - A[k][f] for k in keys]
        se = statistics.pstdev(d) / len(d) ** 0.5 if len(d) > 1 else 0
        print(f'- {nm}: {statistics.mean(A[k][f] for k in keys):.1f} -> {statistics.mean(B[k][f] for k in keys):.1f} '
              f'(change {statistics.mean(d):+.1f} ± {se:.1f})')
    gpc = lambda G: sum(G[k]['cap'] for k in keys) / max(1, sum(G[k]['ncap'] for k in keys))
    print(f'- gems per capture: {gpc(A):.1f} -> {gpc(B):.1f}')


if __name__ == '__main__':
    main(*sys.argv[1:3])
