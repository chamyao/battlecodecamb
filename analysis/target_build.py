"""Build the top-team fitting target: per-game outcomes and per-team fight statistics from the
same 10 unranked groups played by several of our versions (same teams, maps and sides).

Usage: python3 target_build.py OUT.json LABEL=EXDIR,FETCHDIR [LABEL=EXDIR,FETCHDIR ...] > summary.md

OUT.json:
- games: one row per (our version, top team, map, our side) with result, gems, kills, deaths,
  champion damage (official summaries), tributes, captures, gems per capture, share of our deaths
  with 2+ of theirs within 5 tiles, first-kill round both ways, drafts, rounds played.
- by_version_team: means of the same per (version, team), the level a stand-in should hit.
- fights[team][champion]: their engagement statistics pooled over all versions (fight_rules):
  engage distance at the first hit and 5/10 rounds before, opener distribution, rounds to first
  cast, allies/enemies within 5 at the first hit, basic-attack range, chase, disengage HP, recall
  within 10 rounds, kill rate.
- decisive[team]: our decisive deaths (no kill back within 10 rounds; fight_dump), per team.
"""
import collections, json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, fight_dump, fight_rules, mapinfo, race_analysis, top_teams
from analyse import CH, DRAFT


def med(x):
    x = [v for v in x if v is not None]
    return statistics.median(x) if x else None


def q(x, p):
    x = sorted(v for v in x if v is not None)
    return x[min(len(x) - 1, int(p * len(x)))] if x else None


def dist(x, nd=2):
    x = [v for v in x if v is not None]
    if not x:
        return None
    return dict(median=round(med(x), nd), p25=round(q(x, 0.25), nd), p75=round(q(x, 0.75), nd), n=len(x))


def first_kill(d, us):
    """Round of the first champion kill by each side (us, them)."""
    team = {c['i']: c['team'] for c in d['champions']}
    out = [None, None]
    for e in d['events']:
        if e['a'][0] != 1 or e['a'][1] not in team:
            continue
        s = 0 if team[e['a'][1]] == us else 1
        if out[s] is None and any(y.get('alive') == 0 and team[y['i']] != team[e['a'][1]] for y in e.get('d', [])):
            out[s] = e['r']
    return out


