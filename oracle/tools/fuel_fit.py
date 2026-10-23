# Fit fuelprobe output: python3 oracle/tools/fuel_fit.py MAP... (reads /tmp/fp/MAP.txt from oracle/run_fuelprobe.sh)
import sys,collections,re
maps=sys.argv[1:]
data=collections.defaultdict(lambda: collections.defaultdict(list))  # name -> map -> [(n,cost)]
dims={}
for m in maps:
    for l in open(f'/tmp/fp/{m}.txt'):
        if l.startswith('@@dims') and m not in dims: dims[m]=l.split()[1:3]
        if l.startswith('@@F '):
            _,name,n,c=l.split(); data[name][m].append((int(n),int(c)-2))
def fit(pts):
    if len(set(n for n,_ in pts))<2: 
        cs=[c for _,c in pts]; return (min(cs),max(cs),None)
    xs=[n for n,_ in pts]; ys=[c for _,c in pts]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in pts)
    b=sxy/sxx; a=my-b*mx
    res=max(abs(y-(a+b*x)) for x,y in pts)
    return (a,b,res)
print("name".ljust(28)+"".join(f"{m}({'x'.join(dims[m])})".rjust(30) for m in maps))
for name in sorted(data):
    row=name.ljust(28)
    for m in maps:
        pts=data[name].get(m,[])
        if not pts: row+="-".rjust(30); continue
        a,b,res=fit(pts)
        if res is None: row+=(f"{a}" if a==b else f"{a}..{b}").rjust(30)
        else: row+=f"{a:.0f}+{b:.3f}n (±{res:.0f})".rjust(30)
    print(row)
