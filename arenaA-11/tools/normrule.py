"""normrule.py SEQ: reply = the request's rule gene with every 'if X > top' guard set to its branch's 'top = Y'
(tuned guards like 264 > top let a later rule override every earlier one) and pick 16 for the capture hold."""
import json, re, sys
u = json.load(open(f'/home/user/battlecodecamb/arenaA-11/queue/req-{sys.argv[1]}.json'))['user']
blk = re.search(r'## EDITABLE gene rule .*?\n```python\n(.*?)```', u, re.S).group(1)
def fix(m):
    return f"    if {m.group(3)} > top and{m.group(2)}\n        top = {m.group(3)}\n"
new = re.sub(r'    if (\d+) > top and(.*?)\n        top = (\d+)\n', fix, blk)
new = re.sub(r'(if 117 > top and r_hold\(\) and not threat_near\(\):\n        top = 117\n        pick = )15', r'\g<1>16', new)
if new == blk:
    sys.exit('no change')
new = new.replace("(ids 1-20, 20 always holds)", "(ids 1-20, 20 always holds); each guard matches its own priority", 1)
open(f'/home/user/battlecodecamb/arenaA-11/queue/rep-{sys.argv[1]}.txt', 'w').write('```python\n' + new + '```\n')
print('\n'.join(l for l in new.splitlines() if '> top' in l))
