"""Draft tally from a fetch_ladder.py matches.json (uses the draftPicks and engineVersion fields of the match list; no replays needed).
Usage: python3 -I genome/intel/tools/drafts.py OUT/matches.json"""
import json,collections,sys
DR=['Ryth','Vesper Vale','Vendetta','Cassi & Issac','Stellar','Prism','Marcella','Willow','Ren','Varg','Tavi','Heart of Ruin']
d=json.load(open(sys.argv[1]))
print('ladder:',[(t['rank'],t['name']) for t in d['ladder']])
def tally(ms,label):
    pick=collections.Counter();win=collections.Counter();n=0;first=collections.Counter()
    for m in ms:
        for t in m['teams']:
            n+=1
            for p in t['draftPicks']:
                pick[p]+=1; win[p]+= t['result']=='win'
            first[t['draftPicks'][0]]+=1
    print(label,'team-games',n)
    for p,c in pick.most_common(): print(f'  {DR[p]:14s} {c/n:5.0%} picked, win {win[p]/c:4.0%}, first-pick {first[p]}')
v2=[m for m in d['matches'] if all(t.get('engineVersion')=='2.0.0' for t in m['teams'])]
print(collections.Counter(t.get('engineVersion') for m in d['matches'] for t in m['teams']))
tally(v2,'engine 2.0.0')
print(collections.Counter(len(t['draftPicks']) for m in v2 for t in m['teams']))
per=collections.defaultdict(collections.Counter)
for m in v2:
    for t in m['teams']: per[t['name']][tuple(sorted(t['draftPicks']))]+=1
for k,v in per.items(): print(k, sum(v.values()), [('/'.join(DR[i] for i in s),c) for s,c in v.most_common(2)])
