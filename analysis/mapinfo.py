"""Decode the map embedded in a .repl26a replay (offset 14) and identify it in a map pool."""
import glob, hashlib, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import map26a


def replay_map(path):
    d = open(path, 'rb').read()
    m = map26a.decode(d[14:], partial=True)
    raw = d[14:14 + m['end']]
    m['sha'] = hashlib.sha1(raw).hexdigest()[:10]
    return m


def pool(dirname):
    out = {}
    for f in glob.glob(os.path.join(dirname, '*.map26a')):
        out[hashlib.sha1(open(f, 'rb').read()).hexdigest()[:10]] = os.path.basename(f)[:-7]
    return out


if __name__ == '__main__':
    p = pool(sys.argv[1])
    for f in sys.argv[2:]:
        m = replay_map(f)
        print(f, m['width'], m['height'], m['sha'], p.get(m['sha'], '?'), len(m['camps']), len(m['altars']))
