"""Kill gold per game for our team: 100 per kill, +50 per kill while the killer owns a Hunter Str emblem (id 61).
Usage: python3 -I genome/intel/tools/killgold.py SCRATCH BATCH [BATCH ...]  (reads SCRATCH/BATCH and SCRATCH/BATCHx)"""
import json,os,sys
def kg(fd,ex):
    tot=[];bonus=[]
    for v in json.load(open(os.path.join(fd,'sides.json'))).values():
        p=os.path.join(ex,'ladder',v['file'])
        if not os.path.exists(p): continue
        d=json.load(open(p)); us=0 if v['A']=='Master' else 1
        team={c['i']:c['team'] for c in d['champions']}
        hunter={}
        for e in d['events']:
            if e['k']=='Shop':
                for x in e['d']:
                    for it,n in x.get('items',[]):
                        if it==61 and n>0: hunter.setdefault(x['i'],e['r'])
        R=d['rounds']; g=b=0
        for t in range(1,len(R)):
            for i,(a,c) in enumerate(zip(R[t-1][3],R[t][3])):
                if team[i]==us and c[3]>a[3]:
                    k=c[3]-a[3]; g+=100*k
                    if i in hunter and R[t][0]>=hunter[i]: g+=50*k; b+=50*k
        tot.append(g); bonus.append(b)
    n=len(tot); return sum(tot)/n, sum(bonus)/n, n
S=sys.argv[1]
for s in sys.argv[2:]:
    a,b,n=kg(S+'/'+s,S+'/'+s+'x'); print(f'{s}: kill gold/game {a:.0f} (hunter bonus {b:.0f}), {n} games')
