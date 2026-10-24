"""Ladder gate part (a) in the simulator (genome/SPEND.md): candidate vs the live bot over 800 fresh
games (two seeds x 400, all 40 maps x both sides x 5), and vs each anchor over 400, next to the live
bot's own rate on the same games (bar: >= 53.5%, no drop > 3 points). Also vs the seed and suspensions.

Usage: python3 -m genome.arenab.sim_gate CAND.genome [CAND2.genome ...] [--seed0 S] [--ref POLICY] [--bot-seeds]
--bot-seeds plays deploy seeds (the bots as cambc runs them): 80 distinct games per pairing, any --seed.
"""
import argparse, glob, os, sys
import json, subprocess
from genome.intel import sim_metrics
from genome.intel.sim_metrics import metrics, run as _run

BOT_SEEDS = False


def run(a, b, games, maps, seed=None):
    """sim_metrics.run, or with --bot-seeds every bot plays its deploy seed: the 80 games of
    40 maps x 2 sides are then the whole (deterministic) distribution, as in real cambc."""
    if not BOT_SEEDS:
        return _run(a, b, games, maps, seed=seed)
    cmd = [sim_metrics.EVAL, '--a', sim_metrics.side(a), '--b', sim_metrics.side(b), '--games', '80',
           '--threads', '4', '--details', '--bot-seeds']
    out = subprocess.run(cmd + maps, capture_output=True, text=True, check=True).stdout
    return [g for g in map(json.loads, out.splitlines()) if 'game' in g]

LIVE = 'policies/candidates/style-gconv1.policy'
ANCHORS = {'v7': 'policies/v7.policy', 'tune-v20-L1': 'policies/candidates/tune-v20-L1.policy',
           'rall2-ca4-lean-g': 'policies/candidates/rall2-ca4-lean-g.policy',
           'opp-tune5-metadraft': 'policies/opp-tune5-metadraft.policy'}
SEED = 'genome/seeds/v23.genome'


def wr(G):
    return metrics(G)['win']


def susp(G):
    return metrics(G)['susp']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cands', nargs='+')
    ap.add_argument('--seed0', type=int, default=94000)
    ap.add_argument('--ref', default=LIVE)
    ap.add_argument('--bot-seeds', action='store_true', help='deploy seeds: 80 deterministic games per pairing')
    a = ap.parse_args()
    global BOT_SEEDS
    BOT_SEEDS = a.bot_seeds
    maps = sorted(glob.glob('maps/*.map26a'))
    base = {}
    for k, (name, path) in enumerate(ANCHORS.items()):
        base[name] = wr(run(a.ref, path, 400, maps, seed=a.seed0 + 10 + k))
    for c in a.cands:
        G1 = run(c, a.ref, 400, maps, seed=a.seed0 + 1)
        G2 = run(c, a.ref, 400, maps, seed=a.seed0 + 2)
        live = (wr(G1) + wr(G2)) / 2
        drops = {}
        for k, (name, path) in enumerate(ANCHORS.items()):
            drops[name] = wr(run(c, path, 400, maps, seed=a.seed0 + 10 + k)) - base[name]
        vs_seed = wr(run(c, SEED, 400, maps, seed=a.seed0 + 3))
        ok = live >= 0.535 and min(drops.values()) >= -0.03
        print(f"{os.path.basename(c)}: vs live {live:.3f} over {80 if BOT_SEEDS else 800} ({wr(G1):.3f}/{wr(G2):.3f}), vs seed {vs_seed:.3f}, "
              f"susp/game {susp(G1 + G2):.1f}; anchors " +
              ', '.join(f"{n} {base[n] + d:.3f} ({d * 100:+.1f})" for n, d in drops.items()) +
              f" -> {'PASS' if ok else 'FAIL'}", flush=True)


if __name__ == '__main__':
    sys.exit(main())
