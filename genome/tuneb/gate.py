"""Gate table from a gauntlet file: python3 genome/tuneb/gate.py GAUNTLET.jsonl
Bar (Arena B, Oct 25): >= 43/80 vs the live bot; an anchor drop blocks only if the paired sign test on the diverging
(map, side) games gives p < 0.1 (01boss-battle excluded); no worse than the base vs farmer and rushbank."""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
R = [json.loads(l) for l in open(sys.argv[1])]
BAR = float(sys.argv[2]) if len(sys.argv) > 2 else 43  # 41 for the A8 family (sim undershoots real by 5-8/80)
base = [r for r in R if r['tag'] == 'base'][0]
for r in R:
    if r is base:
        continue
    blocks, cells = [], []
    for k in r['res']:
        if k == 'live':
            continue
        maps = tb.MAPS if not k.endswith('_400') else tb.MAPS
        up, dn, p = tb.sign_test(r['res'][k], base['res'][k], maps)
        cells.append('%s %+d/%+d p%.2f' % (k, up, -dn, p))
        if dn > up and p < 0.1:
            blocks.append(k)
    band = all(r[k] >= base[k] for k in ('farmer', 'rushbank'))
    ok = r['live'] >= BAR and not blocks and band
    print('%s: live %.0f/80, susp %.2f (base %.2f), farmer %.0f (%.0f), rushbank %.0f (%.0f), blocks %s -> %s' % (
        r['tag'], r['live'], r['susp'], base['susp'], r['farmer'], base['farmer'], r['rushbank'], base['rushbank'],
        blocks or '-', 'PASS' if ok else 'fail'))
    print('   ' + '; '.join(cells))
