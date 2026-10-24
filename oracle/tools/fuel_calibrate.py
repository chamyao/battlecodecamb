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
APIN=[]  # canonical API scope names: runs from different bot builds list them differently
OVH={}
samples=collections.defaultdict(list); loop=collections.defaultdict(list)
TURNS=collections.defaultdict(list)  # run -> [(turn_no, [(op, exp, dbits, occ)], blocks, api calls)]
for run in runs:
    mp=os.path.basename(run); tot=0
    for l in open(f'{run}/prof.txt'):
        f=l.split()
        if not f: continue
        if f[0]=='@@APINAMES':
            remap={}
            for i,nm in enumerate(f[1].split(',')):
                if nm not in APIN: APIN.append(nm)
                remap[1000+i]=1000+APIN.index(nm)
        elif f[0]=='@@T': tot=0; nsc=0; nblk=0; tno=int(f[1]); ops=[]
        elif f[0]=='@@S':
            op,sf,ex,db,cex,cdb,oc=map(int,f[1:8])
            if op in (509,510): continue  # the profiler's own calibration scopes, outside the turn
            op=remap.get(op,op)
            samples[op].append((mp,sf,ex+cex,db+cdb,oc)); tot+=sf; nsc+=1; nblk+=op<1000
            ops.append((op,ex+cex,db+cdb,oc))
        elif f[0]=='@@TURN':
            loop[run].append((int(f[1])-tot-nsc*OVH[run], nblk, int(f[1])-nsc*OVH[run]))
            TURNS[run].append((tno,ops,nblk,nsc-nblk))
        elif f[0]=='@@OVH': OVH[run]=int(f[1])
def name(op):
    if op>=1000: return "api:"+APIN[op-1000]
    return ("exec:" if op>=256 else "")+BLOCKS[op%256]
FEATS={'1':lambda f,e,d,o:1,'H':lambda f,e,d,o:f['H'],'ch':lambda f,e,d,o:f['ch'],'camps':lambda f,e,d,o:f['camps'],'groups':lambda f,e,d,o:f['groups'],
       'altars':lambda f,e,d,o:f['altars'],'exp*ch':lambda f,e,d,o:e*f['ch'],'exp':lambda f,e,d,o:e,'dbits':lambda f,e,d,o:d,'occ':lambda f,e,d,o:o,'occ*H':lambda f,e,d,o:o*f['H'],'occ*ch':lambda f,e,d,o:o*f['ch']}
def allowed(nm):
    # memoised in the bot (bot_api.cpp field_query): occ = memo misses, exp = layers searched
    if nm in ('api:distance_field','api:nearest_by_walk'): return ['1','ch','occ','occ*ch','exp*ch','dbits']
    if nm.endswith('_occupancy'): return ['1','H','ch']
    if nm=='api:visible_camps': return ['1','dbits']  # dbits = occupied camp tiles
    if nm.startswith('api:'): return ['1']
    if nm=='camps_visible()': return ['1','camps']
    if nm=='in_danger()': return ['1','camps']  # guest loop over every map camp (API calls are their own scopes)
    if nm=='capturable_spawns()': return ['1','groups','camps']
    if nm=='rich_spawns(Num)': return ['1','groups','camps','ch']  # static loop over groups and camps
    if nm=='group_tiles(TileSet)': return ['1','groups','camps','ch']  # static loop over groups and their camps
    if nm=='group_gems(TileSet)': return ['1','groups','camps','ch']  # static loop over groups and their camps
    if nm in ('group_threat(Tile)','group_hp(Tile)','group_rate(Tile)'): return ['1','camps']  # scan for the tile's camp (camp() calls are API scopes)
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
            if not hasx and any(x in ('exp*ch','exp','dbits','occ','occ*H','occ*ch') for x in sub): continue
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
 'draft_champion':'draft_champion','distance_field':'distance_field','nearest_by_walk':'nearest_by_walk',
 'visible_camps':'visible_camps','camp_state':'camp_state','vision':'vision','my_champion':'my_champion','my_team':'my_team'}
API_TERM={'1':'base','H':'per_row','ch':'per_chunk'}
BLOCK_TERMS=['1','H','ch','occ','occ*H','dbits','exp*ch','camps','groups','altars']

