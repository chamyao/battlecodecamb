# EC2 runner status

Updated 2026-10-24 15:05 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 14.50 13.89 12.96 on 16 threads.
Disk: 3.4G used of 38G.

## python3 processes
```
92618 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
92630 /usr/bin/python3 -m funsearch.run --run pure4-g5 --budget 4.29 --max-programs 151 --seed-policy policies/fs-p3.policy --opponents builtin:starter@0.25,policies/fs-p3.policy@3.0,policies/tune-v20-L1c.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,polic
112760 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,polici
112781 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 0.97 --max-programs 12 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-h
114024 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.
114076 /usr/bin/python3 -m funsearch.run --run hyb5-g3 --budget 18.75 --max-programs 28 --seed-policy policies/pool/v21.policy --opponents builtin:starter@0.25,policies/pool/v21.policy@3.0,policies/pool/v20.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.polic
117552 python3 -m funsearch.run --run style8-gconv --budget 1.76 --max-programs 400 --seed-policy policies/tune-v21.policy --opponents builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraft.pol
```
## tick.log (last 40 lines)
```
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
[14:28:46] style: S8 gap line: gap metric conversion (max, scale 0.05): reference tune-v21 mirror value 0.9034; win floor 0.5 vs it; weight 0.5
[14:33:55] style: S8 HOLD: SIGTERM style8-gconv pid 106865
[14:34:00] style: S8 HOLD: gconv stopped; spend $0.019 over 8 lines
[14:49:24] style: S9: SIGTERM pid 106899
[14:49:24] style: S9: SIGTERM pid 106920
[14:49:50] style: S9: at ec8c33d (has 6e8cc17), rebuilt, 2024 passed in 6.17s; restarting b, releasing gconv
[14:49:50] style: S8: style8-gconv not running: relaunching (resumes)
[14:49:50] style: S8: launched style8-gconv ($2.0 total)
[14:49:50] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[14:49:50] style: launched style8-b (budget $3.5)
[14:54:56] hybrid: H10: SIGTERM hyb5 pid 103837
[14:55:21] hybrid: H10: funsearch/runs 6646329 (has 7a6038d, 6646329: H10-H15: gap sensors, vocab variant, exec_blocks refresh, calibrated fuel), rebuilt, 2028 passed in 7.16s; relaunching hyb5 with the weighted axis menu and --helpers-runs
[14:55:21] hybrid: hyb5 not running: relaunching (resume from runs/)
[14:55:21] hybrid: launched hyb5 league
[14:55:24] style: S9 check: $1.98 left of $2.0; reference tune-v21 mirror value 0.8999
[15:00:29] hybrid: H10 startup check: 'exec_blocks vs starter for 65 programs (3s)'
[15:05:41] style: S10: SIGTERM style8-gconv pid 112718
[15:05:51] style: S10: at ec8c33d (has 34f261c), no rebuild; gconv relaunching below
[15:05:51] style: S8: style8-gconv not running: relaunching (resumes)
[15:05:51] style: S8: launched style8-gconv ($2.0 total)
```
