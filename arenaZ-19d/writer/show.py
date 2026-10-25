import json, re, sys
d = json.load(open('/tmp/qw.json'))
for q in d:
    r = json.load(open(f"/root/z19/queue/req-{q['seq'] if isinstance(q, dict) else q}.json"))
    print(r['seq'], r['op'], r['parents'], re.findall(r'## Link\(s\) to mutate: (.*)', r['user']), re.findall(r'Current results: (.*)', r['user']))
fb = r['feedback']; print(json.dumps(fb)[:3000])
