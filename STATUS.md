# EC2 runner status

Updated 2026-10-24 11:51 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 13.15 12.58 12.68 on 16 threads.
Disk: 3.3G used of 38G.

## python3 processes
```
40768 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
40780 /usr/bin/python3 -m funsearch.run --run pure4-g4 --budget 7.73 --max-programs 151 --seed-policy policies/fs-p2.policy --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/rall2-ca4-lean-g.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,p
43713 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policie
43738 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 2.60 --max-programs 106 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
65847 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.p
75396 /usr/bin/python3 -m funsearch.run --run hyb5-g1 --budget 21.34 --max-programs 30 --seed-policy policies/pool/v19.policy --opponents builtin:starter@0.25,policies/pool/v19.policy@3.0,policies/pool/lean-g65.policy,policies/pool/v18.policy,policies/pool/opp-hunter3.policy,policies/pool/opp-hunter
75545 python3 -m funsearch.league --name style8-h2 --budget 2.2 --members policies/opp-hunter3.policy --keep 0 --best-weight 0.5 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune-v20.policy,policies/tune-v19.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy,policies/
75565 /usr/bin/python3 -m funsearch.run --run style8-h2-g1 --budget 2.18 --max-programs 33 --seed-policy policies/opp-hunter3.policy --opponents builtin:starter@0.25,policies/opp-hunter3.policy@0.5,policies/tune-v20.policy,policies/tune-v19.policy,policies/tune5-campreset.policy,policies/tune5-reset
```
## tick.log (last 40 lines)
```
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
[10:23:16] tune: G2: stopped tune-fight pid 35865
[10:23:16] tune: G2: stopped tune-fight pid 46966
[10:23:16] tune: G2: tune/fs at de5dc62
[10:23:16] tune: G2: launched tune-fight2 ($2.25)
[10:48:59] hybrid: H4: hold set for the next hyb5 boundary
[11:04:30] hybrid: H4: SIGTERM hyb5 pid 37632
[11:04:46] hybrid: H4: funsearch/runs 4a08ddb (has 8c5b4e4), rebuilt, 2012 passed in 5.90s; relaunching hyb5 retuned
[11:04:46] hybrid: hyb5 not running: relaunching (resume from runs/)
[11:04:46] hybrid: launched hyb5 league
[11:09:57] hybrid: H4 check: 're-seeded island 3 with v19' x1 (expected 1), other islands re-seeded: 0
[11:10:03] tune: G2: tune-fight2 exited: [11:05:26] budget spent ($2.43)
[11:35:47] style: S6: at ace8582 (has 97e64e9), no rebuild; budgets: h 3.95 h2 2.2 b 3.5 a 0.04 c 2.25 
[11:35:47] style: style8-h exited: [11:31:47] budget spent ($3.95)
[11:35:47] style: launched style8-h2 (budget $2.2)
[11:40:54] pure: pure: v20 opponent files from 13f4e52 (fixed from g5): policies/tune-fight-2s.policy policies/v5d.policy policies/v4.policy policies/locker.policy policies/fs-2.policy policies/opp-hunter3.policy 
[11:40:56] style: S6 check: h2: g1 best opp-hunter3 ok tune-v19 in league $2.20 left; injected policies/opp-hunter-stack.policy
[11:46:02] hybrid: H5: hold set for the next hyb5 boundary
[11:46:05] style: S6b: SIGTERM style8-h2 pid 72978
[11:46:05] style: S6b: SIGTERM style8-h2 pid 72998
[11:46:15] style: S6b: at ace8582 (has ac873bb); h2 restarting below
[11:46:15] style: style8-h2 not running: relaunching (resumes from its programs.jsonl)
[11:46:15] style: launched style8-h2 (budget $2.2)
[11:46:15] style: S6b check: h2: tune-v20 first in league best policies/opp-hunter3.policy $2.18 left
```
