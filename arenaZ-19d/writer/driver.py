import json, os, subprocess, sys, time, glob, re
from concurrent.futures import ThreadPoolExecutor
Q = '/root/z19/queue'
def panel_from(req):
    fb = req['feedback']; top = [t[0] for t in fb.get('top5', [])]
    rated = sorted(fb.get('rated', []), key=lambda r: -r[1])
    extra = [r[0] for r in rated if r[0] not in top][:3]
    names = [n for n in top + extra if os.path.exists(f'/root/z19/runs/arenaZ-19d/arena/genomes/{n}.genome')]
    return ','.join(names[:8])
def handle(seq):
    req = json.load(open(f'{Q}/req-{seq}.json'))
    if os.path.exists(f'{Q}/rep-{seq}.txt'): return f'{seq} already'
    P = panel_from(req)
    try: os.remove(f'/root/w/d/{seq}.best')
    except FileNotFoundError: pass
    log = f'/root/w/logs/{seq}.log'
    with open(log, 'w') as f:
        subprocess.run(['python3', '/root/w/auto.py', str(seq), P, os.environ.get('GAMES', '12')], stdout=f, stderr=subprocess.STDOUT, env=dict(os.environ, CAP=os.environ.get('CAP', '5'), T='1'))
    if not os.path.exists(f'/root/w/d/{seq}.best'):
        open('/root/w/logs/MANUAL', 'a').write(f'{seq}\n'); return f'{seq} MANUAL'
    r = subprocess.run(['/root/w/wbest.sh', str(seq)], capture_output=True, text=True)
    return f'{seq} {r.stdout.strip()} ' + open(log).read().strip().splitlines()[-1]
os.makedirs('/root/w/logs', exist_ok=True)
while True:
    out = subprocess.run(['python3', '-m', 'genome.search.queuewait', Q, '--max', '8', '--timeout', '600'], capture_output=True, text=True, cwd='/root/z19')
    try: d = json.loads(out.stdout)
    except Exception: print('qw parse fail', out.stdout[-300:], out.stderr[-300:], flush=True); time.sleep(10); continue
    if isinstance(d, dict) and d.get('done'): print('DONE', flush=True); break
    seqs = [q['seq'] if isinstance(q, dict) else q for q in (d if isinstance(d, list) else d.get('requests', []))]
    seqs = [s for s in seqs if not os.path.exists(f'{Q}/rep-{s}.txt')]
    if not seqs: continue
    print(time.strftime('%H:%M:%S'), 'batch', seqs, flush=True)
    with ThreadPoolExecutor(2) as ex:
        for r in ex.map(handle, seqs): print(time.strftime('%H:%M:%S'), r, flush=True)
