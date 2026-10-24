# EC2 runner status

Updated 2026-10-24 09:41 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 18.64 16.97 15.45 on 16 threads.
Disk: 3.2G used of 38G.

## python3 processes
```
35865 python3 -m funsearch.league --name tune-fight --budget 5 --members policies/tune-v18g.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune-v18.policy --fixed policies/tune-v18.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policies/tune5-campreset.policy --regress 1.0 
37632 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.p
37639 /usr/bin/python3 -m funsearch.run --run hyb5-g1 --budget 25.00 --max-programs 30 --seed-policy policies/pool/v19.policy --opponents builtin:starter@0.25,policies/pool/v19.policy@3.0,policies/pool/lean-g65.policy,policies/pool/v18.policy,policies/pool/opp-hunter3.policy,policies/pool/opp-hunter
40768 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
40780 /usr/bin/python3 -m funsearch.run --run pure4-g4 --budget 7.73 --max-programs 151 --seed-policy policies/fs-p2.policy --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/rall2-ca4-lean-g.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,p
43700 python3 -m funsearch.league --name style8-h --budget 3.95 --members policies/opp-hunter2b.policy --keep 0 --best-weight 0.5 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune-v19.policy,policies/tune-v18.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy,policies
43713 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policie
43728 /usr/bin/python3 -m funsearch.run --run style8-h-g2 --budget 2.62 --max-programs 33 --seed-policy policies/style-h1.policy --opponents builtin:starter@0.25,policies/style-h1.policy@0.5,policies/tune-v19.policy,policies/tune-v18.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy
43738 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 2.60 --max-programs 106 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
```
## tick.log (last 40 lines)
```
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
[08:59:55] hybrid: H3: g4 verdict logged; STOP placed in runs/hyb4-g5, waiting for hyb4 to exit
[09:00:00] tune: G: restarting tune-fight on 45acc49 (pid 29566)
[09:00:00] tune: G: tune-fight not running: relaunching (resumes)
[09:00:00] tune: G: launched tune-fight ($5)
[09:05:05] hybrid: H3: hyb4 stopped. g4 verdict: [08:36:55]   #33: builtin:starter 0.973, hyb-t5m 0.511, tune-4 0.568, tune-1 0.682, v7-zerogem 0.792, locker 0.944, v7zg-cast 0.720, v8 0.724, v7zg-monozone 0.7|[08:44:09]   #29: builtin:starter 0.976, hyb-t5m 0.481, tune-4 0.527, tune-1 0.652, v7-zerogem 0.787, locker 0.946, v7zg-cast 0.713, v8 0.704, v7zg-monozone 0.7|[08:51:28]   #23: builtin:starter 0.976, hyb-t5m 0.486, tune-4 0.532, tune-1 0.649, v7-zerogem 0.787, locker 0.946, v7zg-cast 0.710, v8 0.700, v7zg-monozone 0.7|[08:58:41]   policies/tune5-campreset.policy: builtin:starter 0.974, hyb-t5m 0.710, tune-4 0.734, tune-1 0.774, v7-zerogem 0.869, locker 0.950, v7zg-cast 0.809,|[08:58:47]   PROMOTED challenger policies/tune5-campreset.policy: builtin:starter 97.4%, hyb-t5m 71.0%, tune-4 73.4%, tune-1 77.4%, v7-zerogem 86.9%, locker 95.|
[09:05:12] hybrid: H3: funsearch/runs 557ce2c (has 557ce2c), rebuilt, 2012 passed in 5.94s; SPEND lines appended; hyb5 launches next tick
[09:10:20] hybrid: launched hyb5 league
[09:15:29] hybrid: hyb5 check ok: [09:10:20] hyb5-g1: +30 programs to the next boundary (0 so far), best policies/pool/v19.policy, league ['poli; seeds:  2 seed v19;
[09:20:39] pure: g3 advance: STOP requested, waiting for the league to exit
[09:25:56] pure: g3 ended without promotion (best stays fs-p2); moved to funsearch/pure 2b65f8d for g4
[09:25:56] pure: league not running: relaunching (g4, resume from runs/)
[09:25:56] pure: launched pure4 league (g4)
[09:31:05] pure: resume check ok: [09:25:56] pure4-g4: +151 programs (to 151), best policies/fs-p2.policy, league ['policies/rall2-ca4-lean-g.policy', 'policies/v5d.policy', 'policies/v4.policy'
[09:36:17] style: S5: SIGTERM style8-h pid 29229
[09:36:17] style: S5: SIGTERM style8-h pid 41062
[09:36:17] style: S5: SIGTERM style8-b pid 29242
[09:36:17] style: S5: SIGTERM style8-b pid 29270
[09:36:42] style: S5: at e576e98 (has 88e3783: deploy/v0 merge, pair-farming h, fuel-gate b), rebuilt, 2012 passed in 5.86s; left before: h 2.65 b 3.06; relaunching h and b
[09:36:42] style: style8-h not running: relaunching (resumes from its programs.jsonl)
[09:36:42] style: launched style8-h (budget $3.95)
[09:36:42] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[09:36:42] style: launched style8-b (budget $3.5)
[09:36:42] style: S5 check: h: UNEXPECTED tune-v19 in league $2.62 left; b: style8-b-g1: +106 programs to the next boundary (44 so far) $2.60 left; before: h 2.65 b 3.06
```
