"""Round-robin league: every policy plays every other on all maps, then one Bradley-Terry rating each.

Ranks by strength against the whole pool instead of head to head against one bot, so a policy that
only exploits the live bot does not rank above one that beats everything.

Usage: python3 tools/league.py [--games N] [--seed S] [--bot-seeds] [--threads T] [--out DIR] POLICY...
  POLICY is a .policy (compiled on the fly) or .pol file, or builtin:starter. Name = file stem.
  --games: games per pair (default 160 = 40 maps x 2 sides x 2 seeds); --bot-seeds plays the 80
  cambc-exact games per pair instead. Pair results are cached in OUT/pairs/ by policy content hash,
  so adding a policy only plays its new pairs.
Prints ratings (Elo scale, pool mean 1500) with 90% bootstrap intervals, mean score, and worst matchup.
"""
import argparse, hashlib, itertools, json, math, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL = os.path.join(ROOT, 'build', 'interp_eval')


def load(spec, out):
    if spec.startswith('builtin:'):
        return spec.split(':', 1)[1], spec, spec
    name = os.path.splitext(os.path.basename(spec))[0]
    if spec.endswith('.policy'):
        pol = os.path.join(out, 'pol', name + '.pol')
        os.makedirs(os.path.dirname(pol), exist_ok=True)
        subprocess.run([sys.executable, '-m', 'policygen.compile', spec, pol], cwd=ROOT, check=True)
        spec = pol
    return name, spec, hashlib.sha256(open(spec, 'rb').read()).hexdigest()[:16]


def play(a, b, args, maps):
    """Wins of a over b (draws count half) from a cached or fresh interp_eval run."""
    key = f"{a[2]}_{b[2]}_{'bot' if args.bot_seeds else f'{args.games}s{args.seed}'}.json"
    path = os.path.join(args.out, 'pairs', key)
    if os.path.exists(path):
        return json.load(open(path))
    cmd = [EVAL, '--a', a[1], '--b', b[1], '--threads', str(args.threads), '--seed', str(args.seed)]
    cmd += ['--bot-seeds', '--games', str(2 * len(maps))] if args.bot_seeds else ['--games', str(args.games)]
    r = json.loads(subprocess.run(cmd + maps, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
    res = dict(a=a[0], b=b[0], games=r['games'], a_wins=r['a_wins'], crashes=r['crashes'])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(res, open(path, 'w'))
    return res


def bradley_terry(n, wins, games, iters=500):
    """MM fit of strengths p_i with P(i beats j) = p_i / (p_i + p_j); returns Elo-scale ratings, mean 1500."""
    p = [1.0] * n
    for _ in range(iters):
        q = []
        for i in range(n):
            w = sum(wins[i][j] for j in range(n)) + 0.5  # small prior keeps unbeaten/winless bots finite
            d = sum(games[i][j] / (p[i] + p[j]) for j in range(n) if j != i) + 1.0 / (p[i] + 1.0)
            q.append(w / d)
        g = math.exp(sum(math.log(x) for x in q) / n)
        p = [x / g for x in q]
    r = [400 * math.log10(x) for x in p]
    m = sum(r) / n
    return [x - m + 1500 for x in r]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=160)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--bot-seeds', action='store_true')
    ap.add_argument('--threads', type=int, default=os.cpu_count())
    ap.add_argument('--out', default=os.path.join(ROOT, 'league'))
    ap.add_argument('--boot', type=int, default=200)
    ap.add_argument('policies', nargs='+')
    args = ap.parse_args()
    maps = sorted(os.path.join(ROOT, 'maps', m) for m in os.listdir(os.path.join(ROOT, 'maps')) if m.endswith('.map26a'))
    bots = [load(s, args.out) for s in args.policies]
    n = len(bots)
    pairs = list(itertools.combinations(range(n), 2))
    with ThreadPoolExecutor(1) as ex:  # interp_eval already uses every thread
        results = list(ex.map(lambda ij: play(bots[ij[0]], bots[ij[1]], args, maps), pairs))
    wins = [[0.0] * n for _ in range(n)]
    games = [[0] * n for _ in range(n)]
    for (i, j), r in zip(pairs, results):
        wins[i][j], wins[j][i] = r['a_wins'], r['games'] - r['a_wins']
        games[i][j] = games[j][i] = r['games']
        if r['crashes']:
            print(f"warning: {r['crashes']} crashes in {r['a']} vs {r['b']}", file=sys.stderr)
    rating = bradley_terry(n, wins, games)
    rng = random.Random(0)
    boots = []
    for _ in range(args.boot):
        bw = [[0.0] * n for _ in range(n)]
        for i, j in pairs:
            g = games[i][j]
            k = sum(rng.random() < wins[i][j] / g for _ in range(g))
            bw[i][j], bw[j][i] = k, g - k
        boots.append(bradley_terry(n, bw, games, iters=200))
    print(f"{'policy':28s} {'rating':>6s} {'90% interval':>13s} {'score':>6s}  worst matchup")
    for i in sorted(range(n), key=lambda i: -rating[i]):
        bs = sorted(b[i] for b in boots)
        lo, hi = bs[int(0.05 * len(bs))], bs[int(0.95 * len(bs)) - 1]
        score = sum(wins[i]) / sum(games[i])
        worst = min((j for j in range(n) if j != i), key=lambda j: wins[i][j] / games[i][j])
        print(f"{bots[i][0]:28s} {rating[i]:6.0f} {lo:6.0f}-{hi:<6.0f} {score:6.1%}  "
              f"{bots[worst][0]} {wins[i][worst] / games[i][worst]:.0%}")


if __name__ == '__main__':
    main()