def main(out, *specs):
    games, E, D = [], collections.defaultdict(list), collections.defaultdict(list)
    for s in specs:
        label, dirs = s.split('=', 1)
        exdir, fetchdir = dirs.split(',')
        sides = json.load(open(os.path.join(fetchdir, 'sides.json')))
        race = {(r['opp'], r['map']): r for r in race_analysis.main(exdir, fetchdir)}
        for key, v in sorted(sides.items()):
            path = os.path.join(exdir, 'ladder', v['file'])
            if not os.path.exists(path):
                continue
            d = json.load(open(path))
            us = 0 if v['A'] == 'Master' else 1
            o = v['B'] if us == 0 else v['A']
            m = mapinfo.replay_map(d['file'])
            r = race[(o, v['map'])]
            summ = json.load(open(os.path.join(fetchdir, 'summaries', v['file'])))
            dmg = collections.Counter()
            for c in summ['champions']:
                dmg[0 if c['team'] == 'teamA' else 1] += int(c['metrics']['championDamageDone'])
            hunts = top_teams.hunting(d, us, m)
            fk = first_kill(d, us)
            games.append(dict(
                version=label, team=o, map=v['map'], our_side='A' if us == 0 else 'B', match=key.split('/')[-1],
                win=r['win'], rounds=r['rounds'], gems=[r['sub'][0], r['sub'][1]],
                kills=[r['us']['kills'], r['them']['kills']], deaths=[r['us']['deaths'], r['them']['deaths']],
                champion_damage=[dmg[us], dmg[1 - us]], tributes=[r['us']['tributes'], r['them']['tributes']],
                captures=[r['us']['caps'], r['them']['caps']], gems_per_capture=[round(r['us']['gpc'], 1), round(r['them']['gpc'], 1)],
                gold=[r['us']['gold'], r['them']['gold']], gems_lost_dying=[r['us']['lost'], r['them']['lost']],
                our_deaths_to_champions=len(hunts),
                share_2v1=round(sum(1 for h in hunts if h['hunters'] >= 2) / len(hunts), 3) if hunts else None,
                first_kill_round=fk, draft=[[DRAFT[x] for x in d['drafts'][us] if x >= 0], [DRAFT[x] for x in d['drafts'][1 - us] if x >= 0]]))
            for x in fight_rules.engagements(d, us, m):
                x['version'] = label
                E[o].append(x)
            for death in fight_dump.decisive(d, us):
                a = fight_dump.analyse_fight(d, m, us, death)
                if a:
                    D[o].append(a)

    mean = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
    byvt = []
    for (ver, t) in sorted({(g['version'], g['team']) for g in games}):
        G = [g for g in games if g['version'] == ver and g['team'] == t]
        row = dict(version=ver, team=t, games=len(G), wins=sum(g['win'] for g in G))
        for k in ('gems', 'kills', 'deaths', 'champion_damage', 'tributes', 'captures', 'gems_per_capture'):
            row[k] = [mean([g[k][0] for g in G]), mean([g[k][1] for g in G])]
        row['share_2v1'] = mean([g['share_2v1'] for g in G if g['share_2v1'] is not None])
        row['first_kill_round_them'] = med([g['first_kill_round'][1] for g in G])
        byvt.append(row)

    fights = {}
    for t, X in E.items():
        fights[t] = {}
        for ch in sorted({x['champ'] for x in X}):
            Y = [x for x in X if x['champ'] == ch]
            n = len(Y)
            rg = collections.Counter(r for x in Y for r in x['ranges'])
            fights[t][ch] = dict(
                engagements=n, kill_rate=round(sum(x['kill'] for x in Y) / n, 3),
                dist_first_hit=dist([x['d0'] for x in Y], 0), dist_5_before=dist([x['d5'] for x in Y], 0), dist_10_before=dist([x['d10'] for x in Y], 0),
                own_hp_first_hit=dist([x['hp'] for x in Y]), target_hp_first_hit=dist([x['thp'] for x in Y]),
                allies_within5=dist([x['allies'] for x in Y], 0), ours_within5=dist([x['enemies'] for x in Y], 0),
                target_closest=round(sum(x['closest'] for x in Y) / n, 3), target_lowest=round(sum(x['lowest'] for x in Y) / n, 3),
                target_carrier=round(sum(x['carrier'] for x in Y) / n, 3), from_bush=round(sum(x['bush'] for x in Y) / n, 3),
                first_action={k: round(v / n, 3) for k, v in collections.Counter(x['first'] for x in Y).most_common(5)},
                first_three={k: round(v / n, 3) for k, v in collections.Counter(x['seq'] for x in Y).most_common(5)},
                rounds_to_first_cast=dist([x['cast_delay'] for x in Y], 0),
                basic_range={str(k): round(v / max(1, sum(rg.values())), 3) for k, v in sorted(rg.items())},
                duration=dist([x['dur'] for x in Y], 0), chase=dist([x['chase'] for x in Y], 0),
                hp_end=dist([x['hp_end'] for x in Y]), recall_within10=round(sum(x['recall10'] for x in Y) / n, 3))
    decisive = {}
    for t, X in D.items():
        n = len(X)
        decisive[t] = dict(
            fights=n, them_first=round(sum(1 for x in X if x['first'] == 'them') / n, 3),
            hitters_2plus=round(sum(1 for x in X if x['n_hitters'] >= 2) / n, 3), rounds_to_death=med([x['ttk'] for x in X]),
            victim_hit_back=round(sum(x['victim_hit'] for x in X) / n, 3),
            hits_outside_victim_range=round(sum(x['out_range'] for x in X) / max(1, sum(x['their_hits'] for x in X)), 3),
            stun_on_victim=round(sum(x['stunned'] for x in X) / n, 3), killer_unseen_3=round(sum(x['unseen'] for x in X) / n, 3),
            victim_hitting_camp=round(sum(x['vcamp'] for x in X) / n, 3),
            gap_after_400=dict(strength=med([x['dstr'] for x in X if x['r0'] >= 400]), focus=med([x['dfoc'] for x in X if x['r0'] >= 400]),
                               max_hp=med([x['dhp'] for x in X if x['r0'] >= 400]),
                               item_points=[med([x['kpts'] for x in X if x['r0'] >= 400]), med([x['vpts'] for x in X if x['r0'] >= 400])]))
    json.dump(dict(note='Pairs are [us, them]. See docs/TOP_TEAMS_TARGET.md.', versions=[s.split('=')[0] for s in specs],
                   games=games, by_version_team=byvt, fights=fights, decisive=decisive), open(out, 'w'), indent=1)

    P = print
    P('| team | games | W-L (ours) | deaths us / them | kills us / them | gems us / them | champ dmg us / them | 2v1 share | first kill on us (median rd) | their draft (most common) |')
    P('|---|---|---|---|---|---|---|---|---|---|')
    for t in sorted({g['team'] for g in games}):
        G = [g for g in games if g['team'] == t]
        dr = collections.Counter(' '.join(n.split()[0] for n in g['draft'][1]) for g in G).most_common(1)[0][0]
        P(f"| {t} | {len(G)} | {sum(g['win'] for g in G)}-{sum(not g['win'] for g in G)} | {mean([g['deaths'][0] for g in G]):.1f} / {mean([g['deaths'][1] for g in G]):.1f} | "
          f"{mean([g['kills'][0] for g in G]):.1f} / {mean([g['kills'][1] for g in G]):.1f} | {mean([g['gems'][0] for g in G]):.0f} / {mean([g['gems'][1] for g in G]):.0f} | "
          f"{mean([g['champion_damage'][0] for g in G]) / 1000:.1f}k / {mean([g['champion_damage'][1] for g in G]) / 1000:.1f}k | "
          f"{mean([g['share_2v1'] for g in G if g['share_2v1'] is not None]):.2f} | {med([g['first_kill_round'][1] for g in G])} | {dr} |")
    P('\n| team | decisive fights | they hit first | 2+ hitters | victim hit back | stun on victim | hits from outside victim range | killer unseen 3 rds | item points after r400 killer/victim |')
    P('|---|---|---|---|---|---|---|---|---|')
    for t, x in sorted(decisive.items()):
        P(f"| {t} | {x['fights']} | {x['them_first']:.0%} | {x['hitters_2plus']:.0%} | {x['victim_hit_back']:.0%} | {x['stun_on_victim']:.0%} | {x['hits_outside_victim_range']:.0%} | {x['killer_unseen_3']:.0%} | {x['gap_after_400']['item_points']} |")


if __name__ == '__main__':
    main(*sys.argv[1:])
