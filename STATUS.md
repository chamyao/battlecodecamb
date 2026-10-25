# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-25 04:48 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 20.27 22.91 23.15 on 16 threads.
Disk: 12G used of 38G.

## python3 processes
```
715799 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-1x/arena --resume-from /root/bc/genome/out/arenaZ-1x/../arenaZ-1/arena --tag Z --seed genome/examples/starter.genome --budget 15 --threads 5 --fixed-anchors --gate-every 100000000
970075 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-15/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-15/starter.genome --budget 20 --opus-every 1 --threads 5 --fixed-anchors --gate-every 100000000 --batch-mutate 8 --batch-wait 20 --births
971083 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-16/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-16/starter.genome --budget 3 --threads 5 --fixed-anchors --gate-every 100000000 --split-every 10 --split-lines 30
```
## tick.log (last 40 lines)
```
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
```
