"""Simulator metrics for the gaps in GAPS.md: one genome against one opponent, per-game means for side A.

Usage: python3 -m genome.intel.sim_metrics GENOME OPP [--games N] [--maps GLOB ...] [--fuel-mult X]
GENOME: a .genome file (compiled with genome.build) or genome:path.so; OPP: a .genome, .policy, .pol or builtin:.
Prints win rate (draws half) and the gap metrics: gems submitted, gems lost to champions, deaths to
champions / to camps (deaths - enemy kills), gems per capture, captures, tributes, suspensions.
"""
import glob, json, os, statistics, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(ROOT, 'genome', 'build', 'genome_eval')
CACHE = os.path.join(ROOT, 'genome', 'build', 'intel')


def side(spec):
    if spec.endswith('.genome'):
        so = subprocess.run([sys.executable, '-m', 'genome.build', spec], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        return 'genome:' + so.splitlines()[-1]
    if spec.endswith('.policy'):
        os.makedirs(CACHE, exist_ok=True)
        pol = os.path.join(CACHE, os.path.basename(spec)[:-7] + '.pol')
        subprocess.run([sys.executable, '-m', 'policygen.compile', spec, pol], cwd=ROOT, check=True)
        return pol
    return spec


def run(a, b, games, maps, fuel_mult=None, threads=4):
    cmd = [EVAL, '--a', side(a), '--b', side(b), '--games', str(games), '--threads', str(threads), '--details']
    if fuel_mult:
        cmd += ['--fuel-mult', str(fuel_mult)]
    out = subprocess.run(cmd + maps, capture_output=True, text=True, check=True).stdout
    return [g for g in map(json.loads, out.splitlines()) if 'game' in g]


def metrics(G):
    a = lambda g, k: g[k][0 if g['a_side'] == 'A' else 1] if isinstance(g[k], list) else g[k]
    b = lambda g, k: g[k][1 if g['a_side'] == 'A' else 0]
    n = len(G)
    m = lambda f: sum(f(g) for g in G) / n
    win = lambda g: 1 if g['winner'] == (0 if g['a_side'] == 'A' else 1) else 0.5 if g['winner'] not in (0, 1) else 0
    return dict(
        games=n, win=m(win), gems=m(lambda g: a(g, 'gems')), gems_them=m(lambda g: b(g, 'gems')),
        lost_to_champs=m(lambda g: a(g, 'gems_lost_to_champs')),
        deaths_champ=m(lambda g: b(g, 'kills')), deaths_camp=m(lambda g: a(g, 'deaths') - b(g, 'kills')),
        captures=m(lambda g: a(g, 'captures')), captured=m(lambda g: a(g, 'gems_captured')),
        per_capture=sum(a(g, 'gems_captured') for g in G) / max(1, sum(a(g, 'captures') for g in G)),
        tributes=m(lambda g: a(g, 'tributes')), susp=m(lambda g: g['suspensions']))


def main(argv):
    args, games, maps, fm = [], 80, [], None
    i = 0
    while i < len(argv):
        if argv[i] == '--games': games = int(argv[i + 1]); i += 2
        elif argv[i] == '--fuel-mult': fm = float(argv[i + 1]); i += 2
        elif argv[i] == '--maps':
            i += 1
            while i < len(argv) and not argv[i].startswith('--'):
                maps += sorted(glob.glob(argv[i])); i += 1
        else: args.append(argv[i]); i += 1
    maps = maps or sorted(glob.glob(os.path.join(ROOT, 'maps', '*.map26a')))
    G = run(args[0], args[1], games, maps, fm)
    r = metrics(G)
    se = (r['win'] * (1 - r['win']) / r['games']) ** 0.5
    print(f"win {r['win']:.3f} ± {se:.3f} over {r['games']}; " + ', '.join(f'{k} {v:.1f}' for k, v in r.items() if k not in ('games', 'win')))


if __name__ == '__main__':
    main(sys.argv[1:])
