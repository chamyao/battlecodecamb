"""deaths.py RUNDIR CAND : extract every replay in RUNDIR (A-*: CAND is team 0, B-*: team 1),
count deaths to champions per side, and dump per-death context to RUNDIR/deaths.json."""
import json, os, subprocess, sys, zipfile, glob
from multiprocessing import Pool
AN = '/tmp/claude-0/wt-an/analysis'

def ext(f):
    out = f[:-8] + '.json'
    if not os.path.exists(out):
        raw = f[:-8] + '.raw'
        z = zipfile.ZipFile(f); open(raw, 'wb').write(z.read('replay.repl26a'))
        subprocess.run(['node', AN + '/extract.js', raw, out], env=dict(os.environ, CAMBC_WASM=AN + '/engine/v2_0_0.wasm'),
                       capture_output=True)
        os.remove(raw)
    return f, out

def deaths(f, js):
    d = json.load(open(js)); side = os.path.basename(f)[0]; cteam = 0 if side == 'A' else 1
    team = {c['i']: c['team'] for c in d['champions']}; typ = {c['i']: c['type'] for c in d['champions']}
    R = {r[0]: r[3] for r in d['rounds']}
    rows = []
    for e in d['events']:
        dd = e.get('d', [])
        dead = [x['i'] for x in dd if x.get('alive') == 0 and 'p' in x and x['i'] in team]
        if not dead: continue
        killer = [x['i'] for x in dd if x.get('kills', 0) > 0 and x['i'] in team]
        for i in dead:
            r = e['r']; p = next(x['p'] for x in dd if x['i'] == i)
            prev = R.get(r - 1) or R.get(r - 2)
            def hp(k):
                s = R.get(r - k); return round(s[i][6] / s[i][7], 2) if s and s[i][7] else None
            al = en = 0
            if prev:
                for j, c in enumerate(prev):
                    if j == i or not c[2]: continue
                    if (c[4] - p[0]) ** 2 + (c[5] - p[1]) ** 2 <= 36:
                        if team[j] == team[i]: al += 1
                        else: en += 1
            gems = prev[i][1] if prev else None
            rows.append(dict(map=os.path.basename(f)[2:-8], side=side, round=r, cand=team[i] == cteam, type=typ[i],
                             by_champ=bool(killer), killer_type=typ[killer[0]] if killer else None, hp3=hp(3), hp10=hp(10),
                             allies6=al, enemies6=en, gems=gems, pos=p, winner_cand=None))
    # half-HP episodes: hp drops below 0.5 while alive; ends in death before recovering to 0.5
    ep = {True: [0, 0], False: [0, 0]}; caps = {True: 0, False: 0}
    for i in team:
        low = False
        for rr in d['rounds']:
            c = rr[3][i]
            if not c[2]:
                if low: ep[team[i] == cteam][1] += 1
                low = False; continue
            fr = c[6] / c[7] if c[7] else 1
            if not low and fr < 0.5: low = True; ep[team[i] == cteam][0] += 1
            elif low and fr >= 0.5: low = False
    for e in d['events']:
        if e['k'] == 'Capture':
            for x in e.get('d', []):
                if x['i'] in team: caps[team[x['i']] == cteam] += 1
    rows.append(dict(meta=True, ep=ep, caps=caps))
    return rows

if __name__ == '__main__':
    rd, cand = sys.argv[1:3]
    fs = sorted(glob.glob(rd + '/[AB]-*.repl26a'))
    with Pool(4) as p: pairs = p.map(ext, fs)
    rows = []
    for f, js in pairs:
        if os.path.exists(js): rows += deaths(f, js)
    meta = [r for r in rows if r.get('meta')]; rows = [r for r in rows if not r.get('meta')]
    E = {k: [sum(m['ep'][k][j] for m in meta) for j in (0, 1)] for k in (True, False)}
    K = {k: sum(m['caps'][k] for m in meta) for k in (True, False)}
    json.dump(rows, open(rd + '/deaths.json', 'w'))
    c = sum(r['by_champ'] and r['cand'] for r in rows); o = sum(r['by_champ'] and not r['cand'] for r in rows)
    cm = sum((not r['by_champ']) and r['cand'] for r in rows); om = sum((not r['by_champ']) and not r['cand'] for r in rows)
    print(f'{cand}: games {len(pairs)}  deaths to champions cand {c} / ref {o}   other deaths cand {cm} / ref {om}'
          f'   died after <50% HP cand {E[True][1]}/{E[True][0]} ({100*E[True][1]/max(1,E[True][0]):.0f}%) ref {E[False][1]}/{E[False][0]} ({100*E[False][1]/max(1,E[False][0]):.0f}%)'
          f'   captures cand {K[True]} / ref {K[False]}'
          f'   gems lost on death to champions cand {sum((r["gems"] or 0) for r in rows if r["by_champ"] and r["cand"])} / ref {sum((r["gems"] or 0) for r in rows if r["by_champ"] and not r["cand"])}')
