"""Queue a band batch from a plan file and fetch it (needs `cambc login`; spends the team's shared match-group quota).

Usage:
  python3 -I genome/intel/run_batch.py plan  OUT.json [--like batches/b1_plan.json] [--teams 10]   # write a plan
  python3 -I genome/intel/run_batch.py queue PLAN.json      # queue every group in the plan without a groupId
A new plan picks teams rated +55..+145 above us (one near each 10-point step, 700+ matches) and spreads all 40
maps (plus 10 repeats) with sides alternating. --like copies another plan's teams, maps and sides, so the games
pair one to one (same opponent, map and side) for a before/after comparison. Check `cambc match-groups quota`
first and stay within half of what is left.
"""
import json, random, subprocess, sys, time


def cambc(*a):
    for k in range(6):
        p = subprocess.run(['cambc', *a], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout
        if '429' in p.stderr or 'busy' in p.stderr:
            time.sleep(5 * (k + 1))
            continue
        raise RuntimeError(p.stderr.strip())
    raise RuntimeError('rate limited')


def plan(out, like=None, n=10):
    if like:
        P = [dict(team=p['team'], id=p['id'], maps=p['maps'], sides=p['sides']) for p in json.load(open(like))]
    else:
        T = []
        for page in range(1, 17):
            T += json.loads(cambc('ladder', '--page', str(page), '--limit', '25', '--json'))['teams']
            time.sleep(1)
        us = next(t for t in T if t['name'] == 'Master')['rating']
        band = [t for t in T if 50 <= t['rating'] - us <= 150 and not t['isDev'] and t['matches'] >= 700]
        pick = []
        for off in range(55, 55 + 10 * n, 10):
            pick.append(min((t for t in band if t not in pick), key=lambda t: abs(t['rating'] - us - off)))
        maps = [m['name'] for m in json.loads(cambc('match-groups', 'quota', '--json'))['maps']]
        rnd = random.Random(int(time.time()))
        L = maps[:]; rnd.shuffle(L); L += rnd.sample(maps, 10)
        P = [dict(team=t['name'], id=t['teamId'], rating_gap=round(t['rating'] - us), maps=L[5 * i:5 * i + 5],
                  sides=['a' if (i + j) % 2 == 0 else 'b' for j in range(5)]) for i, t in enumerate(pick)]
    json.dump(P, open(out, 'w'), indent=1)
    for p in P:
        print(p['team'], p['maps'], p['sides'])


def queue(path):
    P = json.load(open(path))
    for p in P:
        if 'group' in p:
            continue
        p['group'] = json.loads(cambc('match-groups', 'create', p['id'], '--maps', ','.join(p['maps']), '--sides', ','.join(p['sides']), '--json'))
        json.dump(P, open(path, 'w'), indent=1)
        print(p['team'], p['group']['groupId'])
        time.sleep(2)
    print(' '.join(p['group']['groupId'] for p in P))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'plan':
        like = a[a.index('--like') + 1] if '--like' in a else None
        n = int(a[a.index('--teams') + 1]) if '--teams' in a else 10
        plan(a[1], like, n)
    elif a[0] == 'queue':
        queue(a[1])
