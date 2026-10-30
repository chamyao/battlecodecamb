import json, sys, glob, os
sys.path.insert(0, os.getcwd())
from genome.intel import sim_metrics as sm
S = sys.argv[1]
G = ['v40', 'x661', 'A11696', 'A11599', 'A11501', 'v43-fix3', 'A11976', 'A11791', 'x7-125']
O = ['v40', 'x661', 'v43']
maps = sorted(glob.glob(os.path.join(sm.ROOT, 'maps', '*.map26a')))
out = open(os.path.join(S, 'fitcheck.jsonl'), 'a')
for g in G:
    for o in O:
        for fm in (0.98, 1.0, 1.02):
            r = sm.metrics(sm.run(f'{S}/{g}.genome', f'{S}/{o}.genome', 0, maps, fm, bot_seeds=True))
            r.update(g=g, o=o, fm=fm)
            out.write(json.dumps(r) + '\n'); out.flush()
