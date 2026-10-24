"""Score a stand-in policy against the top-team target: play it in the sim (interp_eval, cambc-exact
bot seeds) against our five versions on one team's real maps and sides, and compare per version
with what that team did to the same versions on the ladder (data/top-teams-target.json).

Usage: python3 score_clone.py CANDIDATE.pol TEAM VERSION=OURS.pol [VERSION=OURS.pol ...]
Env: INTERP_EVAL (path to interp_eval), MAPS (map directory, default ../maps relative to it).
Prints, per version: sim vs real deaths/kills (ours), gems us/them, champion damage us/them, W-L,
and a fit error: the mean over versions and metrics of ((sim - real) / spread)^2, where spread is the
standard deviation of that metric over all of the team's real games (floored to avoid zero).
"""
import json, os, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, '..', 'data', 'top-teams-target.json')
METRICS = (('deaths', 0), ('kills', 0), ('gems', 0), ('gems', 1), ('champion_damage', 0), ('champion_damage', 1))


def run(ours, cand, maps, side):
    ev = os.environ['INTERP_EVAL']
    mdir = os.environ.get('MAPS') or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(ev))), 'maps')
    paths = [os.path.join(mdir, m + '.map26a') for m in maps]
    out = subprocess.run([ev, '--a', ours, '--b', cand, '--bot-seeds', '--games', str(2 * len(maps)), '--threads', '8', '--details'] + paths,
                         capture_output=True, text=True, check=True).stdout.splitlines()
    rows = []
    for line in out:
        g = json.loads(line)
        if 'game' not in g:
            continue
        mp = os.path.basename(g['map']).replace('.map26a', '')
        if g['a_side'] != side[mp]:
            continue
        a = 0 if g['a_side'] == 'A' else 1          # our side index in the per-team arrays
        rows.append(dict(map=mp, win=g['winner'] == a, gems=[g['gems'][a], g['gems'][1 - a]], kills=[g['kills'][a], g['kills'][1 - a]],
                         deaths=[g['deaths'][a], g['deaths'][1 - a]], champion_damage=[g['champ_damage'][a], g['champ_damage'][1 - a]]))
    return rows


def main(cand, team, *versions):
    T = json.load(open(TARGET))
    real = [g for g in T['games'] if g['team'] == team]
    side = {g['map']: g['our_side'] for g in real}
    maps = sorted(side)
    spread = {(k, i): max(statistics.pstdev([g[k][i] for g in real]), 1.0 if k != 'champion_damage' else 500.0, 0.1 * abs(statistics.mean([g[k][i] for g in real])))
              for k, i in METRICS}
    mean = lambda xs: sum(xs) / len(xs) if xs else 0
    P = print
    P(f'Candidate {os.path.basename(cand)} vs our versions on {team} maps {", ".join(maps)} (our real side).\n')
    P('| our version | W-L sim / real | our deaths sim / real | our kills sim / real | gems us sim / real | gems them sim / real | champ dmg us sim / real | champ dmg them sim / real |')
    P('|---|---|---|---|---|---|---|---|')
    errs = []
    for spec in versions:
        ver, pol = spec.split('=', 1)
        S = run(pol, cand, maps, side)
        R = [g for g in real if g['version'] == ver]
        cells = [f"{sum(g['win'] for g in S)}-{sum(not g['win'] for g in S)} / {sum(g['win'] for g in R)}-{sum(not g['win'] for g in R)}"]
        for k, i in METRICS:
            s, r = mean([g[k][i] for g in S]), mean([g[k][i] for g in R])
            errs.append(((s - r) / spread[(k, i)]) ** 2)
            cells.append(f"{s / 1000:.1f}k / {r / 1000:.1f}k" if k == 'champion_damage' else f"{s:.1f} / {r:.1f}")
        P(f'| {ver} | ' + ' | '.join(cells) + ' |')
    P(f'\nFit error (mean squared z over versions x metrics; 0 = matches the real games): {mean(errs):.2f}')


if __name__ == '__main__':
    main(*sys.argv[1:])
