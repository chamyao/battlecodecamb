# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-25 02:47 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 23.52 23.65 23.45 on 16 threads.
Disk: 11G used of 38G.

## python3 processes
```
693122 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-9/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-9/starter.genome --budget 6 --threads 5 --fixed-anchors --gate-every 100000000
715799 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-1x/arena --resume-from /root/bc/genome/out/arenaZ-1x/../arenaZ-1/arena --tag Z --seed genome/examples/starter.genome --budget 15 --threads 5 --fixed-anchors --gate-every 100000000
748564 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-11r/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-11r/starter.genome --budget 3 --threads 5 --fixed-anchors --gate-every 100000000 --split-every 10 --split-lines 30
812505 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-8x/arena --resume-from /root/bc/genome/out/arenaZ-8x/../arenaZ-8/arena --tag Z --seed genome/examples/starter.genome --budget 20 --opus-every 1 --threads 5 --fixed-anchors --gate-every 100000000
```
## tick.log (last 40 lines)
```
[00:46:08] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:51:19] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:56:31] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:01:43] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:06:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:12:14] genome: started job arenaZ-6 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[01:12:14] genome: job arenaA-6 exited rc=0
[01:12:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:17:34] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:22:45] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:27:48] genome: job arenaZ-2 exited rc=0
[01:27:48] genome: job arenaZ-4 exited rc=0
[01:27:55] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:33:11] genome: started job arenaZ-8 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
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
```
