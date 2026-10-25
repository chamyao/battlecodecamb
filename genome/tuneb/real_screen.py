"""Real-cambc screen: python3 genome/tuneb/real_screen.py SPEC.json OUT.jsonl REF_BOT [--text-base FILE] [--only TAG,...]
Each variant: edits applied to the text base (default tb.BASE), built under ~/ws/bots/tb-<hash> (genome/bot/sync.sh,
cambc build), played vs REF_BOT (already built) by real_gate.sh: 40 maps x 2 sides, --release. Replays are deleted
after the report is parsed; the report text is kept in OUT."""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, '.')
from genome.tuneb import tb
spec, out, ref = sys.argv[1], sys.argv[2], sys.argv[3]
text_base = open(sys.argv[sys.argv.index('--text-base') + 1]).read() if '--text-base' in sys.argv else tb.base_text()
only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
done = set()
if os.path.exists(out):
    done = {json.loads(l)['tag'] for l in open(out)}
WS = os.path.expanduser('~/ws')
for v in json.load(open(spec)):
    if v['tag'] in done or (only and v['tag'] not in only):
        continue
    t = text_base
    if v.get('order'):
        t = tb.with_draft(t, v['order'])
    if v.get('edits'):
        t = tb.edit(t, v['edits'])
    p = tb.save(t)
    bot = 'tb-' + os.path.basename(p)[:-7]
    subprocess.run([os.path.join(tb.ROOT, 'genome/bot/sync.sh'), p, os.path.join(WS, 'bots', bot)], check=True, capture_output=True)
    b = subprocess.run(['cambc', 'build', bot], cwd=WS, capture_output=True, text=True)
    if b.returncode:
        print(v['tag'], 'BUILD FAILED', b.stdout[-500:], b.stderr[-500:], flush=True)
        continue
    odir = os.path.join(tb.ROOT, 'genome/tuneb/runs/real', '%s-vs-%s' % (bot, ref))
    rep = subprocess.run([os.path.join(tb.ROOT, 'genome/tuneb/real_gate.sh'), bot, ref, '4'], capture_output=True, text=True,
                         env=dict(os.environ, OUT=odir)).stdout
    m = re.search(r'(\d+)/80 wins \((\d+) draws\)', rep)
    cr = [int(x) for x in re.findall(r'crashes (\d+)', rep)]
    cap = [int(x) for x in re.findall(r'normal turns >= 100k (\d+)', rep)]
    row = dict(tag=v['tag'], path=p, bot=bot, real=int(m.group(1)) if m else None, draws=int(m.group(2)) if m else None,
               crashes=cr[0] if cr else None, ref_crashes=cr[1] if len(cr) > 1 else None,
               capped=cap[0] if cap else None, ref_capped=cap[1] if len(cap) > 1 else None, report=rep)
    for f in os.listdir(odir):
        if f.endswith('.repl26a'):
            os.remove(os.path.join(odir, f))
    shutil.rmtree(os.path.join(WS, 'bots', bot, '.cambc'), ignore_errors=True)
    with open(out, 'a') as f:
        f.write(json.dumps(row) + '\n')
    print(v['tag'], row['real'], 'crashes', row['crashes'], 'capped', row['capped'], flush=True)
