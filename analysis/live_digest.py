"""Per-game digest of the newest live games: what decided each one.

Usage: python3 live_digest.py LIVEDIR EXDIR [N]   (the N most recent games, default 5)
Per game: result, gems, captured gems and gems per capture both sides, first tribute both sides,
our deaths to champions / camps / monoliths, gems we lost on death, the share of our champion
deaths with 2+ enemies within 5, our fuel-exhausted turns and bot faults (official summary), and a cause label:
  monolith      we died to monoliths 5+ times
  no-bank       our first tribute came after round 600 (or never) while theirs came before 300
  slow-start    their first tribute 60+ rounds before ours and they led at round 500
  low-yield     our gems per capture under 70% of theirs
  fights        we died 2x+ as often to champions as they did (and 8+ times)
  gems-lost     we lost 250+ gems on death
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse, mapinfo, race_analysis
from top_teams import hunting


def fuel_faults(livedir, v, us):
    """Our champions' fuel-exhausted turns and bot faults, from the official summary."""
    p = os.path.join(livedir, 'summaries', v['file'])
    if not os.path.exists(p):
        return None, None
    sm = json.load(open(p))
    team = 'teamA' if us == 0 else 'teamB'
    cnt = {'fuelExhausted': 0, 'botFault': 0}
    for e in sm.get('events', []):
        if e.get('kind') in cnt and e.get('owner', {}).get('team') == team:
            cnt[e['kind']] += len(e.get('entries', []))
    return cnt['fuelExhausted'], cnt['botFault']


def digest(exdir, v, livedir=None):
    d = json.load(open(os.path.join(exdir, 'ladder', v['file'])))
    us = 0 if v['A'] == 'Master' else 1
    m = mapinfo.replay_map(d['file'])
    team = {c['i']: c['team'] for c in d['champions']}
    st = analyse.game_stats(d, (v['A'], v['B']))
    sides = [race_analysis.side_numbers(d, st, t, m, team) for t in (us, 1 - us)]
    camps = {c['i']: c['type'] for c in d['camps']}
    mono = 0
    for e in d['events']:
        if e['a'][0] != 1 and camps.get(e['a'][1]) == 4:
            mono += sum(1 for y in e.get('d', []) if y.get('alive') == 0 and team.get(y['i']) == us)
    h = hunting(d, us, m)
    u, t = sides
    win = (d['outcome'] == 1) == (us == 0)
    causes = []
    if not win:
        if mono >= 5:
            causes.append('monolith')
        if (u['first_trib'] or 9999) > 600 and (t['first_trib'] or 9999) < 300:
            causes.append('no-bank')
        elif (u['first_trib'] or 9999) - (t['first_trib'] or 9999) >= 60 and t['curve'][500] > u['curve'][500]:
            causes.append('slow-start')
        if t['gpc'] and u['gpc'] < 0.7 * t['gpc']:
            causes.append('low-yield')
        if len(h) >= 8 and len(h) >= 2 * max(1, t['deaths'] - st[1 - us].get('deaths_to_camp', 0)):
            causes.append('fights')
        if u['lost'] >= 250:
            causes.append('gems-lost')
    fuel, faults = fuel_faults(livedir, v, us) if livedir else (None, None)
    return dict(fuel=fuel, faults=faults, opp=v['B'] if us == 0 else v['A'], map=v['map'], win=win, sub=(d['submitted'][us], d['submitted'][1 - us]),
                cap=(u['gems_cap'], t['gems_cap']), gpc=(u['gpc'], t['gpc']), ft=(u['first_trib'], t['first_trib']),
                deaths=(len(h), st[us].get('deaths_to_camp', 0), mono), lost=u['lost'],
                share2=sum(1 for x in h if x['hunters'] >= 2) / len(h) if h else 0, causes=causes or (['-'] if not win else []))


def main(livedir, exdir, n=5):
    sides = json.load(open(os.path.join(livedir, 'sides.json')))
    recent = sorted(sides.values(), key=lambda v: v['created'])[-int(n):]
    print('| time | kind | ver | opp | map | result | gems us-them | captured us/them | gems/capture | first tribute us/them | our deaths champ/camp/monolith | gems lost | 2v1 deaths | fuel-out turns / faults (ours) | cause |')
    print('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for v in recent:
        try:
            g = digest(exdir, v, livedir)
        except Exception as e:
            print(f"| {v['created'][11:16]} | {v['kind']} | {v['version']} | ? | {v['map']} | error {e} |")
            continue
        print(f"| {v['created'][11:16]} | {v['kind']} | {v['version']} | {g['opp'][:18]} | {g['map']} | {'W' if g['win'] else 'L'} | {g['sub'][0]}-{g['sub'][1]} | "
              f"{g['cap'][0]}/{g['cap'][1]} | {g['gpc'][0]:.1f}/{g['gpc'][1]:.1f} | {g['ft'][0]}/{g['ft'][1]} | {g['deaths'][0]}/{g['deaths'][1]}/{g['deaths'][2]} | "
              f"{g['lost']} | {100 * g['share2']:.0f}% | {g['fuel']} / {g['faults']} | {' '.join(g['causes'])} |")


if __name__ == '__main__':
    main(*sys.argv[1:])
