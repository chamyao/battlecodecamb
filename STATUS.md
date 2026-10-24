# EC2 runner status

Updated 2026-10-24 13:15 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 9.87 10.01 11.46 on 16 threads.
Disk: 3.3G used of 38G.

## python3 processes
```
90564 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.p
92618 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
92630 /usr/bin/python3 -m funsearch.run --run pure4-g5 --budget 4.29 --max-programs 151 --seed-policy policies/fs-p3.policy --opponents builtin:starter@0.25,policies/fs-p3.policy@3.0,policies/tune-v20-L1c.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,polic
93083 /usr/bin/python3 -m funsearch.run --run hyb5-g3 --budget 20.13 --max-programs 30 --seed-policy policies/pool/v21.policy --opponents builtin:starter@0.25,policies/pool/v21.policy@3.0,policies/pool/v20.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.policy
93595 python3 -m funsearch.league --name style8-h2 --budget 2.2 --members policies/opp-hunter3.policy --keep 0 --best-weight 0.5 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune-v21.policy,policies/tune-v20.policy,policies/tune5-campreset.policy,policies/tune5-reset.policy,policies/
93608 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policie
93623 /usr/bin/python3 -m funsearch.run --run style8-h2-g1 --budget 0.70 --max-programs 39 --seed-policy policies/opp-hunter3.policy --opponents builtin:starter@0.25,policies/opp-hunter3.policy@0.5,policies/tune-v21.policy,policies/tune-v20.policy,policies/tune5-campreset.policy,policies/tune5-reset
93637 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 1.45 --max-programs 39 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hu
```
## tick.log (last 40 lines)
```
[11:46:15] style: style8-h2 not running: relaunching (resumes from its programs.jsonl)
[11:46:15] style: launched style8-h2 (budget $2.2)
[11:46:15] style: S6b check: h2: tune-v20 first in league best policies/opp-hunter3.policy $2.18 left
[12:01:42] hybrid: H5: SIGTERM hyb5 pid 65847
[12:01:59] hybrid: H5: funsearch/runs d0cbd58 (has d0cbd58), 2012 passed in 5.98s; v20 challenger queued; relaunching on v20
[12:01:59] hybrid: hyb5 not running: relaunching (resume from runs/)
[12:01:59] hybrid: launched hyb5 league
[12:17:26] hybrid: H6: hold set for the next hyb5 boundary
[12:17:26] hybrid: H5 check: no re-seed lines; v20 promoted at the boundary, new generation: [12:10:40]   PROMOTED challenger policies/pool/v20.policy: builtin:starter 99.2%, v19 55.6%, lean-g65 55.6%, v18 59.2%, opp-hunter3 71.9%, opp-hunter2|[12:10:40] hyb5-g2: +30 programs to the next boundary (0 so far), best policies/pool/v20.policy, league ['policies/pool/v19.policy', 'policies/pool/le|
[12:43:07] hybrid: H6: SIGTERM hyb5 pid 79363
[12:43:24] hybrid: H6+H7: funsearch/runs a43aede (has a43aede, 48a1404), 2012 passed in 5.95s; v21 challenger queued; relaunching on v21
[12:43:24] hybrid: hyb5 not running: relaunching (resume from runs/)
[12:43:24] hybrid: launched hyb5 league
[12:43:25] pure: pure: v21 opponent files from 0fcb030 (fixed from g6): policies/tune-v20-L1c.policy policies/v5d.policy policies/v4.policy policies/locker.policy policies/fs-2.policy policies/opp-hunter3.policy 
[12:43:26] style: S7: waiting for h2's boundary verdict (verdict lines so far: 1)
[12:48:33] hybrid: H7b: SIGTERM hyb5 pid 87162
[12:48:58] hybrid: H7b: funsearch/runs c4341a3 (has c4341a3: lockfix + fuel recalibration), rebuilt, 2012 passed in 5.87s; relaunching hyb5 (same v21 flags)
[12:48:58] hybrid: hyb5 not running: relaunching (resume from runs/)
[12:48:58] hybrid: launched hyb5 league
[12:54:08] hybrid: H7b check: hyb5-g2: +0 programs to the next boundary (30 so far) best policies/pool/v20.policy $20.13 left
[12:59:16] hybrid: H7c: SIGTERM hyb5 pid 88382
21
[12:59:31] hybrid: H7c: removed 21 stale-build validation cache entries (expected 21; backup validation_cache.jsonl.pre-h7c); relaunching hyb5
[12:59:31] hybrid: hyb5 not running: relaunching (resume from runs/)
[12:59:31] hybrid: launched hyb5 league
[13:04:40] pure: g6 build switch: STOP requested (gen 5)
[13:09:54] pure: g6 build switch: moved to funsearch/pure 0af36c4 (lockfix); g6 restarts on the new build
[13:09:54] pure: league not running: relaunching (g4, resume from runs/)
[13:09:54] pure: launched pure4 league (g4)
[13:15:01] hybrid: H7 check: no re-seed lines; v21 promoted at the boundary
[13:15:03] pure: resume check ok: [13:09:54] pure4-g5: +151 programs (to 151), best policies/fs-p3.policy, league ['policies/tune-v20-L1c.policy', 'policies/v5d.policy', 'policies/v4.policy', 'p
[13:15:04] style: S7: SIGTERM style8-h2 pid 75545
[13:15:04] style: S7: SIGTERM style8-h2 pid 93167
[13:15:04] style: S7: SIGTERM style8-b pid 43713
[13:15:04] style: S7: SIGTERM style8-b pid 43738
[13:15:20] style: S7: h2 verdict: [13:14:03]   no promotion; style8-h2-g1 continues; at 9fbc23f (has 3f7dae9), 2012 passed in 5.89s; h2 and b restarting below; promoted files kept: 
[13:15:20] style: style8-h2 not running: relaunching (resumes from its programs.jsonl)
[13:15:20] style: launched style8-h2 (budget $2.2)
[13:15:20] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[13:15:20] style: launched style8-b (budget $3.5)
```
