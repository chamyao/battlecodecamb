# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 23:43 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 9.56 9.63 11.36 on 16 threads.
Disk: 8.0G used of 38G.

## python3 processes
```
351143 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-5/arena --resume-from /root/bc/genome/out/arenaA-5/../arenaA-3/arena --tag A --seed genome/seeds/v23.genome --budget 7.77 --threads 5 --fixed-anchors --refingerprint --gate-every 100000000
351678 python3 -m genome.search.panelwatch --out /root/bc/genome/out/panelA-5/panel.jsonl --state /root/bc/genome/out/panelA-5/../arenaA-5/arena --until /root/bc/genome/out/panelA-5/../arenaA-5/rc --every 100 --after-births 737 --top 3 --threads 5 --opponents policies/candidates/style-gconv1.policy,
```
## tick.log (last 40 lines)
```
[21:54:36] genome: job panel-A3-db exited rc=stopped
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:54:39] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:59:53] genome: started job lineage-A at f0e6ce0c575a2d10147ba7bef48334a98c78bd53
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:59:55] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:04:57] genome: job panel-A3-db2 exited rc=0
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:04:59] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:10:05] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:15:10] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:20:15] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:25:19] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:30:22] genome: job lineage-A exited rc=0
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[22:30:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:35:31] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:40:44] genome: started job arenaZ-1 at 7e40b6f
[22:40:56] genome: started job panelZ-1 at cff0329519d81573f27fef7cfa35a5962f740ea2
[22:40:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:46:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:51:18] genome: started job arenaA-5 at 7e40b6f9582dc78a054cc969f81077bf58ea5294
[22:51:30] genome: started job panelA-5 at 08770916c1dfbe9ddd9968b747ba090107b37f55
[22:51:34] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[22:56:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:01:50] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:06:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:12:06] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:17:15] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:22:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:27:33] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:32:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:37:51] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:42:54] genome: job arenaZ-1 exited rc=0
[23:42:54] genome: job panelZ-1 exited rc=0
[23:43:00] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
