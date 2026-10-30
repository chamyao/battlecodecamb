"""suggest.py SEQ...: for each pending request, find an earlier reply of mine that rewrites one of its editable genes
from the same body (gene id + canonical body match); print 'SEQ -> rep-K (gid)' or the compact view if none."""
import json, re, sys, glob, os, subprocess
sys.path.insert(0, '/home/user/battlecodecamb')
from genome.search import edit
Q = '/home/user/battlecodecamb/arenaA-11/queue'
def editable(u):
    out = {}
    for blk in re.findall(r'## EDITABLE gene \w+.*?\n```python\n(.*?)```', u, re.S):
        gid = re.search(r"@gene\(['\"]([^'\"]+)['\"]", blk).group(1)
        try: out[gid] = edit.body_canon(blk)
        except Exception: pass
    return out
lib = {}
for rp in sorted(glob.glob(f'{Q}/rep-*.txt'), key=lambda p: int(re.search(r'rep-(\d+)', p).group(1))):
    k = re.search(r'rep-(\d+)', rp).group(1); r = open(rp).read()
    rq = f'{Q}/req-{k}.json'
    if not os.path.exists(rq) or len(r) > 6000: continue
    ids = re.findall(r"@gene\(['\"]([^'\"]+)['\"]", r)
    if len(ids) != 1: continue
    src = editable(json.load(open(rq))['user'])
    if ids[0] in src: lib.setdefault((ids[0], src[ids[0]]), f'rep-{k}.txt')
rest = []
for s in sys.argv[1:]:
    q = json.load(open(f'{Q}/req-{s}.json'))
    if '## Link' not in q['user']:
        print(f'{s} CROSS'); continue
    hits = [(g, lib[(g, b)]) for g, b in editable(q['user']).items() if (g, b) in lib and g not in ('c0', 'v2')]
    if hits: print(f'{s} -> {hits[0][1]} ({hits[0][0]})  alt {[h[1] for h in hits[1:]]}')
    else: rest.append(s)
if rest:
    print(subprocess.run(['python3', '/home/user/battlecodecamb/arenaA-11/tools/v.py', *rest], capture_output=True, text=True).stdout)
