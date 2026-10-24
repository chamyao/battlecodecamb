# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 20:39 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 13.07 15.43 14.75 on 16 threads.
Disk: 5.5G used of 38G.

## python3 processes
```
235872 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-3/arena --resume-from /root/bc/genome/out/arenaA-3/../arenaA-1/arena --tag A --seed genome/seeds/v23.genome --budget 8 --threads 5 --fixed-anchors --refingerprint --gate-every 100000000
251610 python3 -m genome.search.arena --out /root/bc/genome/out/arenaB-5/arena --resume-from /root/bc/genome/out/arenaB-5/../arenaB-4/arena --tag B --seed genome/seeds/v23.genome --budget 8 --threads 5 --fixed-anchors --gate-every 100000000 --intel-branch genome/intel --add-anchors policies/candidat
251986 python3 -m genome.search.gate --out /root/bc/genome/out/gatekeeper-6 --arena arenaA-* --arena arenaB-* --threads 5 --ref policies/candidates/tune-v20-L1c.policy --anchors policies/candidates/style-gconv1.policy,policies/v7.policy,policies/candidates/tune-v20-L1.policy,policies/candidates/rall
```
## tick.log (last 40 lines)
```
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
Terminated
[20:27:08] genome: stopped job arenaA-2 (by arenaA-2.stop)
Terminated
[20:27:18] genome: stopped job arenaB-3 (by arenaB-3.stop)
Terminated
[20:27:28] genome: stopped job gatekeeper-3 (by gatekeeper-3.stop)
[20:27:40] genome: started job arenaA-3 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[20:27:51] genome: started job arenaB-4 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[20:28:02] genome: started job gatekeeper-4 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[20:28:02] genome: job arenaA-2 exited rc=stopped
[20:28:02] genome: job arenaB-1 exited rc=0
[20:28:02] genome: job arenaB-3 exited rc=stopped
[20:28:02] genome: job gatekeeper-3 exited rc=stopped
[20:28:05] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[20:33:18] genome: stopped job gatekeeper-4 (by gatekeeper-4.stop)
[20:33:29] genome: started job arenaA-4 at df11725ad57541eb2a781dd84a22f3a21fdc20b8
[20:33:40] genome: started job gatekeeper-5 at 0b4a06d041ff8e7dc2b1deb4abd86e511394d588
[20:33:40] genome: job gatekeeper-4 exited rc=stopped
[20:33:43] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[20:38:56] genome: stopped job arenaB-4 (by arenaB-4.stop)
Terminated
[20:39:06] genome: stopped job gatekeeper-5 (by gatekeeper-5.stop)
[20:39:17] genome: started job arenaB-5 at 52d71e88ea305108bdf4ffb1084ec92f3dd9703f
[20:39:27] genome: started job gatekeeper-6 at 52d71e88ea305108bdf4ffb1084ec92f3dd9703f
[20:39:27] genome: job arenaB-4 exited rc=stopped
[20:39:27] genome: job gatekeeper-5 exited rc=stopped
[20:39:31] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
