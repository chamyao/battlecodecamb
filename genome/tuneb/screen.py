"""Screen variants vs v28: python3 genome/tuneb/screen.py SPEC.json OUT.jsonl GAMES SEED [--bot-seeds] [--opp NAME]
SPEC: list of {tag, order?: [...], edits?: [[old, new], ...]} applied to the v28 text."""
import json, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
spec, out, games, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
bs = '--bot-seeds' in sys.argv
opp = sys.argv[sys.argv.index('--opp') + 1] if '--opp' in sys.argv else tb.BASE
done = set()
try:
    done = {json.loads(l)['tag'] for l in open(out)}
except FileNotFoundError:
    pass
todo = []
for v in json.load(open(spec)):
    if v['tag'] in done:
        continue
    t = tb.base_text()
    if v.get('order'):
        t = tb.with_draft(t, v['order'])
    if v.get('edits'):
        t = tb.edit(t, v['edits'])
    todo.append((v, tb.save(t)))
tb.precompile([p for _, p in todo])
with open(out, 'a') as f:
    for v, p in todo:
        r = tb.run(p, opp, games=games, seed=seed, bot_seeds=bs)
        r.pop('results')
        f.write(json.dumps(dict(tag=v['tag'], path=p, **r)) + '\n'); f.flush()
