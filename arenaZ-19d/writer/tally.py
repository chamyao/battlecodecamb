import json, glob, re, collections
ch = {json.loads(l)['seq']: json.loads(l) for l in open('/root/z19/runs/arenaZ-19d/arena/children.jsonl')}
st = json.load(open('/root/z19/runs/arenaZ-19d/arena/state.json'))
mu = {}
for l in open('/root/z19/runs/arenaZ-19d/arena/births.jsonl'):
    d = json.loads(l); mu[d['name']] = d['mu']
# latest ratings from newest request feedback
reqs = sorted(glob.glob('/root/z19/queue/req-*.json'), key=lambda f: int(f.split('-')[-1][:-5]))
rated = {}
for f in reqs[-40:]:
    for n, m, s, g in json.load(open(f))['feedback'].get('rated', []): rated[n] = (m, g)
agg = collections.defaultdict(list)
for f in reqs:
    r = json.load(open(f)); s = r['seq']
    b = f'/root/w/d/{s}.best'
    try: kind = re.sub(r'.*/\d+\.', '', open(b).read().strip())[:-4]
    except FileNotFoundError: continue
    c = ch.get(r['child_seq'])
    if not c: continue
    nm = c.get('name'); pm = [rated.get(p, (mu.get(p), 0))[0] for p in r['parents']]
    if nm and nm in rated and pm[0]:
        for k in kind.split('_'):
            pass
        agg[kind].append(round(rated[nm][0] - pm[0], 2))
    elif nm is None: agg[kind].append(c.get('error','?')[:5])
for k, v in sorted(agg.items()): print(k, v)
