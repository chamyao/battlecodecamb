"""Least squares on the regression: win rate ~ in-first-k indicators (and position weights)."""
import json, sys
import numpy as np
sys.path.insert(0, '.')
from genome.tuneb import tb
R = [json.loads(l) for l in open(sys.argv[1])]
y = np.array([r['wins'] / r['games'] for r in R])
for k in (3, 5):
    X = np.array([[1.0] + [1.0 if c in r['order'][:k] else 0.0 for c in tb.CHAMPS] for r in R])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b
    s2 = res @ res / (len(y) - X.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.pinv(X.T @ X)))
    print('in first %d:' % k, ', '.join('%s %+.3f(%.3f)' % (c, b[i + 1], se[i + 1]) for i, c in sorted(enumerate(tb.CHAMPS), key=lambda t: -b[t[0] + 1])))
print('n', len(R), 'mean', y.mean(), 'top', sorted(((r['wins'], r['order']) for r in R), reverse=True)[:10])
