"""Aggregate statistics over the extracted Sprint 1 games.

Usage: python3 analyse.py EXDIR sides.json OUT.json
EXDIR is the output of run_all.sh. Prints markdown tables used in docs/SPRINT1_ANALYSIS.md
and writes every number to OUT.json.
"""
import collections, json, os, statistics, sys

CH = ['Ryth', 'Vesper Vale', 'Vendetta', 'Cassi', 'Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart of Ruin']
DRAFT = ['Ryth', 'Vesper Vale', 'Vendetta', 'Cassi & Issac', 'Stellar', 'Prism', 'Marcella', 'Willow', 'Ren', 'Varg', 'Tavi', 'Heart of Ruin']
CAMP = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem']
FAM = ['Monster', 'Power', 'Durability', 'Treasure', 'Jungle', 'Home', 'Bruiser']
STAT = ['Str', 'Foc', 'HP']
CONS = {0: 'teleport', 2: 'altar_lock'}
TOP4 = ['Intercontinental Fish', 'Nyx', 'Univardisty of Shingtonwash', 'hello']
if os.environ.get('TOP4'):  # comma-separated team names, e.g. the current ladder top 4
    TOP4 = os.environ['TOP4'].split(',')
# Single altar walled in behind two monoliths: 14/15 games reach round 2000, mostly 0-0,
# decided on lifetime gold. Excluded from per-game averages, reported separately.
LOCKED_MAP = '1b8ddaecdb'


def item_name(j):
    fam, rest = divmod(j, 6)
    stat, emb = divmod(rest, 2)
    return f"{FAM[fam]} {'Emblem' if emb else 'shard'} {STAT[stat]}"


def med(xs):
    return statistics.median(xs) if xs else None


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def camp_groups(camps):
    """Cardinally connected camps -> list of groups (each a list of camp dicts)."""
    by = {(c['x'], c['y']): c for c in camps}
    seen, groups = set(), []
    for c in camps:
        if c['i'] in seen:
            continue
        stack, g = [c], []
        seen.add(c['i'])
        while stack:
            u = stack.pop(); g.append(u)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = by.get((u['x'] + dx, u['y'] + dy))
                if v and v['i'] not in seen:
                    seen.add(v['i']); stack.append(v)
        groups.append(g)
    return groups


def gname(g):
    c = collections.Counter(CAMP[x['type']] for x in g)
    return '+'.join(f"{k}x{v}" if v > 1 else k for k, v in sorted(c.items()))


