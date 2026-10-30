#!/bin/bash
# mirror the run to arenaa/a11-mirror (arena state, queue, candidates, logs; matches.jsonl excluded)
cd /home/user/battlecodecamb
cp arenaA-11/arena/log.txt arenaA-11/arenaA-11.log 2>/dev/null
git add -A arenaA-11 >/dev/null 2>&1
b=$(python3 -c "import json;print(json.load(open('arenaA-11/arena/state.json'))['births'])")
git commit -qm "arenaA-11 mirror: $b births

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H75at7s2GPNPWtwopowYqq" && for i in 2 4 8 16; do git push -q -u origin arenaa/a11-mirror 2>&1 && break; sleep $i; done
git log --oneline -1
