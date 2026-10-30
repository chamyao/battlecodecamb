#!/bin/bash
# leg-3 batch: wait, suggest, apply survival-safe suggestions (aggressive replies excluded; a9 -> v40's a9), list the rest
cd /home/user/battlecodecamb/arenaA-11
bash tools/next.sh 8 ${1:-60} > /tmp/next.txt
S=$(python3 -c "import json;r=json.load(open('/tmp/qw.json'));print(' '.join(str(q['seq']) for q in r) if isinstance(r,list) else '')")
python3 tools/suggest.py $S > /tmp/sug.txt 2>/dev/null
python3 - <<'PY'
import re, shutil
Q = '/home/user/battlecodecamb/arenaA-11/queue'
BAD = {'60', '9', '31', '162', '2', '745', '41', '732', '823', '33', '96', '252', '30', '35', '1010', '612', '934', '1121', '1050'}
rest = []
for l in open('/tmp/sug.txt'):
    m = re.match(r'(\d+) -> rep-(\d+)\.txt \((\S+)\)\s+alt (.*)', l)
    if m:
        s, k, gid, alt = m.groups()
        if gid == 'd1':
            shutil.copy(f'{Q}/v40d1.txt', f'{Q}/rep-{s}.txt'); print(s, 'd1->v40'); continue
        if gid == 'a9':
            shutil.copy(f'{Q}/v40a9.txt', f'{Q}/rep-{s}.txt'); print(s, 'a9->v40'); continue
        cands = [k] + re.findall(r'rep-(\d+)', alt)
        ok = [c for c in cands if c not in BAD]
        if ok:
            shutil.copy(f'{Q}/rep-{ok[0]}.txt', f'{Q}/rep-{s}.txt'); print(s, '->', ok[0])
        else:
            open(f'{Q}/rep-{s}.txt', 'w').write('```python\n```\n'); print(s, 'empty (aggressive)')
    elif re.match(r'\d+ CROSS', l):
        rest.append(l.split()[0] + ' CROSS')
    elif l.startswith('#####'):
        rest.append(l.split()[1])
print('MANUAL', ' '.join(rest))
PY
grep -E "^## Link" /tmp/sug.txt
tail -1 arena/log.txt | cut -c1-160
