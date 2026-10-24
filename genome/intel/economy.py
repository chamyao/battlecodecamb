"""Economy breakdown in real games: where each side's gold comes from and when the gap opens, by our wins and losses.

Usage: python3 -I genome/intel/economy.py ANALYSIS_DIR FETCHDIR EXDIR
Gold sources per side (per game): captures, split into gold-only (0-gem) groups and gem groups, kill bounties,
and other (gold_earned minus both: camp-kill or passive gold the replay credits outside captures and kills).
Timing: cumulative gold earned by rounds 250 / 500 / 750 / 1000. Also gold per capture and kills per game.
"""
import collections, json, os, statistics, sys


def main(argv):
    adir, fd, ex = argv[:3]
    sys.path.insert(0, os.path.abspath(adir))
    import analyse
    rows = []
    for v in json.load(open(os.path.join(fd, 'sides.json'))).values():
        d = json.load(open(os.path.join(ex, 'ladder', v['file'])))
        us = 0 if v['A'] == 'Master' else 1
        st = analyse.game_stats(d, (v['A'], v['B']))
        team = {c['i']: c['team'] for c in d['champions']}
        cum = [collections.Counter(), collections.Counter()]
        for e in d['events']:
            if e['k'] in ('Shop', 'Sell item'):
                continue
            for x in e.get('d', []):
                if x.get('gold', 0) > 0 and x['i'] in team:
                    for rd in (250, 500, 750, 1000):
                        if e['r'] <= rd:
                            cum[team[x['i']]][rd] += x['gold']
        row = dict(win=(d['outcome'] == 1) == (us == 0))
        for side, t in (('us', us), ('them', 1 - us)):
            x = st[t]
            caps = x['lists'].get('capture', [])
            row[f'{side}_earned'] = x.get('gold_earned', 0)
            row[f'{side}_cap_goldonly'] = sum(c[3] for c in caps if c[2] == 0)
            row[f'{side}_cap_gemgroups'] = sum(c[3] for c in caps if c[2] > 0)
            row[f'{side}_kills_gold'] = x.get('gold_from_kills', 0)
            row[f'{side}_kills'] = x.get('kills', 0)
            row[f'{side}_other'] = row[f'{side}_earned'] - row[f'{side}_cap_goldonly'] - row[f'{side}_cap_gemgroups'] - row[f'{side}_kills_gold']
            row[f'{side}_ncap'] = len(caps)
            row[f'{side}_ncap_goldonly'] = sum(1 for c in caps if c[2] == 0)
            for rd in (250, 500, 750, 1000):
                row[f'{side}_by{rd}'] = cum[t][rd]
        rows.append(row)
    W = [r for r in rows if r['win']]; L = [r for r in rows if not r['win']]
    m = lambda R, k: statistics.mean(r[k] for r in R) if R else 0
    print(f'{len(rows)} games ({len(W)}-{len(L)}). Gold per game, us / them:\n')
    print('| source | our wins | our losses |')
    print('|---|---|---|')
    for k, nm in (('earned', 'gold earned'), ('cap_goldonly', 'captures of gold-only groups'), ('cap_gemgroups', 'captures of gem groups'),
                  ('kills_gold', 'kill bounties'), ('other', 'other (camp kills, passives)'), ('kills', 'kills (count)'),
                  ('ncap', 'captures (count)'), ('ncap_goldonly', 'gold-only captures (count)'),
                  ('by250', 'earned by r250'), ('by500', 'earned by r500'), ('by750', 'earned by r750'), ('by1000', 'earned by r1000')):
        print(f'| {nm} | {m(W, "us_" + k):.0f} / {m(W, "them_" + k):.0f} | {m(L, "us_" + k):.0f} / {m(L, "them_" + k):.0f} |')


if __name__ == '__main__':
    main(sys.argv[1:])