def game_stats(d, side_names):
    """Per-team stats for one game. side_names = (team on side A, team on side B)."""
    champ = {c['i']: c for c in d['champions']}
    team_of = {c['i']: c['team'] for c in d['champions']}
    groups = camp_groups(d['camps'])
    tile_group = {}
    for gi, g in enumerate(groups):
        for c in g:
            tile_group[(c['x'], c['y'])] = gi
    T = [collections.defaultdict(lambda: 0) for _ in range(2)]
    lists = [collections.defaultdict(list) for _ in range(2)]
    builds = collections.defaultdict(list)       # champion i -> purchases in order
    rounds = d['rounds']
    hp_at = {}                                    # (round, i) -> hp fraction at end of round
    gold_at, gems_at = {}, {}
    since_trib = collections.Counter()            # champion -> captures since last tribute
    for r, sa, sb, cs in rounds:
        for i, c in enumerate(cs):
            gold_at[(r, i)], gems_at[(r, i)] = c[0], c[1]
            hp_at[(r, i)] = c[6] / champ[i]['maxHealth'] if champ[i]['maxHealth'] else 0
    for e in d['events']:
        k, (ak, ai) = e['k'], e['a']
        actor_team = team_of.get(ai) if ak == 1 else None
        diffs = e.get('d', [])
        if k == 'Attack' and ak == 1:
            t = T[actor_team]
            tg = e.get('tg')
            if tg and tg[0] == 'C':
                t['atk_champ'] += 1
                t['dmg_champ'] += -sum(x.get('hp', 0) for x in diffs if x['i'] == tg[1])
            elif tg and tg[0] == 'M':
                t['atk_camp'] += 1
                t['dmg_camp'] += -sum(v for _, v in e.get('cd', []))
            else:
                t['atk_other'] += 1
        if k == 'Cast ability' and ak == 1:
            t = T[actor_team]
            tg = e.get('tg')
            if tg is None:
                cls = 'ground'
            elif tg[0] == 'M':
                cls = 'camp'
            elif tg[1] == ai:
                cls = 'self'
            elif team_of[tg[1]] == actor_team:
                cls = 'ally'
            else:
                cls = 'enemy'
            lists[actor_team]['casts'].append((CH[champ[ai]['type']], e['sl'], cls))
            if cls == 'enemy':
                t['dmg_champ_spell'] += -sum(x.get('hp', 0) for x in diffs if team_of[x['i']] != actor_team)
            if e.get('cd'):
                t['dmg_camp_spell'] += -sum(v for _, v in e['cd'])
        if k == 'Place ward' and ak == 1:
            T[actor_team]['wards'] += 1
        if k == 'Place altar lock' and ak == 1:
            T[actor_team]['altar_locks'] += 1
            lists[actor_team]['lock_rounds'].append(e['r'])
        if k == 'Teleport channel' and ak == 1:
            T[actor_team]['teleports'] += 1
        if k == 'Recall' and ak == 1:
            T[actor_team]['recall_starts'] += 1
            prev_hp = hp_at.get((e['r'] - 1, ai))
            if prev_hp is not None:
                lists[actor_team]['recall_hp'].append(prev_hp)
                lists[actor_team]['recall_ctx'].append((prev_hp, gold_at.get((e['r'] - 1, ai), 0), gems_at.get((e['r'] - 1, ai), 0)))
        if k == 'Cancel channel' and ak == 1:
            T[actor_team]['channel_cancels'] += 1
        if k == 'Submit gems' and ak == 1:
            T[actor_team]['tribute_starts'] += 1
        if k == 'Shop' and ak == 1:
            for x in diffs:
                for j, n in x.get('items', []):
                    if n > 0:
                        builds[x['i']].append((e['r'], j, n))
                for j, n in x.get('cons', []):
                    if n > 0:
                        T[team_of[x['i']]]['buy_' + CONS.get(j, str(j))] += n
                if x.get('gold', 0) < 0:
                    T[team_of[x['i']]]['gold_spent'] += -x['gold']
        if k == 'Capture':
            recv = [x for x in diffs if x.get('gold', 0) > 0 or x.get('gems', 0) > 0]
            if recv:
                tm = team_of[recv[0]['i']]
                gold = sum(x.get('gold', 0) for x in recv); gems = sum(x.get('gems', 0) for x in recv)
                gi = tile_group.get(tuple(recv[0].get('p', (-1, -1))))
                gn = gname(groups[gi]) if gi is not None else '?'
                T[tm]['captures'] += 1
                T[tm]['capture_gems'] += gems
                T[tm]['capture_gold'] += gold
                if len(recv) > 1:
                    T[tm]['split_captures'] += 1
                lists[tm]['capture'].append((e['r'], gn, gems, gold, len(recv)))
                for x in recv:
                    if x.get('gems', 0) > 0:
                        since_trib[x['i']] += 1
                    lists[tm]['captor'].append(CH[champ[x['i']]['type']])
        if k == 'Gems submitted':
            for x in diffs:
                if x.get('gems', 0) < 0:
                    tm = team_of[x['i']]
                    lists[tm]['tribute'].append((e['r'], -x['gems'], CH[champ[x['i']]['type']], since_trib[x['i']]))
                    since_trib[x['i']] = 0
        # deaths, kills, steals (any step)
        dead = [x for x in diffs if x.get('alive') == 0]
        killers = [x for x in diffs if x.get('kills', 0) > 0]
        for x in dead:
            vt = team_of[x['i']]
            since_trib[x['i']] = 0
            T[vt]['deaths'] += 1
            lost = -x.get('gems', 0)
            T[vt]['gems_lost_on_death'] += lost
            kl = [y for y in killers if team_of[y['i']] != vt]
            if kl:
                kt = team_of[kl[0]['i']]
                T[vt]['deaths_to_champ'] += 1
                T[kt]['kills'] += 1
                T[kt]['gems_stolen'] += max(0, kl[0].get('gems', 0))
                lists[kt]['kill_rounds'].append(e['r'])
            else:
                T[vt]['deaths_to_camp'] += 1
        # gold earned (not shop/sell)
        if k not in ('Shop', 'Sell item'):
            for x in diffs:
                if x.get('gold', 0) > 0:
                    T[team_of[x['i']]]['gold_earned'] += x['gold']
                    if x.get('kills', 0) > 0:
                        T[team_of[x['i']]]['gold_from_kills'] += x['gold']
    # curves
    curve = {}
    for r, sa, sb, cs in rounds:
        if r % 50 == 0 or r == rounds[-1][0]:
            carried = [0, 0]
            for i, c in enumerate(cs):
                carried[team_of[i]] += c[1]
            curve[r] = dict(sub=[sa, sb], carried=carried)
    out = []
    winner = 0 if d['outcome'] == 1 else 1
    for t in (0, 1):
        s = dict(T[t])
        s.update(team=side_names[t], opp=side_names[1 - t], side='AB'[t], win=int(t == winner),
                 tributed=d['submitted'][t], opp_tributed=d['submitted'][1 - t], rounds=d['rounds_played'],
                 draft=[DRAFT[x] for x in d['drafts'][t] if x >= 0],
                 opp_draft=[DRAFT[x] for x in d['drafts'][1 - t] if x >= 0])
        s['lists'] = {k: v for k, v in lists[t].items()}
        s['builds'] = {f"{CH[champ[i]['type']]}": [(r, item_name(j), n) for r, j, n in b]
                       for i, b in builds.items() if team_of[i] == t}
        s['curve'] = {r: dict(sub=v['sub'][t], opp=v['sub'][1 - t], carried=v['carried'][t]) for r, v in curve.items()}
        out.append(s)
    return out


