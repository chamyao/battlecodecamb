"""Which per-game features predict a band win, pooled over batches (bots), for a fitness term vs the band.

Usage: python3 -I genome/intel/predictors.py ANALYSIS_DIR LABEL=FETCHDIR,EXDIR [...]
Features per game (ours minus theirs where marked d_): gold earned, captures, gem-group captures, deaths and kills,
all by round 250 / 500; our first tribute round; gems submitted by r500 (d_). For each: AUC for a win (0.5 = no signal)
and the win rate in the top vs bottom third; then a standardized logistic regression with all r500 features plus
batch dummies (the bot), so a coefficient is the feature's effect independent of which bot played.
"""
import collections, json, os, statistics, sys
import numpy as np


def auc(x, y):
    pos = [a for a, b in zip(x, y) if b]; neg = [a for a, b in zip(x, y) if not b]
    if not pos or not neg:
        return 0.5
    s = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return s / (len(pos) * len(neg))


def features(d, us, st, team):
    them = 1 - us
    F = {}
    for rd in (250, 500):
        gold = [0, 0]; deaths = [0, 0]; caps = [0, 0]; gcaps = [0, 0]
        for e in d['events']:
            if e['r'] > rd:
                break
            if e['k'] not in ('Shop', 'Sell item'):
                for x in e.get('d', []):
                    if x.get('gold', 0) > 0 and x['i'] in team:
                        gold[team[x['i']]] += x['gold']
            for x in e.get('d', []):
                if x.get('alive') == 0 and x['i'] in team and any(y.get('kills', 0) > 0 for y in e.get('d', [])):
                    deaths[team[x['i']]] += 1
        for t in (0, 1):
            for c in st[t]['lists'].get('capture', []):
                if c[0] <= rd:
                    caps[t] += 1; gcaps[t] += c[2] > 0
        F[f'd_gold_r{rd}'] = gold[us] - gold[them]
        F[f'our_deaths_r{rd}'] = deaths[us]
        F[f'their_deaths_r{rd}'] = deaths[them]
        F[f'd_captures_r{rd}'] = caps[us] - caps[them]
        F[f'd_gemcaptures_r{rd}'] = gcaps[us] - gcaps[them]
    tr = st[us]['lists'].get('tribute', []); trt = st[them]['lists'].get('tribute', [])
    F['our_first_tribute'] = min([t[0] for t in tr], default=2000)
    F['d_first_tribute'] = F['our_first_tribute'] - min([t[0] for t in trt], default=2000)
    cur = lambda t: max([v['sub'] for k, v in st[t]['curve'].items() if int(k) <= 500], default=0)
    F['d_submitted_r500'] = cur(us) - cur(them)
    return F


def main(argv):
    adir = argv[0]
    sys.path.insert(0, os.path.abspath(adir))
    import analyse
    rows = []
    for spec in argv[1:]:
        label, dirs = spec.split('=', 1); fd, ex = dirs.split(',')
        for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
            d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
            us = 0 if v['A'] == 'Master' else 1
            st = analyse.game_stats(d, (v['A'], v['B']))
            team = {c['i']: c['team'] for c in d['champions']}
            F = features(d, us, st, team)
            rows.append(dict(F=F, win=(d['outcome'] == 1) == (us == 0), batch=label, map=v['map'], opp=v['B'] if us == 0 else v['A']))
    y = [r['win'] for r in rows]
    names = list(rows[0]['F'])
    print(f'{len(rows)} games, {sum(y)} wins ({", ".join(sorted(set(r["batch"] for r in rows)))})\n')
    print('| feature | AUC for a win | win rate, top third | bottom third |')
    print('|---|---|---|---|')
    for n in names:
        x = [r['F'][n] for r in rows]
        o = sorted(range(len(x)), key=lambda i: x[i]); k = len(o) // 3
        lo = [y[i] for i in o[:k]]; hi = [y[i] for i in o[-k:]]
        print(f'| {n} | {auc(x, y):.2f} | {100 * sum(hi) / len(hi):.0f}% | {100 * sum(lo) / len(lo):.0f}% |')
    # logistic regression on r500 features + batch dummies
    use = ['d_gold_r500', 'our_deaths_r500', 'their_deaths_r500', 'd_gemcaptures_r500', 'd_first_tribute', 'd_submitted_r500']
    X = np.array([[r['F'][n] for n in use] for r in rows], float)
    mu, sd = X.mean(0), X.std(0) + 1e-9; X = (X - mu) / sd
    B = sorted(set(r['batch'] for r in rows))[1:]
    X = np.hstack([X, np.array([[r['batch'] == b for b in B] for r in rows], float), np.ones((len(rows), 1))])
    Y = np.array(y, float); w = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ w)); g = X.T @ (Y - p) - 0.01 * w
        H = -(X.T * (p * (1 - p))) @ X - 0.01 * np.eye(len(w)); w -= np.linalg.solve(H, g)
    p = 1 / (1 + np.exp(-X @ w)); H = (X.T * (p * (1 - p))) @ X + 0.01 * np.eye(len(w)); se = np.sqrt(np.diag(np.linalg.inv(H)))
    print('\nLogistic regression (standardized r500 features; batch dummies for the bot):\n')
    print('| term | coefficient | SE |')
    print('|---|---|---|')
    for n, c, s in zip(use + [f'batch={b}' for b in B] + ['intercept'], w, se):
        print(f'| {n} | {c:+.2f} | {s:.2f} |')
    # maps: win rate by map over all batches
    bm = collections.defaultdict(list)
    for r in rows:
        bm[r['map']].append(r['win'])
    always = sorted(m for m, v in bm.items() if not any(v)); never_lost = sorted(m for m, v in bm.items() if all(v))
    print(f'\nMaps lost in every game ({len(always)}): {", ".join(always)}')
    print(f'Maps won in every game ({len(never_lost)}): {", ".join(never_lost)}')


if __name__ == '__main__':
    main(sys.argv[1:])
