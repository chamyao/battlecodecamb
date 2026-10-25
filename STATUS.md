# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-25 06:02 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 4.30 1.20 2.45 on 16 threads.
Disk: 13G used of 38G.

## python3 processes
```
1155288 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-17a/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-17a/starter.genome --budget 20 --opus-every 1 --threads 5 --fixed-anchors --gate-every 100000000 --batch-mutate 8 --batch-wait 20 --bir
1155811 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-17b/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-17b/starter.genome --budget 20 --opus-every 1 --threads 5 --fixed-anchors --gate-every 100000000 --batch-mutate 8 --batch-wait 20 --bir
```
## tick.log (last 40 lines)
```
[03:44:45] genome: started job arenaA-8c at 051b4954bef9bb57bc6d828321d8fb8356d46511
[03:44:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:49:59] genome: job arenaZ-9 exited rc=0
[03:50:10] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[03:55:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:00:43] genome: started job arenaZ-15 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[04:00:59] genome: started job arenaZ-16 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[04:01:11] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:06:26] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:11:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:16:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:22:15] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:27:32] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:32:48] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:38:06] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:43:23] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:48:26] genome: job arenaA-8c exited rc=0
[04:48:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:53:53] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[04:59:07] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:04:21] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:09:35] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:14:49] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:19:52] genome: job arenaZ-15 exited rc=0
[05:20:03] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:25:05] genome: job arenaZ-16 exited rc=0
[05:25:16] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:30:28] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:35:41] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:40:54] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[05:46:06] genome: stopped job arenaZ-1x (by arenaZ-1x.stop)
[05:46:06] genome: job arenaZ-1x exited rc=stopped
[05:46:16] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:51:26] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[05:56:35] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[06:01:54] genome: started job arenaZ-17a at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[06:02:09] genome: started job arenaZ-17b at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[06:02:26] genome: started job arenaZ-17c at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[06:02:34] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