def load(exdir, sides):
    rows = []
    for key, v in sides.items():
        code, n = key.split('/')
        d = json.load(open(os.path.join(exdir, code, v['file'])))
        for s in game_stats(d, (v['A'], v['B'])):
            s.update(code=code, game=int(n), map=v['map'])
            rows.append(s)
    return rows


def table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)]
    for r in rows:
        out.append('| ' + ' | '.join('' if x is None else (f'{x:.2f}' if isinstance(x, float) else str(x)) for x in r) + ' |')
    return '\n'.join(out)


def report(all_rows):
    R = {}
    rows = [r for r in all_rows if r['map'] != LOCKED_MAP]
    teams = sorted({r['team'] for r in rows}, key=lambda t: -sum(x['win'] for x in rows if x['team'] == t))
    P = print

    # ---- 1. drafts
    P('\n## Drafts\n')
    pick = collections.Counter(); pick_w = collections.Counter(); first = collections.Counter()
    slot = collections.defaultdict(list)
    solo = collections.Counter(); solo_w = collections.Counter()
    for r in rows:
        for k, c in enumerate(r['draft']):
            pick[c] += 1; pick_w[c] += r['win']; slot[c].append(k + 1)
            if c not in r['opp_draft']:
                solo[c] += 1; solo_w[c] += r['win']
        first[r['draft'][0]] += 1
    n = len(rows)
    tab = [(c, pick[c], f"{100 * pick[c] / n:.0f}%", first[c], f"{mean(slot[c]):.1f}", f"{100 * pick_w[c] / pick[c]:.0f}%",
            solo[c], f"{100 * solo_w[c] / solo[c]:.0f}%" if solo[c] else '-') for c in sorted(pick, key=lambda c: -pick[c])]
    P(f'All 16 teams, {n} team-games.\n')
    P(table(['champion', 'picks', 'pick rate', 'first pick', 'mean slot', 'win rate', 'picks opp lacked', 'win rate then'], tab))
    R['draft_all'] = tab
    # per top team
    P('\nTop-4 teams: most common drafts (order as picked)\n')
    for t in TOP4:
        c = collections.Counter(' > '.join(r['draft']) for r in rows if r['team'] == t)
        P(f"- **{t}** ({sum(1 for r in rows if r['team'] == t)} games): " + '; '.join(f'{k} ({v})' for k, v in c.most_common(4)))
    # team size
    sizes = collections.Counter(len(r['draft']) for r in rows)
    P(f"\nTeam sizes: {dict(sizes)} (team-games)")

    # ---- 2. economy
    P('\n## Economy per team (mean per game)\n')
    tab = []
    for t in teams:
        rs = [r for r in rows if r['team'] == t]
        g = len(rs)
        tribs = [x for r in rs for x in r['lists'].get('tribute', [])]
        caps = [x for r in rs for x in r['lists'].get('capture', [])]
        firstcap = [min(x[0] for x in r['lists']['capture']) for r in rs if r['lists'].get('capture')]
        firsttrib = [min(x[0] for x in r['lists']['tribute']) for r in rs if r['lists'].get('tribute')]
        tab.append((t, g, sum(r['win'] for r in rs), round(mean([r['tributed'] for r in rs])),
                    round(mean([r.get('gold_earned', 0) for r in rs])),
                    round(len(caps) / g, 1), round(mean([x[2] for x in caps]) or 0, 1),
                    f"{100 * sum(1 for x in caps if x[4] > 1) / max(1, len(caps)):.0f}%",
                    round(len(tribs) / g, 1), med([x[1] for x in tribs]), round(mean([x[1] for x in tribs]) or 0, 1),
                    med(firstcap), med(firsttrib)))
    P(table(['team', 'games', 'wins', 'gems tributed', 'gold earned', 'captures', 'gems/capture', 'shared captures',
             'tributes', 'median bag', 'mean bag', 'median 1st capture rd', 'median 1st tribute rd'], tab))
    R['economy'] = tab

    # bag size distribution top4 vs rest, winners vs losers
    def bags(sel):
        return [x[1] for r in rows if sel(r) for x in r['lists'].get('tribute', [])]
    P('\nBag size at tribute (gems), distribution\n')
    bins = [(1, 10), (11, 20), (21, 30), (31, 50), (51, 80), (81, 120), (121, 10000)]
    tab = []
    for name, sel in [('top-4 teams', lambda r: r['team'] in TOP4), ('other 12', lambda r: r['team'] not in TOP4),
                      ('game winners', lambda r: r['win']), ('game losers', lambda r: not r['win'])]:
        b = bags(sel)
        tab.append([name, len(b), med(b)] + [f"{100 * sum(1 for x in b if lo <= x <= hi) / len(b):.0f}%" for lo, hi in bins])
    P(table(['who', 'tributes', 'median'] + [f'{lo}-{hi}' if hi < 10000 else f'{lo}+' for lo, hi in bins], tab))
    R['bags'] = tab
    P('\nCaptures (with gems) by the tributing champion since its previous tribute or death\n')
    tab = []
    for name, sel in [('top-4 teams', lambda r: r['team'] in TOP4), ('other 12', lambda r: r['team'] not in TOP4),
                      ('game winners', lambda r: r['win']), ('game losers', lambda r: not r['win'])] + [(t, (lambda t: lambda r: r['team'] == t)(t)) for t in TOP4]:
        c = [x[3] for r in rows if sel(r) for x in r['lists'].get('tribute', [])]
        tab.append([name, len(c), f"{mean(c):.2f}"] + [f"{100 * sum(1 for x in c if x == k) / len(c):.0f}%" for k in (0, 1, 2, 3)] + [f"{100 * sum(1 for x in c if x >= 4) / len(c):.0f}%"])
    P(table(['who', 'tributes', 'mean', '0 (stolen/shared gems)', '1', '2', '3', '4+'], tab))
    R['caps_per_tribute'] = tab
    P('\nWho captures and who tributes (top-4 teams; share of capture rewards received / tributes made)\n')
    cap = collections.Counter(x for r in rows if r['team'] in TOP4 for x in r['lists'].get('captor', []))
    tri = collections.Counter(x[2] for r in rows if r['team'] in TOP4 for x in r['lists'].get('tribute', []))
    P(', '.join(f"{k} {100 * v / sum(cap.values()):.0f}%/{100 * tri[k] / sum(tri.values()):.0f}%" for k, v in cap.most_common()))

    # tribute curve
    P('\nTributed gems by round (median over games; winners vs losers)\n')
    tab = []
    for rd in (100, 200, 300, 400, 500, 600, 800):
        def at(r):
            ks = sorted(int(k) for k in r['curve'])
            ks = [k for k in ks if k <= rd]
            return r['curve'][ks[-1]]['sub'] if ks else 0
        w = [at(r) for r in rows if r['win']]; l = [at(r) for r in rows if not r['win']]
        f = [at(r) for r in rows if r['team'] == 'Intercontinental Fish']; ny = [at(r) for r in rows if r['team'] == 'Nyx']
        tab.append((rd, med(w), med(l), med(f), med(ny)))
    P(table(['round', 'winners', 'losers', 'Fish', 'Nyx'], tab))
    R['curve'] = tab

    # camps farmed
    P('\nCamp groups captured (top-4 teams), share of captures and median first-capture round\n')
    for t in TOP4 + ['(all)']:
        caps = [x for r in rows if (t == '(all)' or r['team'] == t) for x in r['lists'].get('capture', [])]
        c = collections.Counter(x[1] for x in caps)
        tot = sum(c.values())
        P(f"- **{t}**: " + ', '.join(f"{k} {100 * v / tot:.0f}%" for k, v in c.most_common(6)))
    # what the first 3 captures are
    P('\nFirst three captures of each game (all teams): ' + ', '.join(
        f'{k} {v}' for k, v in collections.Counter(x[1] for r in rows for x in sorted(r['lists'].get('capture', []))[:3]).most_common(6)))
    rewards = collections.defaultdict(set)
    for r in rows:
        for x in r['lists'].get('capture', []):
            if x[4] == 1:
                rewards[x[1]].add((x[2], x[3]))
    P('\nObserved (gems, gold) per capture by group type (single captor): ' + '; '.join(
        f"{k}: {sorted(v)[:3]}" for k, v in sorted(rewards.items(), key=lambda kv: -len(kv[1]))[:10]))

    # ---- 3. items
    P('\n## Items\n')
    fam = collections.defaultdict(collections.Counter)
    first_buy = collections.defaultdict(collections.Counter)
    seqs = collections.defaultdict(collections.Counter)
    emblems = collections.defaultdict(collections.Counter)
    for r in rows:
        if r['team'] not in TOP4:
            continue
        for ch, b in r['builds'].items():
            shards = [(nm, n) for _, nm, n in b if 'shard' in nm]
            for nm, nn in shards:
                fam[ch][nm] += nn
            if shards:
                first_buy[ch][shards[0][0]] += 1
            seq = []
            for nm, nn in shards:
                if not seq or seq[-1] != nm:
                    seq.append(nm)
            seqs[(r['team'], ch)][' > '.join(seq[:4])] += 1
            for _, nm, n in b:
                if 'Emblem' in nm:
                    emblems[ch][nm] += n
    P('Shards bought by top-4 teams, per champion (all games):\n')
    for ch in sorted(fam, key=lambda c: -sum(fam[c].values())):
        tot = sum(fam[ch].values())
        P(f"- **{ch}** ({tot} shards): " + ', '.join(f"{k} {100 * v / tot:.0f}%" for k, v in fam[ch].most_common(4)) +
          '; emblems: ' + ', '.join(f"{k} {v}" for k, v in emblems[ch].most_common(3)))
    P('\nBuild order (distinct shard kinds in order, first four) per top-4 team and champion, most common:\n')
    for (t, ch), c in sorted(seqs.items()):
        k, v = c.most_common(1)[0]
        tot = sum(c.values())
        P(f"- {t} / {ch}: {k} ({v}/{tot})")
    R['items'] = {ch: dict(c) for ch, c in fam.items()}
    # consumables
    tab = [(t, round(mean([r.get('buy_altar_lock', 0) for r in rows if r['team'] == t]), 2),
            round(mean([r.get('altar_locks', 0) for r in rows if r['team'] == t]), 2),
            round(mean([r.get('buy_teleport', 0) for r in rows if r['team'] == t]), 2),
            round(mean([r.get('teleports', 0) for r in rows if r['team'] == t]), 2),
            round(mean([r.get('gold_spent', 0) for r in rows if r['team'] == t]))) for t in teams]
    P('\nConsumables and spending (mean per game)\n')
    P(table(['team', 'altar locks bought', 'altar locks placed', 'teleports bought', 'teleports used', 'gold spent'], tab))

    # ---- 4. fighting
    P('\n## Fighting (mean per game)\n')
    tab = []
    for t in teams:
        rs = [r for r in rows if r['team'] == t]
        A = lambda k: mean([r.get(k, 0) for r in rs])
        atk = A('atk_champ') + A('atk_camp')
        tab.append((t, round(A('atk_champ')), round(A('atk_camp')), f"{100 * A('atk_champ') / atk:.0f}%",
                    round(A('dmg_champ') + A('dmg_champ_spell')), round(A('dmg_camp') + A('dmg_camp_spell')),
                    round(A('kills'), 1), round(A('deaths'), 1), round(A('deaths_to_camp'), 1),
                    round(A('gems_stolen'), 1), round(A('gems_lost_on_death'), 1), round(A('wards')), round(A('altar_locks'), 2)))
    P(table(['team', 'basic attacks on champs', 'on camps', 'champ share', 'dmg to champs', 'dmg to camps',
             'kills', 'deaths', 'deaths to camps', 'gems stolen', 'gems lost dying', 'wards', 'altar locks'], tab))
    R['fighting'] = tab
    # recall
    P('\nRecall: health fraction at the end of the round before a recall starts\n')
    tab = []
    for t in teams:
        h = [x for r in rows if r['team'] == t for x in r['lists'].get('recall_hp', [])]
        rs = [r for r in rows if r['team'] == t]
        tab.append((t, round(mean([r.get('recall_starts', 0) for r in rs]), 1), round(mean([r.get('channel_cancels', 0) for r in rs]), 1),
                    f"{100 * sum(1 for x in h if x <= 0.25) / max(1, len(h)):.0f}%", f"{100 * sum(1 for x in h if x >= 0.9) / max(1, len(h)):.0f}%",
                    round(med(h) or 0, 2)))
    P(table(['team', 'recall starts', 'channel cancels', 'at <=25% hp', 'at >=90% hp', 'median hp'], tab))
    P('\nRecalls started at >=90% hp (top-4 teams): what the champion carried (end of previous round)\n')
    for t in TOP4:
        ctx = [x for r in rows if r['team'] == t for x in r['lists'].get('recall_ctx', []) if x[0] >= 0.9]
        if ctx:
            P(f"- {t}: {len(ctx)} recalls; gold >=150 in {100 * sum(1 for x in ctx if x[1] >= 150) / len(ctx):.0f}%, carrying gems in {100 * sum(1 for x in ctx if x[2] > 0) / len(ctx):.0f}%, median gold {med([x[1] for x in ctx])}")

    # ---- 5. abilities
    P('\n## Abilities (all teams): casts per champion-game and target class\n')
    casts = collections.defaultdict(collections.Counter)
    games_with = collections.Counter()
    for r in rows:
        for c in set(x for d_ in [r['draft']] for x in d_):
            for ch in (['Cassi', 'Issac'] if c == 'Cassi & Issac' else [c]):
                games_with[ch] += 1
        for ch, sl, cls in r['lists'].get('casts', []):
            casts[(ch, sl)][cls] += 1
    tab = []
    for (ch, sl), c in sorted(casts.items()):
        tot = sum(c.values())
        tab.append((ch, sl, round(tot / games_with[ch], 1), ', '.join(f"{k} {100 * v / tot:.0f}%" for k, v in c.most_common())))
    P(table(['champion', 'slot', 'casts/game', 'targets'], tab))
    R['abilities'] = tab

    # ---- 6. winners vs losers
    P('\n## Winners vs losers (all games, per team-game means)\n')
    keys = ['tributed', 'gold_earned', 'captures', 'capture_gems', 'kills', 'deaths', 'deaths_to_camp', 'gems_stolen',
            'gems_lost_on_death', 'atk_champ', 'atk_camp', 'wards', 'altar_locks', 'tribute_starts', 'recall_starts', 'gold_spent']
    tab = []
    decided = [r for r in rows if r['rounds'] < 2000]
    timeout_all = [r for r in all_rows if r['rounds'] >= 2000]
    for k in keys:
        w = [r.get(k, 0) for r in decided if r['win']]; l = [r.get(k, 0) for r in decided if not r['win']]
        tab.append((k, round(mean(w), 1), round(mean(l), 1)))
    P(f'{len(decided) // 2} games decided before round 2000.\n')
    P(table(['metric', 'winner', 'loser'], tab))
    R['winloss'] = tab
    # draw-like games
    timeout = timeout_all
    P(f"\nGames reaching round 2000: {len(timeout) // 2}, maps: {collections.Counter(r['map'] for r in timeout if r['side'] == 'A')}")
    for r in timeout:
        if r['side'] == 'A':
            o = [x for x in timeout if x['code'] == r['code'] and x['game'] == r['game'] and x['side'] == 'B'][0]
            P(f"  - {r['code']}/{r['game']:02d} {r['team']} {r['tributed']} vs {r['opp']} {r['opp_tributed']}; gold earned {r.get('gold_earned', 0)} vs {o.get('gold_earned', 0)}; kills {r.get('kills', 0)} vs {o.get('kills', 0)}; winner {r['team'] if r['win'] else r['opp']}")
    # predictors: who leads at round 200/300 wins?
    P('\nDoes the leader in tributed gems at round N win? (decided games)\n')
    tab = []
    for rd in (150, 200, 300, 400):
        agree = tot = 0
        for r in decided:
            if r['side'] != 'A':
                continue
            ks = [int(k) for k in r['curve'] if int(k) <= rd]
            if not ks:
                continue
            c = r['curve'][max(ks)]
            if c['sub'] == c['opp']:
                continue
            tot += 1; agree += (c['sub'] > c['opp']) == bool(r['win'])
        tab.append((rd, tot, f"{100 * agree / tot:.0f}%"))
    P(table(['round', 'games with a leader', 'leader wins'], tab))

    # ---- close series
    for code in [c for c in ('w9-0', 'w10-0') if any(r['code'] == c for r in rows)]:
        P(f'\n## Series {code}\n')
        rs = sorted([r for r in rows if r['code'] == code and r['team'] == 'Intercontinental Fish'], key=lambda r: r['game'])
        tab = [(r['game'], r['map'], 'W' if r['win'] else 'L', f"{r['tributed']}-{r['opp_tributed']}", r['rounds'],
                ' '.join(x.split()[0] for x in r['draft']), ' '.join(x.split()[0] for x in r['opp_draft']),
                f"{r.get('kills', 0)}-{r.get('deaths', 0)}", f"{r.get('gems_stolen', 0)}", r.get('captures', 0),
                r.get('wards', 0), r.get('altar_locks', 0)) for r in rs]
        P(table(['g', 'map', 'Fish', 'gems', 'rounds', 'Fish draft', 'opp draft', 'Fish K-D', 'Fish stole', 'Fish caps', 'Fish wards', 'Fish locks'], tab))
    return R


if __name__ == '__main__':
    exdir, sides_path, outp = sys.argv[1:4]
    rows = load(exdir, json.load(open(sides_path)))
    print(f'Map {LOCKED_MAP} (monolith-locked altar) excluded from averages below unless stated: {sum(1 for r in rows if r["map"] != LOCKED_MAP) // 2} games remain.')
    R = report(rows)
    json.dump(dict(results=R, rows=[{k: v for k, v in r.items() if k not in ('lists', 'builds')} for r in rows]),
              open(outp, 'w'), default=str)