def fit_loop():
    """Step loop outside blocks (Value temporaries etc.) per turn ~ a + b*blocks + c*blocks*H, in
    profile fuel. Weighted for relative error per turn, each run counting equally: otherwise the
    expensive turns of every-turn coverage profiles set the constant and cheap turns are
    over-predicted."""
    rows=[(r,nb,F[os.path.basename(run)]['H'],1/max(t,1)/math.sqrt(len(loop[run]))) for run in runs for r,nb,t in loop[run]]
    xs=np.array([[1,nb,nb*H] for _,nb,H,_ in rows],float); ys=np.array([r for r,_,_,_ in rows],float)
    w=np.array([w for *_,w in rows])
    (a,b,c),*_=np.linalg.lstsq(xs*w[:,None],ys*w,rcond=None)
    return float(a),float(b),float(c),float(np.abs(xs@np.array([a,b,c])-ys).mean())
la_,lb_,lc_,lmae=fit_loop()

# ---- profiler distortion, fitted against the unpatched bot's real fuel ----
# The profiling build costs more than its measured per-scope overhead explains (its fuel probes
# around every block and API call get in the way of the compiler). run_bot_profile.sh also plays
# each game with the plain bot (identical decisions, so an identical game: checked on the
# opponent's per-turn fuel), and every champion logs on the same turns, so each logged round's
# model total can be compared with the plain bot's real fuel for that round:
#   real ~ s * model + h * blocks + g * API calls + d * turns
# The generated tables carry s on every fitted charge and h, g, d in the per-turn term.
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fuel_file import turns as fuel_turns
def predict(op,f,e,d,o):
    r=res.get(op)
    if r is None: return 0
    return sum(c*FEATS[t](f,e,d,o) for c,t in zip(r['coef'],r['feats']))
def plain_rounds(run):
    """[(real fuel, model, blocks, API calls, turns)] per fully logged champion round, or None."""
    import glob
    pz=glob.glob(f'{run}/*-vs-*.repl26a'); qz=glob.glob(f'{run}/plain/*-vs-*.repl26a')
    if not pz or not qz: return None
    if fuel_turns(pz[0],'team-b')[1]!=fuel_turns(qz[0],'team-b')[1]:
        print(f"warning: {run}: plain game differs from the profiled one; not used"); return None
    real=fuel_turns(qz[0])[1]; f=F[os.path.basename(run)]; T=TURNS[run]
    nd=1
    while nd<len(T) and T[nd][0]==T[nd-1][0]+1: nd+=1  # draft turns come first, numbered 1..nd
    champ=T[nd:]
    if not champ: return None
    C=sum(1 for t in champ if t[0]==champ[0][0])  # champion instances
    per={}
    for tno,ops,nb,na in champ:
        m=sum(predict(op,f,e,d,o) for op,e,d,o in ops)+la_+lb_*nb+lc_*nb*f['H']
        x=per.setdefault(tno,[0,0,0,0]); x[0]+=m; x[1]+=nb; x[2]+=na; x[3]+=1
    out=[]
    for tno,(m,nb,na,c) in sorted(per.items()):
        if c!=C or nd+C*tno>len(real): continue
        out.append((sum(real[nd+C*(tno-1):nd+C*tno]),m,nb,na,c))
    return out
# coverage.policy is a synthetic probe (dozens of extra blocks per turn): it prices blocks but its
# turns are unlike any real policy's, and fitting the correction on them moves real policies.
PLAIN={run:plain_rounds(run) for run in runs if os.path.basename(os.path.dirname(run))!='coverage'}
prow=[r for v in PLAIN.values() if v for r in v]
if prow:
    y=np.array([r[0] for r in prow],float); X=np.array([r[1:] for r in prow],float)
    w=1/np.maximum(y,1)
    (cs,ch,cg,cd),*_=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)
    cs,ch,cg,cd=float(cs),float(ch),float(cg),float(cd)
else:
    print("warning: no plain games (run_bot_profile.sh plays them); tables are in profile fuel")
    cs,ch,cg,cd=1.0,0.0,0.0,0.0


