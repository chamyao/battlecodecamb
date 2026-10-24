"""Sim counterpart of stuck.py: 2-cycle walking (A->B->A->B ...) of a genome side, from GENOME_TRACE lines.

Usage: python3 -m genome.intel.sim_stuck GENOME OPP [--games N] [--maps GLOB ...]
Counts, per game and side A, spells of 20+ consecutive rounds where a champion's only actions are moves that
undo the previous move, and the champion-rounds spent in them.
"""
import collections, glob, os, re, subprocess, sys
from genome.intel.sim_metrics import EVAL, ROOT, side

LINE = re.compile(r'@@G r(\d+) t(\d+) c(\d+) pos (-?\d+),(-?\d+) kind (\d+) score \S+ tile (-?\d+),(-?\d+) .* ok (\d+)')


def spells(trace, minlen=20):
    acts = collections.defaultdict(lambda: collections.defaultdict(list))
    for ln in trace.splitlines():
        m = LINE.match(ln)
        if m:
            r, t, c, px, py, k, tx, ty, ok = map(int, m.groups())
            acts[(t, c)][r].append((k, (px, py), (tx, ty), ok))
    out = []
    for key, by_r in acts.items():
        run, last = [], None
        for r in sorted(by_r):
            a = [x for x in by_r[r] if x[3]]
            mv = [x for x in a if x[0] == 2]
            only_move = len(a) == len(mv) == 1
            back = only_move and last is not None and mv[0][2] == last[1] and mv[0][1] == last[2] and r == last[0] + 1
            if back:
                run.append(r)
            else:
                if len(run) >= minlen:
                    out.append((key, run[0], len(run)))
                run = []
            last = (r, mv[0][1], mv[0][2]) if only_move else None
        if len(run) >= minlen:
            out.append((key, run[0], len(run)))
    return out


def main(argv):
    games, maps, args = 2, [], []
    i = 0
    while i < len(argv):
        if argv[i] == '--games': games = int(argv[i + 1]); i += 2
        elif argv[i] == '--maps':
            i += 1
            while i < len(argv) and not argv[i].startswith('--'):
                maps += sorted(glob.glob(argv[i])); i += 1
        else: args.append(argv[i]); i += 1
    maps = maps or sorted(glob.glob(os.path.join(ROOT, 'maps', '*.map26a')))
    a, b = side(args[0]), side(args[1])
    tot = n = 0
    for mp in maps:
        p = subprocess.run([EVAL, '--a', a, '--b', b, '--games', str(games), '--threads', '1', mp],
                           capture_output=True, text=True, env=dict(os.environ, GENOME_TRACE='1'))
        # the trace does not say which side is A: with --games 2 game 0 has A as team 0, game 1 as team 1;
        # count both teams and halve (both sides run the same evaluation order), or pass a non-genome OPP
        S = spells(p.stderr)
        k = sum(s[2] for s in S)
        tot += k; n += games
        if S:
            print(os.path.basename(mp), len(S), 'spells', k, 'rounds')
    print(f'{n} games: stuck champion-rounds per game {tot / n:.1f} (genome sides only: the trace covers genome sides)')


if __name__ == '__main__':
    main(sys.argv[1:])
