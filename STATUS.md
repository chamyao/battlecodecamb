# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-25 03:44 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 8.72 10.06 14.59 on 16 threads.
Disk: 12G used of 38G.

## python3 processes
```
693122 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-9/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-9/starter.genome --budget 6 --threads 5 --fixed-anchors --gate-every 100000000
715799 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-1x/arena --resume-from /root/bc/genome/out/arenaZ-1x/../arenaZ-1/arena --tag Z --seed genome/examples/starter.genome --budget 15 --threads 5 --fixed-anchors --gate-every 100000000
943248 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-8c/arena --resume-from /root/bc/genome/out/arenaA-8c/../arenaA-6/arena --tag A8C --seed genome/seeds/v23.genome --budget 14 --threads 5 --fixed-anchors --refingerprint --gate-every 100000000 --no-distinct-games --no-bot-seeds --m
```
## tick.log (last 40 lines)
```
[01:33:17] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:38:35] genome: started job arenaZ-9 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[01:38:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:43:45] genome: job arenaZ-3 exited rc=0
[01:43:52] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:49:11] genome: started job arenaZ-1x at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[01:49:17] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:54:28] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:59:45] genome: started job arenaZ-11 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[01:59:45] genome: job arenaZ-8 exited rc=0
[01:59:53] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[02:05:06] genome: stopped job arenaZ-11 (by arenaZ-11.stop)
[02:05:22] genome: started job arenaZ-11r at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[02:05:22] genome: job arenaZ-11 exited rc=stopped
[02:05:29] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:10:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:15:52] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:21:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:26:16] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:31:27] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:36:45] genome: started job arenaZ-8x at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[02:36:45] genome: job arenaZ-6 exited rc=0
[02:36:54] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:42:06] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:47:17] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:52:30] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:57:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:02:55] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:08:08] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:13:21] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:18:35] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:23:48] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:28:51] genome: job arenaZ-8x exited rc=0
[03:29:02] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:34:14] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:39:17] genome: job arenaZ-11r exited rc=0
[03:39:26] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:44:45] genome: started job arenaA-8c at 051b4954bef9bb57bc6d828321d8fb8356d46511
[03:44:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
