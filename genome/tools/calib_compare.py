import re,zipfile,glob,json
def rd(lines):
    rows={}
    for l in lines:
        m=re.search(r'@@GENE r(\d+) (\w+) calls (\d+) fuel (-?\d+)',l)
        if m and int(m.group(3))>0: rows[m.group(2)]=int(m.group(4))/int(m.group(3))   # latest cumulative
    b=rows['p_empty']; return {k[2:]:v-b for k,v in rows.items() if k.startswith('p_')}
out={}
for M in ['00ambush','01big-world','00lanes']:
    s=rd(open(f'/tmp/claude-0/simcal-{M}.txt'))
    z=zipfile.ZipFile(glob.glob(f'/tmp/claude-0/calib-{M}/*.repl26a')[0]); r=rd(z.read('team-a.stdout').decode(errors='replace').split('\n'))
    out[M]={k:(r[k],s.get(k)) for k in r}
    print(M); print('  '+' '.join(f"{k}:{r[k]:.0f}/{s.get(k,0):.0f}" for k in r))
json.dump(out,open('/tmp/claude-0/calcmp.json','w'))
