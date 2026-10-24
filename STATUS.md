# EC2 runner status

Updated 2026-10-24 08:34 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 16.82 15.33 14.64 on 16 threads.
Disk: 3.2G used of 38G.

## python3 processes
```
5462 python3 -m funsearch.league --name pure4 --budget 9.71 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --threads 
5473 /usr/bin/python3 -m funsearch.run --run pure4-g3 --budget 4.57 --max-programs 102 --seed-policy policies/fs-p2.policy --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/tune-3.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy --workers 3 
27961 python3 -m funsearch.league --name hyb4 --threads 5 --budget 29.47 --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2
29229 python3 -m funsearch.league --name style8-h --budget 3.95 --members policies/opp-hunter2b.policy --keep 0 --best-weight 0.5 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune-v19.policy,policies/tune-v18.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy,policies
29242 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policie
29257 /usr/bin/python3 -m funsearch.run --run style8-h-g2 --budget 3.32 --max-programs 34 --seed-policy policies/style-h1.policy --opponents builtin:starter@0.25,policies/style-h1.policy@0.5,policies/tune-v19.policy,policies/tune-v18.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy
29270 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 3.06 --max-programs 128 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
29566 python3 -m funsearch.league --name tune-fight --budget 5 --members policies/tune-v18g.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune-v18.policy --fixed policies/tune-v18.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policies/tune5-campreset.policy --regress 1.0 
29578 /usr/bin/python3 -m funsearch.run --run tune-fight-g1 --budget 5.00 --max-programs 60 --seed-policy policies/tune-v18g.policy --opponents builtin:starter@0.25,policies/tune-v18g.policy@3.0,policies/tune-v18.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policies/tune5-campres
```
## tick.log (last 40 lines)
```
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
[07:26:00] tune: job E exited rc=0
[07:36:16] style: S3: paused style8-a (SIGTERM pid 12435)
[07:36:16] style: S3: paused style8-a (SIGTERM pid 12451)
[07:36:16] style: S3: paused style8-c (SIGTERM pid 12446)
[07:36:16] style: S3: paused style8-c (SIGTERM pid 12461)
[07:36:16] style: S3: SIGTERM style8-h pid 12414
[07:36:16] style: S3: SIGTERM style8-h pid 12433
[07:36:31] style: S3: at 3d34e37; a and c paused (STOP files), h stopped and relaunching below, b untouched
[07:36:31] style: style8-h not running: relaunching (resumes from its programs.jsonl)
[07:36:31] style: launched style8-h (budget $3.95)
[07:36:32] style: S3 h check: tune-v18 in league; $3.93 left
[07:41:38] hybrid: g4 started: hold set for the g4 boundary upgrade
[07:46:53] tune: job C exited rc=0
[08:07:30] tune: job D2 exited rc=0
[08:23:09] hybrid: g4 boundary upgrade: funsearch/runs 4802e7b, 2012 passed in 6.07s; relaunching with --budget 29.47
[08:23:09] hybrid: league not running: relaunching (resume from runs/)
[08:23:09] hybrid: launched hyb4 league
[08:28:20] style: S4: SIGTERM style8-h pid 17790
[08:28:20] style: S4: SIGTERM style8-h pid 27479
[08:28:20] style: S4: SIGTERM style8-b pid 12424
[08:28:20] style: S4: SIGTERM style8-b pid 12444
[08:28:45] style: S4: at 1e5e1fc (has 05bb372: tune-v19 in h fixed), rebuilt, 2012 passed in 5.87s; left before: h 3.34 b 3.50; relaunching h and b
[08:28:45] style: style8-h not running: relaunching (resumes from its programs.jsonl)
[08:28:45] style: launched style8-h (budget $3.95)
[08:28:45] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[08:28:45] style: launched style8-b (budget $3.5)
[08:28:56] tune: G: tune/fs set up at 6cba5f0
[08:28:56] tune: G: launched tune-fight ($5)
[08:34:03] style: S4 check: h: g2 best style-h1 ok tune-v19 in league $3.32 left; b: style8-b-g1: +128 programs to the next boundary (22 so far) $3.06 left; before: h 3.34 b 3.50
```
