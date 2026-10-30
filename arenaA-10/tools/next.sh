cd ~/a10w
timeout 650 python3 -m genome.search.queuewait ~/a10w/queue --max 8 --timeout 600 > /tmp/qw.json
python3 -c "
import json,re;r=json.load(open('/tmp/qw.json'))
if isinstance(r,dict): print(r)
for q in r if isinstance(r,list) else []:
  u=q['user']; print(q['seq'], q['op'], q['parents'], re.findall(r'## Link\(s\) to mutate: (.*)', u)[:1] if q['op']=='mutate' else '', u.split('\n')[0][:60])
"
for s in $(python3 -c "import json;r=json.load(open('/tmp/qw.json'));print(' '.join(str(q['seq']) for q in (r if isinstance(r,list) else []) if q['op']=='mutate'))"); do
  echo "=== $s $(python3 tools/portgene.py $s | grep -o 'PORTED [a-z0-9]*' | tr '\n' ' ')"
  python3 tools/show.py $s | grep -v "^- " | awk '/^## EDITABLE/{p=1} p' | grep -v '^```\|^$' | awk '/^## EDITABLE gene (here|update) /{skip=1;print;next} /^## EDITABLE/{skip=0} !skip'
done
