"""Random-draft regression: random top-5 orders vs v28, 40 seeded games each (one per map)."""
import json, random, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
N, G, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(4242)
base = tb.base_text()
orders = [rng.sample(tb.CHAMPS, 5) for i in range(N)]
paths = [tb.save(tb.with_draft(base, o)) for o in orders]
done = sum(1 for _ in open(out)) if __import__('os').path.exists(out) else 0
with open(out, 'a') as f:
    for i in range(done, N):
        order, p = orders[i], paths[i]
        if (i - done) % 20 == 0:
            tb.precompile(paths[i:i + 20])
        r = tb.run(p, tb.BASE, games=G, seed=50000 + i)
        f.write(json.dumps(dict(order=order, wins=r['wins'], games=r['games'], susp=r['susp'])) + '\n'); f.flush()
