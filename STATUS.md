# EC2 runner status

Updated 2026-10-24 16:35 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 7.85 9.82 11.82 on 16 threads.
Disk: 3.4G used of 38G.

## python3 processes
```
92618 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
92630 /usr/bin/python3 -m funsearch.run --run pure4-g5 --budget 4.29 --max-programs 151 --seed-policy policies/fs-p3.policy --opponents builtin:starter@0.25,policies/fs-p3.policy@3.0,policies/tune-v20-L1c.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,polic
134213 python3 -m funsearch.run --run style8-gyield --budget 1.27 --max-programs 400 --seed-policy policies/style-gconv1.policy --opponents builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraf
134253 python3 -m funsearch.league --name style8-b --budget 3.5 --members policies/tune5-campreset.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune5-campreset.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,polici
134277 /usr/bin/python3 -m funsearch.run --run style8-b-g1 --budget 0.92 --max-programs 149 --seed-policy policies/tune5-campreset.policy --opponents builtin:starter@0.25,policies/tune5-campreset.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-
142461 python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.
142565 /usr/bin/python3 -m funsearch.run --run hyb5-g3 --budget 16.30 --max-programs 29 --seed-policy policies/pool/v21.policy --opponents builtin:starter@0.25,policies/pool/v21.policy@3.0,policies/pool/v20.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.polic
```
## tick.log (last 40 lines)
```
[15:05:41] style: S10: SIGTERM style8-gconv pid 112718
[15:05:51] style: S10: at ec8c33d (has 34f261c), no rebuild; gconv relaunching below
[15:05:51] style: S8: style8-gconv not running: relaunching (resumes)
[15:05:51] style: S8: launched style8-gconv ($2.0 total)
[15:10:59] style: S10 check: gconv relaunched: $1.76 left of $2.0
[15:16:04] hybrid: H16: hold set for the next hyb5 boundary
[15:16:07] style: S11: SIGTERM pid 112760
[15:16:07] style: S11: SIGTERM pid 112781
[15:16:07] style: S11: SIGTERM pid 117552
[15:16:34] style: S11: at a8682fd (has 5b70f04: v22 dead-camp fix), rebuilt, 2024 passed in 6.18s; relaunching b and gconv
[15:16:34] style: S8: style8-gconv not running: relaunching (resumes)
[15:16:34] style: S8: launched style8-gconv ($2.0 total)
[15:16:35] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[15:16:35] style: launched style8-b (budget $3.5)
[15:21:43] style: S11 check: gconv $1.75 left of $2.0; b style8-b-g1: +6 programs to the next boundary (144 so far) $0.95 left
[15:31:58] hybrid: H16: SIGTERM hyb5 pid 114024
[15:32:21] hybrid: H16: funsearch/runs 44d4dac (has 8b38ce6: dead-camp fix / v22 build), rebuilt, 2029 passed in 7.13s; relaunching hyb5, same flags
[15:32:21] hybrid: hyb5 not running: relaunching (resume from runs/)
[15:32:21] hybrid: launched hyb5 league
[15:32:21] hybrid: H10 check: 28 new programs: conversion 13 (0.46, expect 0.31), disengage 1 (0.04, expect 0.12), vocab 5 (0.18, expect ~0.2)
[15:42:40] hybrid: H17: hold set for the next hyb5 boundary
[16:03:15] hybrid: H17: SIGTERM hyb5 pid 124830
[16:03:38] hybrid: H17: funsearch/runs fce1ade (has 27dd4a2, fce1ade: H17-H19), built interp_eval+fuel_turns, 2029 passed in 7.31s; relaunching hyb5 with the #82 fuel island and --yield-weight 0.25
[16:03:38] hybrid: hyb5 not running: relaunching (resume from runs/)
[16:03:38] hybrid: launched hyb5 league
[16:03:38] hybrid: H15 ALERT: 'FLAG yield' in explore.txt:   FLAG yield: #119 gems per capture 13.8 vs v21 8.8 (+5.0) with 52% vs v21 (score 0.545)
[16:03:41] style: S12: SIGTERM pid 120806
[16:03:41] style: S12: SIGTERM pid 120843
[16:03:41] style: S12: SIGTERM pid 131479
[16:04:07] style: S12: at 16dfcad (has 983462f), rebuilt, 2024 passed in 6.28s; gconv stopped for good; b restarting; gyield starting
[16:04:07] style: S12: launched style8-gyield ($1.27)
[16:04:07] style: style8-b not running: relaunching (resumes from its programs.jsonl)
[16:04:07] style: launched style8-b (budget $3.5)
[16:09:15] style: S12 gyield check: gap run style8-gyield (conversion:max:0.05,gems_per_capture:max:3 vs policies/tune-v21.policy): $1.27 left of |gap metric conversion (max, scale 0.05): reference tune-v21 mirror value 0.8974|gap metric gems_per_capture (max, scale 3): reference tune-v21 mirror value 10.6992|gap: 2 term(s), equal weight; win floor 0.5 vs the reference; weight 0.5|
[16:14:20] hybrid: H18 check: 'yield term: 122 logged programs rescaled'; 3 new children carry metrics.yield
[16:19:29] hybrid: H20: hold set for the next hyb5 boundary
[16:34:57] hybrid: H20: SIGTERM hyb5 pid 133949
[16:35:16] hybrid: H20: funsearch/runs 694a4a3 (has 694a4a3/166f85c: v23 style-gconv1, sim fix, #76, H21 cover screens), built interp_eval+fuel_turns, 2029 passed in 7.37s; relaunching hyb5 with style-gconv1 fixed + island-1 seed, island-3 seed #76, --screen-maps cover --rescreen-top 3
[16:35:16] hybrid: hyb5 not running: relaunching (resume from runs/)
[16:35:16] hybrid: launched hyb5 league
```
