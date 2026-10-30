"""Dump every death of one of our champions to an enemy champion, from extract.js output (engine 2.0.0).

Usage: python3 -I genome/intel/tools/deaths.py ANALYSIS_DIR OUT.json LABEL:FETCHDIR:EXDIR[:losses] ...
  ':losses' keeps only the games we lost.

A death is a round where our champion goes alive -> dead. The killer is the enemy champion whose
kill count rises in that round; a death with no such enemy (a camp or monolith) is skipped.
Positions are per round (end of round), so "3/10 rounds before" means the round rows r-3 / r-10.
on_camp_tile: standing on a camp spawn tile (where captures happen); near_camp: within 2 of one.
approach (5 rounds before death): chasing = we closed on the killer and moved more than it did;
caught = the distance shrank mostly by the killer's movement; apart = the distance did not shrink.
"""
import json, math, os, sys

CH = ['Ryth', 'Vesper Vale', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart of Ruin']


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def rows(an, label, fd, ex, losses_only):
    sys.path.insert(0, an)
    import mapinfo
    out = []
    for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
        p = os.path.join(ex, 'ladder', v['file'])
        if not os.path.exists(p):
            continue
        us = 0 if v['A'] == 'Master' else 1
        res = v['results']['a' if us == 0 else 'b']
        if losses_only and res != 'loss':
            continue
        d = json.load(open(p))
        m = mapinfo.replay_map(d['file'])
        team = {c['i']: c['team'] for c in d['champions']}
        ctype = {c['i']: c['type'] for c in d['champions']}
        R = d['rounds']
        # spawn of each team: where its champions stand in the first round row
        first = R[0][3]
        spawn = {}
        for t in (0, 1):
            ps = [(c[4], c[5]) for i, c in enumerate(first) if team[i] == t and c[4] >= 0]
            spawn[t] = (sum(x for x, _ in ps) / len(ps), sum(y for _, y in ps) / len(ps))
        camp_tiles = {(c['x'], c['y']) for c in d['camps']}  # camp spawn tiles = where captures happen
        opp = v['B'] if us == 0 else v['A']
        for t in range(1, len(R)):
            a, b = R[t - 1][3], R[t][3]
            for i, (ca, cb) in enumerate(zip(a, b)):
                if team[i] != us or not (ca[2] == 1 and cb[2] == 0):
                    continue
                killers = [j for j in range(len(b)) if team[j] != us and b[j][3] > a[j][3]]
                if not killers:
                    continue  # camp or monolith death
                k = killers[0]
                pos = (ca[4], ca[5])  # last position alive
                kpos = (b[k][4], b[k][5]) if b[k][4] >= 0 else (a[k][4], a[k][5])

                def frac(dt):
                    if t - 1 - dt < 0:
                        return None
                    c = R[t - 1 - dt][3][i]
                    return round(c[6] / c[7], 2) if c[2] and c[7] else None
                near = lambda tm: sum(1 for j, c in enumerate(a) if team[j] == tm and j != i and c[2] and c[4] >= 0 and dist(pos, (c[4], c[5])) <= 6)
                # chasing: did we get closer to the killer over the 5 rounds before death?
                chase = None
                if t - 6 >= 0:
                    c0, k0 = R[t - 6][3][i], R[t - 6][3][k]
                    if c0[2] and k0[2] and c0[4] >= 0 and k0[4] >= 0:
                        moved = dist((c0[4], c0[5]), pos)
                        closer = dist((c0[4], c0[5]), (k0[4], k0[5])) - dist(pos, (k0[4], k0[5]))
                        k_moved = dist((k0[4], k0[5]), kpos)
                        chase = 'chasing' if moved > k_moved and closer > 0 else 'caught' if closer > 0 else 'apart'
                out.append(dict(
                    set=label, match=v['file'][:-5], map=v['map'], side='a' if us == 0 else 'b', result=res, opponent=opp,
                    round=R[t][0], champion=CH[ctype[i]], killer=CH[ctype[k]],
                    hp_frac_3=frac(3), hp_frac_10=frac(10), gems=ca[1],
                    enemies_within6=near(1 - us), allies_within6=near(us),
                    dist_own_spawn=round(dist(pos, spawn[us]), 1), dist_enemy_spawn=round(dist(pos, spawn[1 - us]), 1),
                    in_bush=pos in m['bushes'], on_camp_tile=pos in camp_tiles,
                    near_camp=any(dist(pos, c) <= 2 for c in camp_tiles), approach=chase))
    return out


def main(an, out, *specs):
    allrows = []
    for s in specs:
        parts = s.split(':')
        allrows += rows(an, parts[0], parts[1], parts[2], len(parts) > 3 and parts[3] == 'losses')
    json.dump(allrows, open(out, 'w'), indent=0)
    print(len(allrows), 'deaths to champions')


if __name__ == '__main__':
    main(*sys.argv[1:])
