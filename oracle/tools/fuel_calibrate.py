"""Calibrate the simulator's fuel model to the deploy bot's real fuel.

Input: profile directories from oracle/run_bot_profile.sh (/tmp/prof/POLICY/MAP, holding prof.txt;
the map is the directory name), pooled across policies. Fits, per interpreter
block and per bot API wrapper, a linear model of the measured self fuel on features the
simulator can compute (map rows H and 8x8 chunks; BFS expansions and destination tiles; whether
the block refreshed the occupancy cache; camp/group counts; input set size), and writes:
  sim/src/fuel_bot_gen.inc         PriceTable::bot_wrapper() (API calls as made by bot_api.cpp)
  interp/src/block_costs_gen.inc   per-block self costs for the interpreter
  docs/fuel_calibration.json       the fits, errors and sample counts
Usage: python3 oracle/tools/fuel_calibrate.py /tmp/prof/*/*
"""
import sys,re,collections,json,math,itertools
import numpy as np, os
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src=open(REPO+'/interp/src/policy.cpp').read()
m=src[src.index("#define INTERP_BLOCKS(X)"):src.index("enum class Op")]
BLOCKS=re.findall(r'X\(\w+,\s*"([^"]+)"\)',m)
runs=[d.rstrip('/') for d in sys.argv[1:]]
maps=sorted({os.path.basename(d) for d in runs})
pols=sorted({os.path.basename(os.path.dirname(d)) for d in runs})
def mfeat(mp):
    d=json.load(open(f'{REPO}/oracle/fixtures/maps/{mp}.json'))
    W,H=d['metadata']['width'],d['metadata']['height']
    alt=bytes.fromhex(d['masks']['altars'])
    return dict(H=H,W=W,ch=math.ceil(W/8)*math.ceil(H/8),camps=sum(len(g['camps']) for g in d['camp_layout']),
                groups=len(d['camp_layout']),altars=sum(bin(b).count('1') for b in alt))
F={mp:mfeat(mp) for mp in maps}
APIN=None
OVH={}
samples=collections.defaultdict(list); loop=collections.defaultdict(list)
for run in runs:
    mp=os.path.basename(run); tot=0
    for l in open(f'{run}/prof.txt'):
        f=l.split()
        if not f: continue
        if f[0]=='@@APINAMES': APIN=f[1].split(',')
        elif f[0]=='@@T': tot=0; nsc=0; nblk=0
        elif f[0]=='@@S':
            op,sf,ex,db,cex,cdb,oc=map(int,f[1:8])
            if op in (509,510): continue  # the profiler's own calibration scopes, outside the turn
            samples[op].append((mp,sf,ex+cex,db+cdb,oc)); tot+=sf; nsc+=1; nblk+=op<1000
        elif f[0]=='@@TURN': loop[run].append((int(f[1])-tot-nsc*OVH[run], nblk, int(f[1])-nsc*OVH[run]))
        elif f[0]=='@@OVH': OVH[run]=int(f[1])
def name(op):
    if op>=1000: return "api:"+APIN[op-1000]
    return ("exec:" if op>=256 else "")+BLOCKS[op%256]
FEATS={'1':lambda f,e,d,o:1,'H':lambda f,e,d,o:f['H'],'ch':lambda f,e,d,o:f['ch'],'camps':lambda f,e,d,o:f['camps'],'groups':lambda f,e,d,o:f['groups'],
       'altars':lambda f,e,d,o:f['altars'],'exp*ch':lambda f,e,d,o:e*f['ch'],'exp':lambda f,e,d,o:e,'dbits':lambda f,e,d,o:d,'occ':lambda f,e,d,o:o,'occ*H':lambda f,e,d,o:o*f['H']}
