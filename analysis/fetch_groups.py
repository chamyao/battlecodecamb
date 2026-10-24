"""Fetch match groups (e.g. unranked groups vs chosen opponents) for analysis (needs `cambc login`).

Usage: python3 fetch_groups.py OUTDIR GROUP_ID [GROUP_ID ...]
Writes OUTDIR/matches.json (same shape as fetch_mine.py), replays/<id>.zip, summaries/<id>.json.
Only finished matches are fetched; re-run to pick up the rest.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_mine import cambc


def main(out, *groups):
    for sub in ('replays', 'summaries'):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
    done, pending = [], 0
    for g in groups:
        d = json.loads(cambc('match-groups', 'show', g, '--json'))
        for m in d['matches']:
            if m['status'] == 'finished':
                done.append(m)
            else:
                pending += 1
    json.dump(dict(ladder=[], matches=done), open(os.path.join(out, 'matches.json'), 'w'), indent=1)
    for m in done:
        mid = m['matchId']
        for sub, cmd in (('replays', ['matches', 'download', mid, '-o']), ('summaries', ['matches', 'summary', mid, '--json', '-o'])):
            dst = os.path.join(out, sub, mid + ('.zip' if sub == 'replays' else '.json'))
            if not os.path.exists(dst):
                cambc(*cmd, dst)
    print(f'{len(done)} finished, {pending} pending', file=sys.stderr)


if __name__ == '__main__':
    main(*sys.argv[1:])
