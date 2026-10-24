import json,collections,math,sys
d=sys.argv[1]
M=[json.loads(l) for l in open(f"{d}/matches.jsonl")]
B={json.loads(l)["name"]:json.loads(l) for l in open(f"{d}/births.jsonl")}
C=[json.loads(l) for l in open(f"{d}/children.jsonl")]
FIX=["style-gconv1","tune-v20-L1","rall2-ca4-lean-g","v7","opp-tune5-metadraft"]
# per-genome per-opponent record (all opponents, incl. population)
rec=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0]))
for m in M:
    rec[m["a"]][m["b"]][0]+=m["a_wins"]; rec[m["a"]][m["b"]][1]+=m["games"]
    rec[m["b"]][m["a"]][0]+=m["games"]-m["a_wins"]; rec[m["b"]][m["a"]][1]+=m["games"]
# anchor-mix-adjusted strength: mean over fixed anchors of logit win rate (needs games vs all? use available, center by anchor)
glob={o:sum(rec[g][o][0] for g in B)/max(1,sum(rec[g][o][1] for g in B)) for o in FIX}
def lg(p): p=min(max(p,0.02),0.98); return math.log(p/(1-p))
def anc(g):
    s=n=0
    for o in FIX:
        w,k=rec[g][o]
        if k: s+=k*(lg((w+.5)/(k+1))-lg(glob[o])); n+=k
    return (s/n if n else None), n
# child vs parent head to head, and anchor-adjusted delta
ops=collections.defaultdict(list); h2h=collections.defaultdict(lambda:[0,0])
for name,b in B.items():
    if not b["parents"]: continue
    p=b["parents"][0]; key=b["op"]+("-"+b.get("model","").split("-")[1] if b.get("model") else "")
    w,k=rec[name][p]; h2h[key][0]+=w; h2h[key][1]+=k
    a,n=anc(name); pa,pn=anc(p)
    if a is not None and pa is not None and n>=24 and pn>=24: ops[key].append(a-pa)
print("op: births, child-vs-parent h2h, anchor-adjusted logit delta mean (n, sd/sqrt n)")
cnt=collections.Counter(b["op"]+("-"+b.get("model","").split("-")[1] if b.get("model") else "") for b in B.values())
for k in sorted(cnt):
    v=ops[k]; w,n=h2h[k]
    mu=sum(v)/len(v) if v else float('nan'); sd=(sum((x-mu)**2 for x in v)/max(1,len(v)-1))**.5 if v else 0
    print(f"{k:14s} {cnt[k]:4d}  h2h {w/max(1,n):.3f} ({n})  dAnc {mu:+.3f} ({len(v)}, se {sd/max(1,len(v))**.5:.3f})")
rej=collections.Counter((c["op"],c.get("error") or "ok") for c in C)
print(rej)
# genome sizes / lines changed
lc=collections.defaultdict(list)
for c in C:
    if c.get("accepted"): lc[c["op"]].append(c["log"].get("lines_changed",0))
print({k:(len(v),sum(v)/len(v)) for k,v in lc.items()})
# seed-equivalence: overall anchor-adjusted of seed and of best-measured genomes
L=sorted(((anc(g)[0],anc(g)[1],g) for g in B if anc(g)[0] is not None and anc(g)[1]>=80),reverse=True)
print("seed",anc("seed")); print("top by anchors (>=80 anchor games):",[(round(a,2),n,g) for a,n,g in L[:8]])
print("n genomes with >=80 anchor games",len(L), "mean", sum(a for a,_,_ in L)/len(L))
