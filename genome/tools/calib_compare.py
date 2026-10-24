"""Real vs sim fuel per probe gene (inclusive, minus p_empty), from genome/tools/prof_pair.sh output.

    python3 genome/tools/calib_compare.py calib2 00ambush 01big-world 00lanes [--json out.json]
"""
import json, re, sys


def rd(path):
    rows = {}
    for l in open(path, errors="replace"):
        m = re.search(r'@@GENE r(\d+) (\w+) calls (\d+) fuel (-?\d+)', l)
        if m and int(m.group(3)) > 0:
            rows[m.group(2)] = (int(m.group(4)) / int(m.group(3)), int(m.group(3)))  # latest cumulative
    b = rows['p_empty'][0]
    return {k[2:]: (v - b, n) for k, (v, n) in rows.items() if k.startswith('p_')}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    name, maps = args[0], args[1:]
    out = {}
    for M in maps:
        d = f'/tmp/claude-0/prof/{name}-{M}'
        r, s = rd(f'{d}/real.txt'), rd(f'{d}/sim.txt')
        out[M] = {k: (r[k][0], s.get(k, (0, 0))[0]) for k in r}
        print(M)
        for k in r:
            sv = s.get(k, (0, 0))[0]
            print(f"  {k:16s} real {r[k][0]:8.0f} sim {sv:8.0f} ratio {sv / r[k][0] if r[k][0] else 0:5.2f}  (calls {r[k][1]})")
    if '--json' in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'))
