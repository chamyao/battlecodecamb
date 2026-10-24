# EC2 runner status

Updated 2026-10-24 14:23 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 11.83 10.27 10.25 on 16 threads.
Disk: 3.3G used of 38G.

## python3 processes
```
92618 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
92630 /usr/bin/python3 -m funsearch.run --run pure4-g5 --budget 4.29 --max-programs 151 --seed-policy policies/fs-p3.policy --opponents builtin:starter@0.25,policies/fs-p3.policy@3.0,policies/tune-v20-L1c.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,polic
103837 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.
104363 /usr/bin/python3 -m funsearch.run --run hyb5-g3 --budget 19.53 --max-programs 30 --seed-policy policies/pool/v21.policy --opponents builtin:starter@0.25,policies/pool/v21.policy@3.0,policies/pool/v20.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.polic
106865 python3 -m funsearch.run --run style8-gconv --budget 2.00 --max-programs 400 --seed-policy policies/tune-v21.policy --opponents builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraft.pol
106899 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,polici
106920 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 0.99 --max-programs 17 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
```
## tick.log (last 40 lines)
```
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
[13:20:32] style: S7 check: h2: tune-v21 first in league style8-h2-g1: +39 programs to the next boundary (81 so far) best policies/opp-hunter3.policy $0.70 left; b: style8-b-g1: +39 programs to the next boundary (111 so far) $1.45 left
[13:41:04] hybrid: H8: hold set for the next hyb5 boundary
[13:46:15] style: style8-h2 exited: [13:44:16] budget spent ($2.23)
[13:51:21] hybrid: H8: SIGTERM hyb5 pid 90564
[13:51:39] hybrid: H8: funsearch/runs fb401ce (has f31c3a4, 896fb6b), rebuilt, 2022 passed in 5.88s; relaunching hyb5 (disengage axis; seeds v21,v21,v20,v19-L1c; --tune-children)
[13:51:39] hybrid: hyb5 not running: relaunching (resume from runs/)
[13:51:39] hybrid: launched hyb5 league
[13:56:48] hybrid: H8b: SIGTERM hyb5 pid 101560 (drop --tune-* flags)
[13:57:03] hybrid: hyb5 not running: relaunching (resume from runs/)
[13:57:03] hybrid: launched hyb5 league
[14:07:16] hybrid: H9: SIGTERM hyb5 pid 102351
[14:07:38] hybrid: H9: funsearch/runs 41e1191 (has c6eb17a), 2024 passed in 6.46s; relaunching hyb5 with --tune-opponents (5)
[14:07:38] hybrid: hyb5 not running: relaunching (resume from runs/)
[14:07:38] hybrid: launched hyb5 league
[14:12:46] hybrid: H10: hold set for the next hyb5 boundary
[14:12:46] hybrid: H9 rate: 0 programs in 5 min = 0/h; tuned children 0, mean tuned.games 0 (round ended: [14:10:50]   no promotion; hyb5-g3 continues); before: g2 58/h, g3 49/h
[14:18:02] hybrid: H8 check: hyb5-g3: re-seeded island 2 with v20;hyb5-g3: re-seeded island 3 with v19-; (expected island 2 with v20, island 3 with v19-L1c; 0/1 keep v21)
[14:23:07] hybrid: H8 tune check: 3 programs carry metrics.tuned
[14:23:10] style: S8: SIGTERM style8-b pid 93608
[14:23:10] style: S8: SIGTERM style8-b pid 93637
[14:23:38] style: S8: at 834ac00 (has ed49293), rebuilt, 2012 passed in 5.87s; h2 and b restarting, gap run style8-gconv starting
[14:23:38] style: S8: launched style8-gconv ($2.0 total)
[14:23:38] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[14:23:38] style: launched style8-b (budget $3.5)
```