def generate():
    by_call={}
    for op,r in res.items():
        if op<1000: continue
        nm=r['name'][4:]
        c=API_CALL.get(nm)
        if not c or (c in by_call and by_call[c]['n']>=r['n']): continue
        by_call[c]=r
    hdr="// Generated by oracle/tools/fuel_calibrate.py from profiles of the deploy bot ("+", ".join(pols)+") on "+", ".join(maps)+"; do not edit."
    out=[hdr,"// Unprofiled calls keep the raw import price plus the median wrapper overhead below.",
         f"// Fitted prices carry the profiler-distortion scale {cs:.3f} (fuel_calibrate.py)."]
    raw_overhead=sorted(r['coef'][0] for c,r in by_call.items() if r['feats']==['1'])
    oh=raw_overhead[len(raw_overhead)//2]*cs if raw_overhead else 30
    out.append(f"for (int i = 0; i < static_cast<int>(Call::count); ++i) p.base[i] += {round(oh)};")
    out.append("p.base[static_cast<int>(Call::compute)] = p.base[static_cast<int>(Call::yield)] = 0; // not API calls")
    for c,r in sorted(by_call.items()):
        idx=f"static_cast<int>(Call::{c})"
        vals={'base':0,'per_row':0,'per_chunk':0,'per_n_milli':0,'per_n_chunk_milli':0,'per_n2_milli':0,'per_n3_milli':0,'per_n3_chunk_milli':0}
        for f,v in zip(r['feats'],r['coef']):
            v*=cs
            if f=='exp*ch': vals['per_n_chunk_milli']=round(v*1000)
            elif f=='exp': vals['per_n_milli']=round(v*1000)
            elif f=='dbits': vals['per_n2_milli']=round(v*1000)
            elif f=='occ': vals['per_n3_milli']=round(v*1000)  # memo misses (sim: field_memo.h)
            elif f=='occ*ch': vals['per_n3_chunk_milli']=round(v*1000)
            else: vals[API_TERM[f]]=round(v)
        out.append(f"// {r['name']}: n={r['n']} mean={r['mean']:.0f} mae={r['mae']:.0f} (profile fuel)")
        out.append(" ".join(f"p.{k}[{idx}] = {v};" for k,v in vals.items()))
    open(f'{REPO}/sim/src/fuel_bot_gen.inc','w').write("\n".join(out)+"\n")
    bl=[hdr,
        "// { block key, exec?, milli-fuel per term: 1, H, chunks, occupancy refreshes, refreshes*H, destination tiles,",
        f"//   expansions*chunks, camps, camp groups, input set tiles }}, with the profiler-distortion scale {cs:.3f}"]
    for op,r in sorted(res.items(),key=lambda kv:kv[1]['name']):
        if op>=1000 or op in (509,510): continue
        key=BLOCKS[op%256]; ex='true' if op>=256 else 'false'
        coef={f:v for f,v in zip(r['feats'],r['coef'])}
        terms=", ".join(str(round(coef.get(t,0)*cs*1000)) for t in BLOCK_TERMS)
        bl.append(f'{{ "{key}", {ex}, {{ {terms} }} }}, // n={r["n"]} mean={r["mean"]:.0f} mae={r["mae"]:.0f} (profile fuel)')
    bl.append(f"// Per turn: the step loop outside blocks (profile fit {la_:.0f} + {lb_:.2f}*blocks + {lc_:.3f}*blocks*H, mae {lmae:.0f}),")
    bl.append(f"// scaled by {cs:.3f}, plus the profiler-distortion terms per block, per API call and per turn.")
    bl.append(f"#define INTERP_TURN_COST(BLOCKS, H, API) ({round(cs*la_+cd)} + {round(cs*lb_+ch,2)} * (BLOCKS) + {round(cs*lc_,3)} * (BLOCKS) * (H) + {round(cg,2)} * (API))")
    open(f'{REPO}/interp/src/block_costs_gen.inc','w').write("\n".join(bl)+"\n")
    json.dump(dict(policies=pols,maps=F,ops={r['name']:dict(feats=r['feats'],coef=r['coef'],mae=r['mae'],mean=r['mean'],n=r['n']) for r in res.values()},
                   turn_loop_fit=[la_,lb_,lc_],turn_loop_mae=lmae,distortion=dict(scale=cs,per_block=ch,per_api=cg,per_turn=cd)),
              open(f'{REPO}/docs/fuel_calibration.json','w'),indent=1)
    print(f"wrote sim/src/fuel_bot_gen.inc ({len(by_call)} calls), interp/src/block_costs_gen.inc, docs/fuel_calibration.json")
    print(f"loop {la_:.0f}+{lb_:.1f}*blocks+{lc_:.3f}*blocks*H (mae {lmae:.0f}); real = {cs:.3f}*model {ch:+.1f}*blocks {cg:+.1f}*api {cd:+.0f}*turns ({len(prow)} rounds)")

if __name__=="__main__":
    for op,r in sorted(res.items(),key=lambda kv:-kv[1]['mean']*kv[1]['n']):
        print(f"{r['name'][:34]:34s} n={r['n']:5d} mean={r['mean']:8.0f} mae={r['mae']:6.0f}  "+" + ".join(f"{c:g}*{f}" for c,f in zip(r['coef'],r['feats'])))
    generate()
