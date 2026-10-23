"""Assign tournament teams to replay sides (A/B) by fingerprinting each team's draft per map.

All matches in Sprint 1's top 16 use the same 15 maps. A team's draft on a map is
(near-)stable across its matches, so for each game we pick the orientation whose
drafts agree best with the same teams' drafts on that map in their other matches.
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapinfo

README_TEAMS = {  # code: (team a, team b) from data/sprint1/README.md
    'w10-0': ('Intercontinental Fish', 'Nyx'), 'w9-0': ('Intercontinental Fish', 'Univardisty of Shingtonwash'),
    'w9-1': ('hello', 'Nyx'), 'w8-0': ('Intercontinental Fish', 'Tartarus'), 'w8-1': ('Univardisty of Shingtonwash', 'procless'),
    'w8-2': ('EMPEROR Tung', 'hello'), 'w8-3': ('Nyx', 'Sneaky Bush Campers'), 'w7-0': ('Intercontinental Fish', 'print dont int'),
    'w7-1': ('Tartarus', 'Sloppy Joe Pirates'), 'w7-2': ('Univardisty of Shingtonwash', 'Pantheon'), 'w7-3': ('procless', 'Boost'),
    'w7-4': ('Mite', 'EMPEROR Tung'), 'w7-5': ('hello', 'new team(4)'), 'w7-6': ('Nyx', 'Shawn'), 'w7-7': ('Sneaky Bush Campers', 'E=mc^2+AI^3'),
}


# Mirror drafts leave these games ambiguous; resolved by each team's opening purchases
# (Tung always opens Monster shards, Mite/Sneaky Bush Campers open Jungle shards), which
# also makes every series score match the bracket.
FLIP = {('w7-4', 3), ('w7-7', 8)}


def load_games(exdir):
    games = []
    for f in sorted(glob.glob(os.path.join(exdir, '*', '*.json'))):
        d = json.load(open(f))
        games.append(dict(code=f.split('/')[-2], n=int(os.path.basename(f)[:2]), path=f,
                          map=mapinfo.replay_map(d['file'])['sha'],
                          drafts=[tuple(x for x in d['drafts'][t] if x >= 0) for t in (0, 1)]))
    return games


def assign(games):
    # orient[g] = 0 means team a is side A
    orient = {id(g): 0 for g in games}
    for _ in range(10):
        changed = 0
        for g in games:
            ta, tb = README_TEAMS[g['code']]
            score = [0, 0]
            for h in games:
                if h is g or h['map'] != g['map']:
                    continue
                ha, hb = README_TEAMS[h['code']]
                o = orient[id(h)]
                hd = {ha: h['drafts'][o], hb: h['drafts'][1 - o]}
                for flip in (0, 1):
                    da, db = g['drafts'][flip], g['drafts'][1 - flip]
                    score[flip] += (hd.get(ta) == da) + (hd.get(tb) == db) - (hd.get(ta) == db) - (hd.get(tb) == da)
            best = 0 if score[0] >= score[1] else 1
            g['margin'] = abs(score[0] - score[1])
            if best != orient[id(g)]:
                orient[id(g)] = best; changed += 1
        if not changed:
            break
    for g in games:
        if (g['code'], g['n']) in FLIP:
            orient[id(g)] ^= 1
        ta, tb = README_TEAMS[g['code']]
        g['A'], g['B'] = (ta, tb) if orient[id(g)] == 0 else (tb, ta)
    return games


if __name__ == '__main__':
    games = assign(load_games(sys.argv[1]))
    out = {f"{g['code']}/{g['n']:02d}": dict(A=g['A'], B=g['B'], map=g['map'], margin=g['margin'], file=os.path.basename(g['path'])) for g in games}
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
    for k, v in out.items():
        print(k, v['map'], 'A=' + v['A'], '| B=' + v['B'], 'margin', v['margin'])
