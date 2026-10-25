import sys, json; sys.path.insert(0, '/root/w')
import auto
s = int(sys.argv[1]); name = sys.argv[2]
r = json.load(open(f'/root/z19/queue/req-{s}.json'))
cs = dict(auto.cross_candidates(s) if 'mutate one link' not in r['system'] else auto.candidates(s))
open(f'/root/w/d/{s}.txt', 'w').write("```python\n" + cs[name] + "```\n")
open(f'/root/w/d/{s}.best', 'w').write(f'/root/w/d/{s}.{name.replace(":", "_").replace("+", "_").replace(".", "_")}.txt')
print(s, name)
