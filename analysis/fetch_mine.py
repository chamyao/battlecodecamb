"""Fetch our own finished ranked matches since a time (needs `cambc login`).

Usage: python3 fetch_mine.py OUTDIR SINCE_ISO   e.g. 2026-10-23T17:05
Writes OUTDIR/matches.json, OUTDIR/replays/<id>.zip, OUTDIR/summaries/<id>.json (official
CAMSTAT summary as JSON). Re-running only fetches what is missing.
"""
import json, os, subprocess, sys, time


def cambc(*args, tries=20):
    for k in range(tries):
        time.sleep(1.5)
        p = subprocess.run(['cambc', *args], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        if any(x in p.stderr for x in ('429', '503', 'busy', 'retry', 'unavailable')):
            time.sleep(min(60, 3 * (k + 1)))
            continue
        raise RuntimeError(p.stderr.strip())
    raise RuntimeError('rate limited')


def main(out, since):
    for sub in ('replays', 'summaries'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    ms, cur = [], None
    while True:
        args = ['matches', 'list', '--team', 'me', '--kind', 'ranked', '--limit', '25', '--json'] + (['--cursor', cur] if cur else [])
        d = json.loads(cambc(*args))
        ms += d['matches']
        cur = d.get('nextCursor')
        if not cur or not d['matches'] or min(m['createdAt'] for m in d['matches']) < since:
            break
    done = [m for m in ms if m['createdAt'] >= since and m['status'] == 'finished']
    json.dump(dict(ladder=[], matches=done), open(os.path.join(out, 'matches.json'), 'w'), indent=1)
    for m in done:
        mid = m['matchId']
        for sub, cmd in (('replays', ['matches', 'download', mid, '-o']), ('summaries', ['matches', 'summary', mid, '--json', '-o'])):
            dst = os.path.join(out, sub, mid + ('.zip' if sub == 'replays' else '.json'))
            if not os.path.exists(dst):
                cambc(*cmd, dst)
    print(len(done), 'finished matches since', since, file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:3])
