# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 22:46 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 5.92 4.17 3.38 on 16 threads.
Disk: 7.5G used of 38G.

## python3 processes
```
340214 python3 -m genome.search.arena --out /root/bc/genome/out/arenaZ-1/arena --tag Z --seed genome/examples/starter.genome --anchors /root/bc/genome/out/arenaZ-1/starter.genome --budget 3 --threads 5 --fixed-anchors --gate-every 100000000
341711 python3 -m genome.search.panelwatch --out /root/bc/genome/out/panelZ-1/panel.jsonl --state /root/bc/genome/out/panelZ-1/../arenaZ-1/arena --until /root/bc/genome/out/panelZ-1/../arenaZ-1/rc --every 100 --top 3 --threads 5 --opponents policies/fs-1.policy,/root/bc/genome/out/panelZ-1/fs-p2.pol
```
## tick.log (last 40 lines)
```
[21:33:45] genome: job promptbench-r1c exited rc=0
[21:33:45] genome: job simspeed-exact-1 exited rc=0
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:33:47] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:38:49] genome: job simspeed-exact-2 exited rc=0
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:38:51] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:44:05] genome: started job panel-A3-db at 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:44:07] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
fatal: not a git repository: /root/bc/genome/w/simspeed-exact-1/.git/worktrees/base
[21:49:12] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
Terminated
[21:54:25] genome: stopped job panel-A3-db (by panel-A3-db.stop)
[21:54:36] genome: started job panel-A3-db2 at 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
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
```
