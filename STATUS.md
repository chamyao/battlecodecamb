# EC2 runner status

Updated 2026-10-24 07:15 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 21.85 22.36 20.40 on 16 threads.
Disk: 3.1G used of 38G.

## python3 processes
```
3284 python3 funsearch/t5_mapfix.py
5159 python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2
5462 python3 -m funsearch.league --name pure4 --budget 9.71 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --threads 
5473 /usr/bin/python3 -m funsearch.run --run pure4-g3 --budget 4.57 --max-programs 102 --seed-policy policies/fs-p2.policy --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/tune-3.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy --workers 3 
6766 python3 funsearch/draft_meta.py r1 9431 policies/tune5-reset.policy
7792 python3 funsearch/explore.py drafts 9471 400
12414 python3 -m funsearch.league --name style8-h --budget 3.95 --members policies/opp-hunter2b.policy --keep 0 --best-weight 0.5 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-campreset.policy,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2a.policy --regr
12424 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policie
12433 /usr/bin/python3 -m funsearch.run --run style8-h-g1 --budget 3.95 --max-programs 150 --seed-policy policies/opp-hunter2b.policy --opponents builtin:starter@0.25,policies/opp-hunter2b.policy@0.5,policies/tune5-campreset.policy,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunt
12435 python3 -m funsearch.league --name style8-a --budget 2.25 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,polici
12444 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 3.50 --max-programs 150 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
12446 python3 -m funsearch.league --name style8-c --budget 2.25 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,polici
12451 /usr/bin/python3 -m funsearch.run --run style8-a-g1 --budget 2.25 --max-programs 150 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
12461 /usr/bin/python3 -m funsearch.run --run style8-c-g1 --budget 2.25 --max-programs 150 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
```
## tick.log (last 40 lines)
```
[06:38:22] hybrid: launched hyb4 league
[06:38:23] hybrid: line script exited 1
[06:38:41] pure: setup ok at 81ab84b: 2012 passed in 5.60s; cambc 0.3625 ok; g3 programs.jsonl 49 lines; spent $5.14 (left $4.57)
[06:38:41] pure: launched pure4 league (g3)
[06:38:57] style: setup ok at funsearch/style 4f8ce7e: 2012 passed in 5.69s; budgets: a 0.9 b 0.5 c 0.6 
[06:38:57] style: launched style7-a (budget $0.9)
[06:38:57] style: launched style7-b (budget $0.5)
[06:38:58] style: launched style7-c (budget $0.6)
The following paths are ignored by one of your .gitignore files:
runs
hint: Use -f if you really want to add them.
hint: Turn this message off by running
hint: "git config advice.addIgnoredFile false"
[06:44:04] hybrid: resume check ok: [06:38:22] hyb4-g3: +0 programs to the next boundary (30 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', '
[06:44:05] hybrid: line script exited 1
[06:44:05] pure: resume check ok: [06:38:41] pure4-g3: +102 programs (to 151), best policies/fs-p2.policy, league ['policies/tune-3.policy', 'policies/v5d.policy', 'policies/v4.policy', 'policie
The following paths are ignored by one of your .gitignore files:
runs
hint: Use -f if you really want to add them.
hint: Turn this message off by running
hint: "git config advice.addIgnoredFile false"
[06:44:08] tune: stopped job D (superseded by D2)
[06:44:09] tune: started job D2: python3 funsearch/draft_meta.py r1 9431 policies/tune5-reset.policy > runs/tune/draftmeta-r1.out 2>&1
[06:44:09] tune: job D exited rc=superseded
[06:49:18] tune: started job E: python3 funsearch/explore.py drafts 9471 400 > runs/tune/explore-drafts.out 2>&1
[06:49:18] tune: started job F: python3 funsearch/explore.py switches > runs/tune/explore-switches.out 2>&1
[06:54:22] hybrid: U1: challenger tune5-campreset added; SPEND.md lines appended
[06:54:25] style: HOLD: SIGTERM style7-a pid 5780
[06:54:25] style: HOLD: SIGTERM style7-a pid 5799
[06:54:25] style: HOLD: SIGTERM style7-b pid 5790
[06:54:25] style: HOLD: SIGTERM style7-b pid 5803
[06:54:25] style: HOLD: SIGTERM style7-c pid 5801
[06:54:25] style: HOLD: SIGTERM style7-c pid 5813
[06:54:45] style: HOLD: style7 stopped; spend a/b/c: 0.02 0.017 0.007  a:8lines b:7lines c:5lines
[06:54:49] tune: job F exited rc=0
[07:10:25] style: style8 setup ok at 5c47501: gate 3, 2012 passed in 6.26s; budgets: h 3.95 b 3.5 a 2.25 c 2.25 
[07:10:25] style: launched style8-h (budget $3.95)
[07:10:25] style: launched style8-b (budget $3.5)
[07:10:25] style: launched style8-a (budget $2.25)
[07:10:25] style: launched style8-c (budget $2.25)
```
