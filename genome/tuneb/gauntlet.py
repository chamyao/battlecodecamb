"""Gauntlet vs the live bot (tb.BASE) and every anchor: bot seeds /80, plus 400 seeded games vs the policy anchors
(their games vary by seed). Per-game results are kept for paired sign tests (tb.sign_test) against the base row.
python3 genome/tuneb/gauntlet.py OUT.jsonl SEED TAG=PATH ...   (TAG 'base' = the live bot itself)"""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
out, seed = sys.argv[1], int(sys.argv[2])
items = [a.split('=', 1) for a in sys.argv[3:]]
tb.precompile([p for _, p in items] + [v for v in tb.ANCHORS.values() if v.endswith('.genome')])
with open(out, 'a') as f:
    for tag, p in items:
        row = dict(tag=tag, path=p, res={})
        v = tb.run(p, tb.BASE, bot_seeds=True)
        row['live'] = v['wins']; row['susp'] = v['susp']; row['res']['live'] = v['results']
        for k, spec in tb.ANCHORS.items():
            r = tb.run(p, k, bot_seeds=True)
            row[k] = r['wins']; row['susp_' + k] = r['susp']; row['res'][k] = r['results']
            if spec.endswith('.pol'):
                r = tb.run(p, k, games=400, seed=seed)
                row[k + '_400'] = r['wins']; row['res'][k + '_400'] = r['results']
        f.write(json.dumps(row) + '\n'); f.flush()
        print(tag, json.dumps({k: v for k, v in row.items() if k not in ('res', 'path') and not k.startswith('susp_')}), flush=True)
