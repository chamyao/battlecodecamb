"""Gauntlet: bot seeds /80 vs every anchor, plus 400 seeded games vs the policy anchors (their games vary by seed).
python3 genome/tuneb/gauntlet.py OUT.jsonl SEED TAG=PATH ..."""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
out, seed = sys.argv[1], int(sys.argv[2])
items = [a.split('=', 1) for a in sys.argv[3:]]
tb.precompile([p for _, p in items] + [tb.ANCHORS[k] for k in tb.ANCHORS if k.endswith('.genome') or tb.ANCHORS[k].endswith('.genome')])
with open(out, 'a') as f:
    for tag, p in items:
        row = dict(tag=tag, path=p)
        v = tb.run(p, tb.BASE, bot_seeds=True)
        row['v28'] = v['wins']; row['susp'] = v['susp']
        for k, spec in tb.ANCHORS.items():
            r = tb.run(p, k, bot_seeds=True)
            row[k] = r['wins']
            row['susp_' + k] = r['susp']
            if spec.endswith('.pol'):
                row[k + '_400'] = tb.run(p, k, games=400, seed=seed)['wins']
        f.write(json.dumps(row) + '\n'); f.flush()
        print(json.dumps({k: v for k, v in row.items() if not k.startswith('susp_') and k != 'path'}), flush=True)
