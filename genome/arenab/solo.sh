#!/bin/bash
# solo.sh BOT : 70 maps x 2 vs genome idle; prints total rounds, losses, new slow games vs v40 (gsolo-x6-83)
S=/tmp/claude-0/-home-user-battlecodecamb/ffe54acc-bdb7-57df-a68a-1cdbcfbc6770/scratchpad; R=$S/cambc4/runs; D=$R/gsolo-$1; mkdir -p $D
rm -f $D/*.repl26a
sed "s#bots/x6-83 #bots/$1 #g; s#bots/x6-83\$#bots/$1#g; s#gsolo-x6-83#gsolo-$1#g" $R/gsolo-x6-83/m.txt > $D/m.txt
(cd $S/cambc4/ws4 && $S/cambc4/venv/bin/cambc run-batch --release --jobs 4 --timeout 1800 $D/m.txt > $D/batch.log 2>&1)
python3 - $R $1 ${2:-x6-83} <<'PY'
import re,sys
R,b=sys.argv[1:3]
def rd(n):
    d={}
    for l in open(f"{R}/{n}/batch.log"):
        m=re.search(r"(WIN \((\S+)\)|DRAW)\s+(\S+) vs (\S+)\s+(\S+)\s+Round (\d+)",l)
        if m: d[(m[5],'A' if m[3]!='gidle' else 'B')]=(int(m[6]),m[2])
    return d
v=rd("gsolo-"+sys.argv[3]); j=rd("gsolo-"+b)
print(b,"solo games",len(j),"total",sum(x[0] for x in j.values()),"(v40",sum(x[0] for x in v.values()),") losses",[k for k,x in j.items() if x[1]!=b])
for k in sorted(j):
    if k in v and j[k][0]>=1800 and j[k][0]-v[k][0]>150: print("  new slow",k,j[k][0],"v40",v[k][0])
PY
