"""Win rate vs the fixed anchors by birth cohort (fifths of birth index).

    python3 arenaa/cohort.py <arena dir with matches.jsonl, births.jsonl>
"""
import json,sys,collections
d=sys.argv[1]
M=[json.loads(l) for l in open(f"{d}/matches.jsonl")]
B={}
for l in open(f"{d}/births.jsonl"):
    r=json.loads(l); B[r["name"]]=r["birth"]
FIX=["style-gconv1","tune-v20-L1","rall2-ca4-lean-g","v7","opp-tune5-metadraft"]
nb=max(B.values()); K=5
cell=collections.defaultdict(lambda:[0,0])
per=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0]))
for m in M:
    for g,o,w in ((m["a"],m["b"],m["a_wins"]),(m["b"],m["a"],m["games"]-m["a_wins"])):
        if g in B and o in FIX:
            q=min(K-1,B[g]*K//(nb+1)); cell[(q,o)][0]+=w; cell[(q,o)][1]+=m["games"]
            per[g][o][0]+=w; per[g][o][1]+=m["games"]
print("by birth cohort (fifths of birth index):")
for o in FIX:
    print(f"{o:22s}"," ".join(f"{cell[(q,o)][0]/max(1,cell[(q,o)][1]):.2f}({cell[(q,o)][1]})" for q in range(K)))
s=per["seed"]; print("seed:",{o:(round(s[o][0]/s[o][1],2),s[o][1]) for o in FIX if s[o][1]})
