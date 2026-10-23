"""Why does our bot (team "Master") lose? Per-game diagnostics from extracted replays.

Usage: python3 loss_analysis.py EXDIR SIDES.json [TEAM]
Deaths are attributed to the actor of the step in which the champion died (a camp or an
enemy champion). "Recall under fire" = a recall started within 8 rounds before a death to a
camp. "Stuck" = alive, off spawn, same tile for >= 15 rounds with no attack/cast/tribute.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapinfo
from analyse import CH, CAMP, camp_groups, gname


def med(x):
    return statistics.median(x) if x else None


def main(exdir, sides_path, me='Master'):
    sides = json.load(open(sides_path))
    agg = {'us': collections.Counter(), 'opp': collections.Counter()}
    killers = {'us': collections.Counter(), 'opp': collections.Counter()}
    groups_engaged = {'us': collections.Counter(), 'opp': collections.Counter()}
    death_ctx = collections.Counter()
    first_buy = {'us': [], 'opp': []}
    rows = []
    for key, v in sides.items():
        d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
        m = mapinfo.replay_map(d['file'].replace('.json', '.repl26a')) if d['file'].endswith('.repl26a') else mapinfo.replay_map(d['file'])
        us_t = 0 if v['A'] == me else 1
        champ = {c['i']: c for c in d['champions']}
        team = {c['i']: c['team'] for c in d['champions']}
        camp_t = {c['i']: c['type'] for c in d['camps']}
        groups = camp_groups(d['camps'])
        camp_group = {c['i']: gname(g) for g in groups for c in g}
        sp = [set((x, y) for x in range(a[0], a[2]) for y in range(a[1], a[3])) for a in m['spawn']]
        R = d['rounds']
        hp = {(r, i): (c[6] / c[7] if c[7] else 0) for r, _, _, cs in R for i, c in enumerate(cs)}
        P = {(r, i): (c[4], c[5]) for r, _, _, cs in R for i, c in enumerate(cs)}
        alive = {(r, i): c[2] for r, _, _, cs in R for i, c in enumerate(cs)}
        last_recall = {}
        acted = collections.defaultdict(set)   # champion -> rounds with attack/cast/tribute
        shards = collections.Counter()
        for e in d['events']:
            r, k = e['r'], e['k']
            if e['a'][0] == 1:
                ai = e['a'][1]
                if k in ('Attack', 'Cast ability', 'Submit gems', 'Gems submitted'):
                    acted[ai].add(r)
                if k == 'Recall':
                    last_recall[ai] = r
                if k in ('Attack', 'Cast ability'):
                    tg = e.get('tg')
                    if tg and tg[0] == 'M':
                        groups_engaged['us' if team[ai] == us_t else 'opp'][camp_group.get(tg[1], '?')] += 1
            if k == 'Shop':
                for x in e.get('d', []):
                    n = sum(c for j, c in x.get('items', []) if c > 0 and j % 2 == 0)
                    shards[x['i']] += n
                    if n and shards[x['i']] == n:
                        first_buy['us' if team[x['i']] == us_t else 'opp'].append(r)
            for x in e.get('d', []):
                if x.get('alive') != 0:
                    continue
                side = 'us' if team[x['i']] == us_t else 'opp'
                agg[side]['deaths'] += 1
                if e['a'][0] == 2:
                    ct = CAMP[camp_t.get(e['a'][1], 0)]
                    killers[side][ct] += 1
                    agg[side]['deaths_to_camps'] += 1
                    if side == 'us':
                        h = hp.get((r - 3, x['i']), 1)
                        rec = last_recall.get(x['i'], -99)
                        allies = sum(1 for j in champ if j != x['i'] and team[j] == team[x['i']] and alive.get((r - 1, j))
                                     and max(abs(P[(r - 1, j)][0] - P[(r - 1, x['i'])][0]), abs(P[(r - 1, j)][1] - P[(r - 1, x['i'])][1])) <= 5)
                        death_ctx['camp death'] += 1
                        death_ctx['  recall started in previous 8 rounds (interrupted)'] += r - rec <= 8
                        death_ctx['  hp >= 50% three rounds earlier'] += h >= 0.5
                        death_ctx['  no ally within 5 tiles'] += allies == 0
                        death_ctx['  carrying gems'] += x.get('gems', 0) < 0
                        death_ctx[f'  killed by {camp_group.get(e["a"][1], "?")}'] += 1
                else:
                    killers[side]['champion'] += 1
        # stuck / spawn time
        for i in champ:
            side = 'us' if team[i] == us_t else 'opp'
            run, prevp = 0, None
            for r, _, _, cs in R:
                c = cs[i]
                if not c[2]:
                    run, prevp = 0, None
                    agg[side]['dead_rounds'] += 1
                    continue
                agg[side]['alive_rounds'] += 1
                p = (c[4], c[5])
                if p in sp[team[i]]:
                    agg[side]['spawn_rounds'] += 1
                if p == prevp and p not in sp[team[i]] and r not in acted[i]:
                    run += 1
                    if run == 15:
                        agg[side]['stuck_episodes'] += 1
                    if run >= 15:
                        agg[side]['stuck_rounds'] += 1
                else:
                    run = 0
                prevp = p
        sub = d['submitted']
        rows.append((v['map'], 'W' if (d['outcome'] == 1) == (us_t == 0) else 'L', sub[us_t], sub[1 - us_t], d['rounds_played'],
                     v['B'] if us_t == 0 else v['A']))
    print('| map | result | gems us-them | rounds | opponent |\n|---|---|---|---|---|')
    for r in rows:
        print(f'| {r[0]} | {r[1]} | {r[2]}-{r[3]} | {r[4]} | {r[5]} |')
    for side in ('us', 'opp'):
        a = agg[side]
        print(f"\n**{side}**: deaths {a['deaths']} (to camps {a['deaths_to_camps']}); killers {dict(killers[side].most_common())}; "
              f"dead {100 * a['dead_rounds'] / (a['dead_rounds'] + a['alive_rounds']):.0f}% of champion-rounds; "
              f"on spawn {100 * a['spawn_rounds'] / a['alive_rounds']:.0f}% of alive rounds; "
              f"stuck episodes {a['stuck_episodes']} ({a['stuck_rounds']} rounds); median first shard round {med(first_buy[side])}")
        tot = sum(groups_engaged[side].values())
        print('  attacks on camp groups: ' + ', '.join(f'{k} {100 * v / tot:.0f}%' for k, v in groups_engaged[side].most_common(8)))
    print('\nOur deaths to camps:')
    for k, v in death_ctx.most_common():
        print(f'- {k}: {v}')


if __name__ == '__main__':
    main(*sys.argv[1:])
