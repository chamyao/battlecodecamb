# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 18:08 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 0.00 0.15 2.68 on 16 threads.
Disk: 3.6G used of 38G.

## python3 processes
```
```
## tick.log (last 40 lines)
```
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
[17:47:37] pure: pure: final state pushed, HALT
[17:47:38] style: S15: SIGTERM style8-b2 pid 143592
[17:47:38] style: S15: SIGTERM style8-b2 pid 143612
remote: 
remote: Create a pull request for 'style/arena-overlay' on GitHub by visiting:        
remote:      https://github.com/chamyao/battlecodecamb/pull/new/style/arena-overlay        
remote: 
[17:47:41] style: S15: pushed style/arena-overlay 391f2d4:  45 files changed, 2901 insertions(+); style tick stops here
[17:52:45] hybrid: FINAL: ec2-final-check.txt + hyb5.cmdline pushed (remote/hybrid c474b96)
[17:52:45] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[17:57:47] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:02:59] genome: started job smoke1 at ff86746cf72a
remote: 
remote: Create a pull request for 'remote/genome' on GitHub by visiting:        
remote:      https://github.com/chamyao/battlecodecamb/pull/new/remote/genome        
remote: 
[18:03:01] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:08:03] genome: job smoke1 exited rc=0
[18:08:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
