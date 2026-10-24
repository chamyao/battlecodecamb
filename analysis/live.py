"""Live stream of our games: poll the platform, download and extract every finished match of ours
(ranked and unranked) as it lands, tag it with our bot version, and exit once enough new games
have arrived so the analysis session wakes up and looks at them.

Usage: python3 live.py LIVEDIR EXDIR SINCE_ISO [--min-new N] [--interval S] [--max-wait S]
- LIVEDIR: matches.json (all matches seen), replays/, summaries/, unpacked/, sides.json, versions.json.
- EXDIR: extracted JSON in EXDIR/ladder/ (analysis/extract.js), same layout as the other tools.
- Version tags: our deploy timeline parsed from docs/STRATEGY.md on origin/main ("N = name (...; ~HH:MM UTC)").
  A match gets the latest version deployed before its group was created; within 5 minutes of a deploy
  it is tagged ambiguous ("17?18"). Overrides: LIVEDIR/version_overrides.json {"18": "2026-10-24T07:27"}
  (times verified from replays, e.g. first ward or lock; no ambiguity window).
- Exits (printing the new matches) after >= N new finished matches (default 5, one group), or after
  --max-wait seconds (default 3600) with whatever arrived.
"""
import io, json, os, re, subprocess, sys, time, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_mine import cambc

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def timeline(livedir, day='2026-10-24'):
    """[(iso time, version label)] from origin/main docs/STRATEGY.md plus overrides, sorted."""
    subprocess.run(['git', '-C', REPO, 'fetch', '-q', 'origin', 'main'], capture_output=True)
    txt = subprocess.run(['git', '-C', REPO, 'show', 'origin/main:docs/STRATEGY.md'], capture_output=True, text=True).stdout
    txt = re.sub(r'\s+', ' ', txt)
    tl = {}
    for n, name, rest in re.findall(r'\b(\d+) = ([\w.\-]+) \(([^)]*)', txt):
        t = re.search(r'~(\d\d):(\d\d) UTC', rest)
        if t and int(n) >= 17:
            tl[n] = (f'{day}T{t.group(1)}:{t.group(2)}', name)
    ov = os.path.join(livedir, 'version_overrides.json')
    if os.path.exists(ov):
        for n, iso in json.load(open(ov)).items():
            tl[n] = (iso, tl.get(n, (None, n))[1] + '!')     # '!' = time verified from replays: no ambiguity window
    return sorted((iso, f'v{n}', name) for n, (iso, name) in tl.items())


def tag(created, tl):
    def mins(a, b):
        return (time.mktime(time.strptime(a[:16], '%Y-%m-%dT%H:%M')) - time.mktime(time.strptime(b[:16], '%Y-%m-%dT%H:%M'))) / 60
    cur = None
    for i, (iso, v, _) in enumerate(tl):
        if created[:16] >= iso:
            cur = i
    if cur is None:
        return 'pre-' + tl[0][1] if tl else '?'
    v = tl[cur][1]
    if mins(created, tl[cur][0]) < 5 and cur > 0 and not tl[cur][2].endswith('!'):
        return f'{tl[cur - 1][1]}?{v[1:]}'
    return v


def poll(livedir, since):
    ms = []
    for kind in ('ranked', 'unranked'):
        cur = None
        while True:
            d = json.loads(cambc('matches', 'list', '--team', 'me', '--kind', kind, '--limit', '25', '--json', *(['--cursor', cur] if cur else [])))
            ms += d['matches']
            cur = d.get('nextCursor')
            if not cur or not d['matches'] or min(m['createdAt'] for m in d['matches']) < since:
                break
    return [m for m in ms if m['createdAt'] >= since and m['status'] == 'finished']


def ingest(livedir, exdir, m, tl, sides):
    mid = m['matchId']
    for sub, cmd in (('replays', ['matches', 'download', mid, '-o']), ('summaries', ['matches', 'summary', mid, '--json', '-o'])):
        dst = os.path.join(livedir, sub, mid + ('.zip' if sub == 'replays' else '.json'))
        if not os.path.exists(dst):
            cambc(*cmd, dst)
    data = open(os.path.join(livedir, 'replays', mid + '.zip'), 'rb').read()
    if data[:2] == b'PK':
        z = zipfile.ZipFile(io.BytesIO(data))
        data = z.read([n for n in z.namelist() if n.endswith('.repl26a')][0])
    rep = os.path.join(livedir, 'unpacked', mid + '.repl26a')
    open(rep, 'wb').write(data)
    ver = 'v%d_%d_%d' % tuple(data[8:11])
    wasm = os.path.join(HERE, 'engine', ver + '.wasm')
    out = os.path.join(exdir, 'ladder', mid + '.json')
    if not os.path.exists(out):
        subprocess.run(['node', os.path.join(HERE, 'extract.js'), rep, out], env=dict(os.environ, CAMBC_WASM=wasm), check=True, capture_output=True)
    t = {x['side']: x['name'] for x in m['teams']}
    sides[f'ladder/{mid}'] = dict(A=t['a'], B=t['b'], map=m['map'], margin=None, file=mid + '.json', engine=ver,
                                  results={x['side']: x['result'] for x in m['teams']}, kind=m['kind'], created=m['createdAt'],
                                  group=m.get('groupId'), version=tag(m['createdAt'], tl))


def main(livedir, exdir, since, *opts):
    o = dict(zip(opts[::2], opts[1::2]))
    min_new, interval, max_wait = int(o.get('--min-new', 5)), int(o.get('--interval', 180)), int(o.get('--max-wait', 3600))
    for sub in ('replays', 'summaries', 'unpacked'):
        os.makedirs(os.path.join(livedir, sub), exist_ok=True)
    os.makedirs(os.path.join(exdir, 'ladder'), exist_ok=True)
    sp = os.path.join(livedir, 'sides.json')
    sides = json.load(open(sp)) if os.path.exists(sp) else {}
    new, t0 = [], time.time()
    while True:
        tl = timeline(livedir)
        json.dump(tl, open(os.path.join(livedir, 'versions.json'), 'w'), indent=1)
        for m in sorted(poll(livedir, since), key=lambda m: m['createdAt']):
            key = f"ladder/{m['matchId']}"
            if key in sides and sides[key].get('version') == tag(m['createdAt'], tl):
                continue
            fresh = key not in sides
            try:
                ingest(livedir, exdir, m, tl, sides)
            except Exception as e:                      # keep streaming; report the failure
                print(f"ingest failed {m['matchId']}: {e}", file=sys.stderr)
                continue
            if fresh:
                new.append(sides[key])
        json.dump(sides, open(sp, 'w'), indent=1)
        json.dump(dict(ladder=[], matches=[]), open(os.path.join(livedir, 'matches.json'), 'w'))
        if len(new) >= min_new or (new and time.time() - t0 > max_wait):
            break
        time.sleep(interval)
    for s in new:
        us = 'a' if s['A'] == 'Master' else 'b'
        opp = s['B'] if us == 'a' else s['A']
        print(f"{s['created'][11:16]} {s['kind']:8} {s['version']:8} {s['results'][us]:4} vs {opp} on {s['map']}")


if __name__ == '__main__':
    main(*sys.argv[1:])
