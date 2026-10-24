# EC2 runner status

Updated 2026-10-24 17:42 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 9.10 11.44 12.07 on 16 threads.
Disk: 3.4G used of 38G.

## python3 processes
```
92618 python3 -m funsearch.league --name pure4 --budget 15.15 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd --workers 3 --eval-threads 2 --thread
143592 python3 -m funsearch.league --name style8-b2 --budget 0.95 --members policies/tune-v21.policy --keep 0 --best-weight 3.0 --cambc-ref policies/tune-v21.policy --fixed policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policies/v7zg-cast
143612 /usr/bin/python3 -m funsearch.run --run style8-b2-g1 --budget 0.95 --max-programs 150 --seed-policy policies/tune-v21.policy --opponents builtin:starter@0.25,policies/tune-v21.policy@3.0,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.poli
145998 /usr/bin/python3 -m funsearch.run --run pure4-g5 --budget 1.04 --max-programs 146 --seed-policy policies/fs-p3.policy --opponents builtin:starter@0.25,policies/fs-p3.policy@3.0,policies/tune-v20-L1c.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy,poli
148638 python3 -m funsearch.run --run style8-gsub --budget 0.52 --max-programs 400 --seed-policy policies/tune-v21.policy --island-seeds policies/style-gconv1.policy,policies/tune-v21.policy --opponents builtin:starter@0.25,policies/tune-v21.policy@3,policies/style-gconv1.policy,policies/opp-finishe
```
## tick.log (last 40 lines)
```
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
[16:40:29] style: S12b: b's first verdict predates S12; stopping b now
[16:40:29] style: S12: SIGTERM style8-b pid 134253 (boundary verdict in)
[16:40:29] style: S12: SIGTERM style8-b pid 134277 (boundary verdict in)
[16:40:29] style: S12: b verdict: [15:54:59]   no promotion; style8-b-g1 continues; b stopped (STOP in runs/style8-b-g1), b2 starts below
[16:40:29] style: launched style8-b2 (budget $0.95)
[16:45:34] hybrid: H22: SPEND.md lines appended (hybrid total $23.26, cap $40)
[16:45:34] hybrid: H21b: hold set for the next hyb5 boundary
[16:45:34] hybrid: H17 check: re-seeded island 3 with hyb5-g3-82 (score -0.649);re-seeded island 3 with hyb5-g3-76 (score 0.657); island-3 children 8: metrics.fuel 8, fuel axis 4 (0.50, expect ~0.5)
[16:45:34] hybrid: H20 check: re-seeded island 1 with style-gconv1 (score 0.639);re-seeded island 3 with hyb5-g3-76 (score 0.657); 2 new children mention style-gconv1 (metrics opponent)
[17:06:09] style: S14: SIGTERM style8-gyield pid 134213
[17:06:16] style: S14: at d446d2b (has 35595b0), 2024 passed in 6.32s; gyield stopped for good; gsub starting
[17:06:16] style: S14: launched style8-gsub ($0.52)
[17:11:24] style: S14 gsub check: gap run style8-gsub (gem_margin:max:50 vs policies/tune-v21.policy): $0.52 left of $0.52|gap metric gem_margin (max, scale 50): reference tune-v21 mirror value 29.8125|gap: 1 term(s), equal weight; win floor 0.5 vs the reference; weight 0.5|
[17:21:37] hybrid: H21 check: 18 're-screened #' lines, 're-screen (cover maps): 9 programs'; 3 new children with screen_maps=cover
[17:42:12] hybrid: FINAL: SIGTERM hyb5 pid 142461
[17:42:27] hybrid: FINAL: hyb5 stopped at the boundary, not relaunched; last hyb5.log: [16:35:18]   helpers: 20 helpers kept; top 20: -> hyb5.helpers.json|[17:40:14] hold file present: waiting at the round boundary (remove hyb5.hold to go on)|
[17:42:29] hybrid: FINAL: state pushed (remote/hybrid fb5107a)
[17:42:29] pure: pure final stop: STOP requested (gen 5)
```
