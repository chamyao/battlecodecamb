"""Report on the live stream (live.py): per our version and match kind, the TOP_TEAMS metrics
(top_compare) and our low-HP survival (low_hp), from LIVEDIR/sides.json.

Usage: python3 live_report.py LIVEDIR EXDIR [--kind ranked|unranked] [--versions v21,v22]
"""
import collections, io, json, os, sys, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import top_compare, low_hp


def main(livedir, exdir, *opts):
    o = dict(zip(opts[::2], opts[1::2]))
    sides = json.load(open(os.path.join(livedir, 'sides.json')))
    want = set(o['--versions'].split(',')) if '--versions' in o else None
    groups = collections.defaultdict(dict)
    for k, v in sides.items():
        if '?' in v['version'] or (want and v['version'] not in want) or ('--kind' in o and v['kind'] != o['--kind']):
            continue
        groups[f"{v['version']}-{v['kind']}"][k] = v
    specs = []
    for label, sd in sorted(groups.items(), key=lambda kv: (int(kv[0].split('-')[0][1:]) if kv[0][1:].split('-')[0].isdigit() else 0, kv[0])):
        d = os.path.join(livedir, 'by', label)
        os.makedirs(d, exist_ok=True)
        json.dump(sd, open(os.path.join(d, 'sides.json'), 'w'))
        if not os.path.exists(os.path.join(d, 'summaries')):
            os.symlink(os.path.join(os.path.abspath(livedir), 'summaries'), os.path.join(d, 'summaries'))
        specs.append(f'{label}={exdir},{d}')
    top_compare.main(*specs)
    print('\nOur champions after dropping below half HP with an enemy within 5 (died within 15 rounds):\n')
    for s in specs:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            low_hp.main('*', s)
        print(f"- {s.split('=')[0]}: " + buf.getvalue().strip().splitlines()[-1].split(': ', 1)[1])


if __name__ == '__main__':
    main(*sys.argv[1:])
