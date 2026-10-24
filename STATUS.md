# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 21:07 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 8.04 10.94 13.76 on 16 threads.
Disk: 6.1G used of 38G.

## python3 processes
```
291848 python3 -m genome.search.promptbench --out /root/bc/genome/out/promptbench-2/bench --parents-from /root/bc/genome/out/promptbench-2/../arenaA-1/arena --rounds 1 --retest-from /root/bc/genome/out/promptbench-2/../arenaA-3/arena --budget 0.8 --workers 5
```
## tick.log (last 40 lines)
```
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
Terminated
[21:01:09] genome: stopped job arenaA-3 (by arenaA-3.stop)
Terminated
[21:01:19] genome: stopped job arenaB-5 (by arenaB-5.stop)
[21:01:30] genome: started job arenaB-6 at 5a961dfc82c499b9416979b896d253562a9502f2
[21:01:42] genome: started job gatekeeper-8 at 5a961dfc82c499b9416979b896d253562a9502f2
[21:01:53] genome: started job promptbench-2 at fe57288757cbe21e7852963cabaeae7b5f6785b4
[21:01:53] genome: job arenaA-3 exited rc=stopped
[21:01:53] genome: job arenaB-5 exited rc=stopped
[21:01:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[21:07:10] genome: stopped job arenaB-6 (by arenaB-6.stop)
Terminated
[21:07:20] genome: stopped job gatekeeper-8 (by gatekeeper-8.stop)
[21:07:20] genome: job arenaB-6 exited rc=stopped
[21:07:20] genome: job gatekeeper-8 exited rc=stopped
[21:07:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
