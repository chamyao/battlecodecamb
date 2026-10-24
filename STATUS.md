# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 20:21 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 11.56 14.67 13.91 on 16 threads.
Disk: 4.7G used of 38G.

## python3 processes
```
164789 python3 -m genome.search.arena --out /root/bc/genome/out/arenaB-1/arena --tag B --seed genome/seeds/v23.genome --budget 3 --threads 5 --intel-branch genome/intel
229042 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-2/arena --resume-from /root/bc/genome/out/arenaA-2/../arenaA-1/arena --tag A --seed genome/seeds/v23.genome --budget 8 --threads 5 --fixed-anchors
229795 python3 -m genome.search.gate --out /root/bc/genome/out/gatekeeper-3 --arena arenaA-1/arena+arenaA-2/arena --arena arenaB-1/arena+arenaB-2/arena+arenaB-3/arena --threads 5
```
## tick.log (last 40 lines)
```
[18:33:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:38:45] genome: job evo-starter-pilot exited rc=0
[18:38:46] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:43:50] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:48:55] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:53:57] genome: job evo-policy-1 exited rc=0
[18:53:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:59:01] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:04:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:09:06] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:14:09] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:19:21] genome: started job arenaA-1 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[19:19:31] genome: started job arenaB-1 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[19:19:32] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:24:36] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:29:41] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:34:45] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:39:49] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:44:54] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:49:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:55:03] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[20:00:08] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[20:05:13] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[20:10:27] genome: started job arenaB-2 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[20:10:30] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[20:15:44] genome: started job gatekeeper-2 at 56b76c429afb2813653d39dc499e654918f2db47
[20:15:47] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[20:21:00] genome: stopped job arenaA-1 (by arenaA-1.stop)
Terminated
[20:21:10] genome: stopped job arenaB-2 (by arenaB-2.stop)
Terminated
[20:21:20] genome: stopped job gatekeeper-2 (by gatekeeper-2.stop)
[20:21:31] genome: started job arenaA-2 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[20:21:42] genome: started job arenaB-3 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[20:21:53] genome: started job gatekeeper-3 at 56b76c429afb2813653d39dc499e654918f2db47
[20:21:53] genome: job arenaA-1 exited rc=stopped
[20:21:53] genome: job arenaB-2 exited rc=stopped
[20:21:53] genome: job gatekeeper-2 exited rc=stopped
[20:21:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
