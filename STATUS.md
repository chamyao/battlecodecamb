# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 20:55 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 18.94 19.48 17.39 on 16 threads.
Disk: 5.7G used of 38G.

## python3 processes
```
235872 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-3/arena --resume-from /root/bc/genome/out/arenaA-3/../arenaA-1/arena --tag A --seed genome/seeds/v23.genome --budget 8 --threads 5 --fixed-anchors --refingerprint --gate-every 100000000
251610 python3 -m genome.search.arena --out /root/bc/genome/out/arenaB-5/arena --resume-from /root/bc/genome/out/arenaB-5/../arenaB-4/arena --tag B --seed genome/seeds/v23.genome --budget 8 --threads 5 --fixed-anchors --gate-every 100000000 --intel-branch genome/intel --add-anchors policies/candidat
```
## tick.log (last 40 lines)
```
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
[20:44:37] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[20:49:50] genome: stopped job arenaA-4 (by arenaA-4.stop)
Terminated
[20:50:00] genome: stopped job gatekeeper-6 (by gatekeeper-6.stop)
[20:50:12] genome: started job gatekeeper-7 at bfbdabdcec7c8500a4d33da1e8e52dc9a67429bd
[20:50:25] genome: started job promptbench-1 at ed9377cd89141589e4bbccd3fc96e4a8b3756295
[20:50:25] genome: job arenaA-4 exited rc=stopped
[20:50:25] genome: job gatekeeper-6 exited rc=stopped
[20:50:29] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[20:55:42] genome: stopped job gatekeeper-7 (by gatekeeper-7.stop)
Terminated
[20:55:52] genome: stopped job promptbench-1 (by promptbench-1.stop)
[20:55:52] genome: job gatekeeper-7 exited rc=stopped
[20:55:52] genome: job promptbench-1 exited rc=stopped
[20:55:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
