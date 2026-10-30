"""fixpick.py SEQ: reply = the request's rule gene with the unthreatened capture hold restored to pick 16."""
import json, re, sys
u = json.load(open(f'/home/user/battlecodecamb/arenaA-11/queue/req-{sys.argv[1]}.json'))['user']
blk = re.search(r'## EDITABLE gene rule .*?\n```python\n(.*?)```', u, re.S).group(1)
new = re.sub(r'(if 117 > top and r_hold\(\) and not threat_near\(\):\n        top = \d+\n        pick = )15', r'\g<1>16', blk)
assert new != blk
new = new.replace("(ids 1-20, 20 always holds)", "(ids 1-20, 20 always holds); an unthreatened capture hold is rule 16 (hold), not the monolith walk", 1)
open(f'/home/user/battlecodecamb/arenaA-11/queue/rep-{sys.argv[1]}.txt', 'w').write('```python\n' + new + '```\n')
print('fixed', sys.argv[1])
