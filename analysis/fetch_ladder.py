"""Fetch recent finished ranked matches among the ladder's top teams (needs `cambc login`).

Usage: python3 fetch_ladder.py OUTDIR [top_n=16] [per_team=60]
Writes OUTDIR/matches.json (metadata) and OUTDIR/replays/<matchId>.zip.
"""
import json, os, subprocess, sys, time


def cambc(*args, tries=20):
    for k in range(tries):
        time.sleep(1.5)  # stay under the public API rate limit
        p = subprocess.run(['cambc', *args], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        if '429' in p.stderr or 'busy' in p.stderr:
            time.sleep(min(60, 3 * (k + 1)))
            continue
        raise RuntimeError(f"cambc {' '.join(args)}: {p.stderr.strip()}")
    raise RuntimeError('rate limited: ' + ' '.join(args))


def ladder(n):
    teams = []
    for line in cambc('ladder').splitlines()[1:]:
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[0].isdigit():
            teams.append(dict(rank=int(parts[0]), rating=float(parts[1]), id=parts[2], name=parts[3]))
    return teams[:n]


def main(out, top_n=16, per_team=60):
    os.makedirs(os.path.join(out, 'replays'), exist_ok=True)
    top = ladder(top_n)
    ids = {t['id'] for t in top}
    matches = {}
    for t in top:
        cursor, got = None, 0
        while got < per_team:
            args = ['matches', 'list', '--team', t['id'], '--kind', 'ranked', '--limit', '25', '--json']
            if cursor:
                args += ['--cursor', cursor]
            d = json.loads(cambc(*args))
            for m in d['matches']:
                if m['status'] != 'finished' or not all(x['teamId'] in ids for x in m['teams']):
                    continue
                if m['matchId'] not in matches:
                    matches[m['matchId']] = m
                got += 1
            cursor = d.get('nextCursor')
            if not cursor or not d['matches']:
                break
        print(t['rank'], t['name'], 'matches so far', len(matches), file=sys.stderr, flush=True)
        json.dump(dict(ladder=top, matches=list(matches.values())), open(os.path.join(out, 'matches.json'), 'w'), indent=1)
    for mid in matches:
        dst = os.path.join(out, 'replays', mid + '.zip')
        if not os.path.exists(dst):
            cambc('matches', 'download', mid, '-o', dst)
            print('got', mid, file=sys.stderr, flush=True)
    print('downloaded', len(matches), file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1], *(int(x) for x in sys.argv[2:]))
