"""Turn fetch_ladder.py output into run inputs: unpack replays, pick the engine per game,
and write a sides file in the format analyse.py reads (key 'ladder/<matchId>').

Usage: python3 ladder_prep.py LADDERDIR EXDIR  -> prints '<replay> <out.json> <wasm>' lines
"""
import io, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main(ladder, exdir):
    meta = json.load(open(os.path.join(ladder, 'matches.json')))
    os.makedirs(os.path.join(exdir, 'ladder'), exist_ok=True)
    os.makedirs(os.path.join(ladder, 'unpacked'), exist_ok=True)
    sides = {}
    for m in meta['matches']:
        mid = m['matchId']
        src = os.path.join(ladder, 'replays', mid + '.zip')
        if not os.path.exists(src):
            continue
        data = open(src, 'rb').read()
        if data[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(data))
            name = [n for n in z.namelist() if n.endswith('.repl26a')][0]
            data = z.read(name)
        rep = os.path.join(ladder, 'unpacked', mid + '.repl26a')
        open(rep, 'wb').write(data)
        ver = 'v%d_%d_%d' % tuple(data[8:11])
        wasm = os.path.join(HERE, 'engine', ver + '.wasm')
        if not os.path.exists(wasm):
            print(f'skip {mid}: engine {ver} not available', file=sys.stderr)
            continue
        t = {x['side']: x['name'] for x in m['teams']}
        sides[f'ladder/{mid}'] = dict(A=t['a'], B=t['b'], map=m['map'], margin=None, file=mid + '.json',
                                      engine=ver, results={x['side']: x['result'] for x in m['teams']})
        print(rep, os.path.join(exdir, 'ladder', mid + '.json'), wasm)
    json.dump(sides, open(os.path.join(ladder, 'sides.json'), 'w'), indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:3])
