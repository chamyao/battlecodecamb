"""Per-batch gap numbers for GAPS.md from real games of our live bot (match-group downloads).

Usage: python3 -I genome/intel/batch_report.py ANALYSIS_DIR FETCHDIR EXDIR [FETCHDIR EXDIR ...] [--json OUT]
ANALYSIS_DIR: the analysis/ directory of branch analysis/sprint1 (git worktree add <dir> origin/analysis/sprint1);
its replay tools make the inputs: fetch_groups.py FETCHDIR <groups>, ladder_prep.py FETCHDIR EXDIR, extract.js.
Prints, over all games pooled: each gap metric with a bootstrap SE (1000 resamples of games), split by our
wins and losses, the per-map record, the loss-cause tally (live_digest.py's labels) and the wins a fixed
gem gain would flip (losses whose final margin is under X).
"""
import collections, json, os, random, statistics, sys


def boot(xs, f, n=1000):
    est = f(xs)
    rnd = random.Random(1)
    bs = []
    for _ in range(n):
        s = [xs[rnd.randrange(len(xs))] for _ in xs]
        try:
            bs.append(f(s))
        except (ZeroDivisionError, statistics.StatisticsError):
            pass
    return est, statistics.pstdev(bs) if bs else 0


def main(argv):
    out = None
    if '--json' in argv:
        k = argv.index('--json'); out = argv[k + 1]; del argv[k:k + 2]
    adir, pairs = argv[0], argv[1:]
    sys.path.insert(0, os.path.abspath(adir))
    import analyse, mapinfo, race_analysis
    from live_digest import digest
    G = []
    for fd, ex in zip(pairs[::2], pairs[1::2]):
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            if not os.path.exists(os.path.join(ex, 'ladder', v['file'])):
                continue
            g = digest(ex, v)
            d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1
            m = mapinfo.replay_map(d['file'])
            team = {c['i']: c['team'] for c in d['champions']}
            st = analyse.game_stats(d, (v['A'], v['B']))
            u, t = (race_analysis.side_numbers(d, st, x, m, team) for x in (us, 1 - us))
            caps = st[us]['lists'].get('capture', [])
            G.append(dict(
                win=g['win'], opp=g['opp'], map=g['map'], sub=g['sub'][0], sub_them=g['sub'][1],
                margin=g['sub'][1] - g['sub'][0], causes=g['causes'],
                d_champ=g['deaths'][0], d_camp=g['deaths'][1], d_mono=g['deaths'][2], lost=g['lost'],
                cap=u['gems_cap'], cap_them=t['gems_cap'], ncap=u['caps'], ncap_them=t['caps'],
                gold_caps=sum(1 for c in caps if c[2] == 0), mono_gems=u['src'].get('monolith', 0),
                trib=u['tributes'], trib_them=t['tributes'], bag=u['bag'] or 0, bag_them=t['bag'] or 0,
                ft=u['first_trib'] or 2000, ft_them=t['first_trib'] or 2000,
                c250=u['curve'][250], c250_them=t['curve'][250], c500=u['curve'][500], c500_them=t['curve'][500],
                gold=u['gold'], gold_them=t['gold'], near=u['near'], near_them=t['near'],
                mono_map=any(c['type'] == 4 for c in d['camps'])))
    W = [x for x in G if x['win']]
    L = [x for x in G if not x['win']]
    P = print
    mean = lambda k: (lambda gs: sum(x[k] for x in gs) / len(gs))
    ratio = lambda a, b: (lambda gs: sum(x[a] for x in gs) / sum(x[b] for x in gs))
    med = lambda k: (lambda gs: statistics.median(x[k] for x in gs))
    pct = lambda f: (lambda gs: sum(1 for x in gs if f(x)) / len(gs))

    def cell(f, gs, p=False):
        if not gs:
            return '-'
        e, se = boot(gs, f)
        return f'{100 * e:.0f}% ± {100 * se:.0f}' if p else f'{e:.1f} ± {se:.1f}'
    P(f'{len(G)} games, our record {len(W)}-{len(L)}\n')
    P('| metric | all | our wins | our losses |')
    P('|---|---|---|---|')
    rows = [
        ('win rate', pct(lambda x: x['win']), True),
        ('gems submitted, us / them', None, False),
        ('our deaths to champions', mean('d_champ'), False),
        ('our deaths to camps', mean('d_camp'), False),
        ('our deaths to monoliths', mean('d_mono'), False),
        ('our deaths to monoliths, monolith maps only', lambda gs: mean('d_mono')([x for x in gs if x['mono_map']]), False),
        ('gems lost on death, us', mean('lost'), False),
        ('gems captured, us', mean('cap'), False), ('gems captured, them', mean('cap_them'), False),
        ('gems per capture, us', ratio('cap', 'ncap'), False), ('gems per capture, them', ratio('cap_them', 'ncap_them'), False),
        ('captures, us', mean('ncap'), False), ('captures, them', mean('ncap_them'), False),
        ('gold-only (0-gem) captures, us', mean('gold_caps'), False),
        ('share of captured gems submitted, us', ratio('sub', 'cap'), True),
        ('tributes, us', mean('trib'), False), ('tributes, them', mean('trib_them'), False),
        ('median bag at tribute, us', med('bag'), False), ('median bag at tribute, them', med('bag_them'), False),
        ('first tribute round, us (median)', med('ft'), False), ('first tribute round, them (median)', med('ft_them'), False),
        ('submitted by r250, us', mean('c250'), False), ('submitted by r250, them', mean('c250_them'), False),
        ('submitted by r500, us', mean('c500'), False), ('submitted by r500, them', mean('c500_them'), False),
        ('gold earned, us', mean('gold'), False), ('gold earned, them', mean('gold_them'), False),
    ]
    res = {}
    for name, f, p in rows:
        if f is None:
            cells = [f"{statistics.mean(x['sub'] for x in gs):.0f} / {statistics.mean(x['sub_them'] for x in gs):.0f}" if gs else '-' for gs in (G, W, L)]
        else:
            cells = [cell(f, gs, p) for gs in (G, W, L)]
        res[name] = cells
        P(f'| {name} | ' + ' | '.join(cells) + ' |')
    P('\nLoss causes (share of losses; a loss can have several):')
    cc = collections.Counter(c for x in L for c in x['causes'])
    for c, n in cc.most_common():
        e, se = boot(L, pct(lambda x, c=c: c in x['causes']))
        P(f'- {c}: {n} of {len(L)} ({100 * e:.0f}% ± {100 * se:.0f})')
    P('\nWins flipped by X more submitted gems (losses with margin < X):')
    P(', '.join(f"+{X}: {sum(1 for x in L if x['margin'] < X)}" for X in (25, 50, 100, 200, 300)))
    P('\n| map | W-L | gems us-them | deaths champ/camp/monolith | gems/capture us/them | first tribute us/them | causes |')
    P('|---|---|---|---|---|---|---|')
    by = collections.defaultdict(list)
    for x in G:
        by[x['map']].append(x)
    for mp, gs in sorted(by.items(), key=lambda kv: (sum(x['win'] for x in kv[1]) / len(kv[1]), kv[0])):
        w = sum(x['win'] for x in gs)
        f = lambda k: statistics.mean(x[k] for x in gs)
        cz = collections.Counter(c for x in gs for c in x['causes'] if c != '-')
        P(f"| {mp} | {w}-{len(gs) - w} | {f('sub'):.0f}-{f('sub_them'):.0f} | {f('d_champ'):.0f}/{f('d_camp'):.0f}/{f('d_mono'):.0f} | "
          f"{sum(x['cap'] for x in gs) / max(1, sum(x['ncap'] for x in gs)):.1f}/{sum(x['cap_them'] for x in gs) / max(1, sum(x['ncap_them'] for x in gs)):.1f} | "
          f"{f('ft'):.0f}/{f('ft_them'):.0f} | {' '.join(cz)} |")
    if out:
        json.dump(dict(rows=res, games=G), open(out, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