def allowed(nm):
    if nm=='api:distance_field': return ['1','H','ch','exp*ch','dbits']
    if nm.endswith('_occupancy'): return ['1','H','ch']
    if nm.startswith('api:'): return ['1']
    if nm=='camps_visible()': return ['1','camps']
    if nm=='respawning_visible_spawns()': return ['1','groups']
    if nm in ('ring(TileSet,Num)','filter(TileSet,TilePred)','first(TileSet)','count(TileSet)'): return ['1','H','altars']
    return ['1','H','ch','occ','occ*H','dbits','exp*ch']
res={}
for op,v in samples.items():
    y=np.array([s for _,s,_,_,_ in v],float)
    hasx=any(e or d or o for _,_,e,d,o in v)
    best=None
    for k in (1,2,3,4,5):
        for sub in itertools.combinations(allowed(name(op)),k):
            if sub[0]!='1': continue
            if not hasx and any(x in ('exp*ch','exp','dbits','occ','occ*H') for x in sub): continue
            A=np.array([[FEATS[n](F[mp],e,d,o) for n in sub] for mp,_,e,d,o in v],float)
            coef,*_=np.linalg.lstsq(A,y,rcond=None)
            if (coef[1:]<-1e-6).any(): continue
            err=np.abs(A@coef-y).mean()
            score=err+0.002*abs(y.mean())*k+1*k
            if best is None or score<best[0]: best=(score,sub,coef,err)
    _,sub,coef,err=best
    res[op]=dict(name=name(op),feats=list(sub),coef=[round(float(c),3) for c in coef],mae=float(err),mean=float(y.mean()),n=len(y))

# Bot API wrapper -> simulator Call (cbs::Call enumerator names).
API_CALL={'champion':'champion','allies':'allies','enemies':'enemies','champion_gems':'champion_gems','champion_gold':'champion_gold',
 'champion_cooldown':'champion_cooldown','champion_consumables':'champion_consumables','champion_ability_props':'champion_ability_props',
 'camp':'camp','camp_group_state':'camp_group_state','altar_locks':'altar_locks','submitted_gems':'submitted_gems','round_number':'round_number',
 'ally_occupancy':'occupancy','enemy_occupancy':'occupancy','camp_occupancy':'occupancy','read_shared_memory':'read_shared_memory',
 'write_shared_memory':'write_shared_memory','read_draft_memory':'read_draft_memory','submit_draft_memory':'submit_draft_memory',
 'move_to':'move_to','attack':'attack','cast':'cast','buy_item':'buy_item','buy_consumable':'buy_consumable','use_consumable':'use_consumable',
 'recall':'recall','submit_gems':'submit_gems','place_ward':'place_ward','set_priority':'set_priority','draft_get':'draft_get',
 'draft_champion':'draft_champion','distance_field':'distance_field'}
API_TERM={'1':'base','H':'per_row','ch':'per_chunk'}
BLOCK_TERMS=['1','H','ch','occ','occ*H','dbits','exp*ch','camps','groups','altars']

