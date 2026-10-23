"""Fit win ~ champion inclusion (+ pick-count interactions) on random-draft games."""
import itertools
import json
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression

NAMES = ["ryth", "vesper_vale", "vendetta", "cassi_issac", "stellar", "prism", "marcella", "willow",
         "ren", "varg", "tavi", "heart_of_ruin"]
TYPE2DRAFT = {0: 0, 1: 1, 2: 2, 3: 3, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11}

rows = []
for line in open(sys.argv[1]):
    try:
        d = json.loads(line)
    except ValueError:
        continue
    if "game" not in d:
        continue
    a_team = 0 if d["a_side"] == "A" else 1
    mine, theirs = set(), 0
    for c in d["champs"].split(","):
        t, ty = map(int, c.split(":"))
        if t == a_team:
            mine.add(TYPE2DRAFT[ty])
        else:
            theirs += 1
    rows.append((mine, theirs, d["map"], int(d["winner"] == a_team)))
print(len(rows), "games, win rate", np.mean([r[3] for r in rows]))
ks = sorted({r[1] for r in rows})
maps = sorted({r[2] for r in rows})
X, y = [], []
for mine, k, m, w in rows:
    f = [1.0 if i in mine else 0.0 for i in range(12)]
    f += [(1.0 if i in mine else 0.0) * (k - 4) for i in range(12)]
    f += [1.0 if m == mm else 0.0 for mm in maps]
    X.append(f)
    y.append(w)
X, y = np.array(X), np.array(y)
clf = LogisticRegression(C=1.0, max_iter=2000).fit(X, y)
main, inter = clf.coef_[0][:12], clf.coef_[0][12:24]
for k in ks:
    print(f"pick count {k}: n={sum(r[1] == k for r in rows)}")
print(f"{'champ':15s} {'main':>7s} {'xk':>7s} | raw win% with / without")
for i in np.argsort(-main):
    w = [r[3] for r in rows if i in r[0]]
    wo = [r[3] for r in rows if i not in r[0]]
    print(f"{NAMES[i]:15s} {main[i]:7.3f} {inter[i]:7.3f} | {np.mean(w):.3f} {np.mean(wo):.3f}")
for k in ks:
    eff = main + inter * (k - 4)
    best = sorted(itertools.combinations(range(12), k), key=lambda s: -sum(eff[list(s)]))[:5]
    print(f"k={k} best sets:", [[NAMES[i] for i in s] for s in best])
