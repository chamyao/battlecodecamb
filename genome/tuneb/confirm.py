"""Confirm genomes vs v28: bot seeds /80 plus 2 x 400 fresh seeds. python3 genome/tuneb/confirm.py OUT.jsonl SEED1 SEED2 TAG=PATH ..."""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
out, s1, s2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
items = [a.split('=', 1) for a in sys.argv[4:]]
tb.precompile([p for _, p in items])
with open(out, 'a') as f:
    for tag, p in items:
        b = tb.run(p, tb.BASE, bot_seeds=True)
        x = tb.run(p, tb.BASE, games=400, seed=s1)
        y = tb.run(p, tb.BASE, games=400, seed=s2)
        f.write(json.dumps(dict(tag=tag, path=p, bot80=b['wins'], f1=x['rate'], f2=y['rate'],
                                susp=b['susp'], susp_base=None)) + '\n'); f.flush()
        print(tag, b['wins'], x['rate'], y['rate'], flush=True)