def generate():
    by_call={}
    for op,r in res.items():
        if op<1000: continue
        nm=r['name'][4:]
        c=API_CALL.get(nm)
        if not c or (c in by_call and by_call[c]['n']>=r['n']): continue
        by_call[c]=r
    out=["// Generated by oracle/tools/fuel_calibrate.py from profiles of the deploy bot ("+", ".join(pols)+") on "+", ".join(maps)+"; do not edit.",
         "// Unprofiled calls keep the raw import price plus the median wrapper overhead below."]
    raw_overhead=sorted(r['coef'][0] for c,r in by_call.items() if r['feats']==['1'])
    oh=raw_overhead[len(raw_overhead)//2] if raw_overhead else 30
    out.append(f"for (int i = 0; i < static_cast<int>(Call::count); ++i) p.base[i] += {round(oh)};")
    for c,r in sorted(by_call.items()):
        idx=f"static_cast<int>(Call::{c})"
        vals={'base':0,'per_row':0,'per_chunk':0,'per_n_milli':0,'per_n_chunk_milli':0,'per_n2_milli':0}
        for f,v in zip(r['feats'],r['coef']):
            if f=='exp*ch': vals['per_n_chunk_milli']=round(v*1000)
            elif f=='exp': vals['per_n_milli']=round(v*1000)
            elif f=='dbits': vals['per_n2_milli']=round(v*1000)
            else: vals[API_TERM[f]]=round(v)
        out.append(f"// {r['name']}: n={r['n']} mean={r['mean']:.0f} mae={r['mae']:.0f}")
        out.append(" ".join(f"p.{k}[{idx}] = {v};" for k,v in vals.items()))
    open(f'{REPO}/sim/src/fuel_bot_gen.inc','w').write("\n".join(out)+"\n")
    bl=["// Generated by oracle/tools/fuel_calibrate.py from profiles of the deploy bot ("+", ".join(pols)+") on "+", ".join(maps)+"; do not edit.",
        "// { block key, exec?, milli-fuel per term: 1, H, chunks, occupancy refreshes, refreshes*H, destination tiles,",
        "//   expansions*chunks, camps, camp groups, input set tiles }"]
    for op,r in sorted(res.items(),key=lambda kv:kv[1]['name']):
        if op>=1000 or op in (509,510): continue
        key=BLOCKS[op%256]; ex='true' if op>=256 else 'false'
        coef={f:v for f,v in zip(r['feats'],r['coef'])}
        terms=", ".join(str(round(coef.get(t,0)*1000)) for t in BLOCK_TERMS)
        bl.append(f'{{ "{key}", {ex}, {{ {terms} }} }}, // n={r["n"]} mean={r["mean"]:.0f} mae={r["mae"]:.0f}')
    open(f'{REPO}/interp/src/block_costs_gen.inc','w').write("\n".join(bl)+"\n")
    # step loop outside blocks (Value temporaries etc.) per turn ~ a + b*blocks + c*blocks*H
    # Weighted for relative error per turn, each run counting equally: otherwise the expensive
    # turns of every-turn coverage profiles set the constant and cheap turns are over-predicted.
    rows=[(r,nb,F[os.path.basename(run)]['H'],1/max(t,1)/math.sqrt(len(loop[run]))) for run in runs for r,nb,t in loop[run]]
    xs=np.array([[1,nb,nb*H] for _,nb,H,_ in rows],float); ys=np.array([r for r,_,_,_ in rows],float)
    w=np.array([w for *_,w in rows])
    (a,b,c),*_=np.linalg.lstsq(xs*w[:,None],ys*w,rcond=None)
    lmae=float(np.abs(xs@np.array([a,b,c])-ys).mean())
    with open(f'{REPO}/interp/src/block_costs_gen.inc','a') as f:
        f.write(f"// step loop outside blocks, per turn: mae {lmae:.0f} on mean {ys.mean():.0f}\n")
        f.write(f"#define INTERP_TURN_COST(BLOCKS, H) ({round(a)} + {round(b,2)} * (BLOCKS) + {round(c,3)} * (BLOCKS) * (H))\n")
    json.dump(dict(policies=pols,maps=F,ops={r['name']:dict(feats=r['feats'],coef=r['coef'],mae=r['mae'],mean=r['mean'],n=r['n']) for r in res.values()},
                   turn_loop_fit=[float(a),float(b),float(c)],turn_loop_mae=lmae),
              open(f'{REPO}/docs/fuel_calibration.json','w'),indent=1)
    print(f"wrote sim/src/fuel_bot_gen.inc ({len(by_call)} calls), interp/src/block_costs_gen.inc, docs/fuel_calibration.json; loop {a:.0f}+{b:.1f}*blocks+{c:.3f}*blocks*H (mae {lmae:.0f})")

if __name__=="__main__":
    for op,r in sorted(res.items(),key=lambda kv:-kv[1]['mean']*kv[1]['n']):
        print(f"{r['name'][:34]:34s} n={r['n']:5d} mean={r['mean']:8.0f} mae={r['mae']:6.0f}  "+" + ".join(f"{c:g}*{f}" for c,f in zip(r['coef'],r['feats'])))
    generate()

