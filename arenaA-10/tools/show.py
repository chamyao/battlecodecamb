import json,re,sys
q=json.load(open(f'/root/a10w/queue/req-{sys.argv[1]}.json')); u=q['user']
print(q['seq'], q['op'], q['parents'], u.split('\n')[0]); print(re.findall(r'## Link\(s\) to mutate: (.*)', u))
i=u.find('## EDITABLE'); print(u[i:u.rfind('Write the mutation')])
