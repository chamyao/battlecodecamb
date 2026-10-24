# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 22:10 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 4.52 5.31 5.39 on 16 threads.
Disk: 7.3G used of 38G.

## python3 processes
```
325213 python3 -m genome.search.lineage --out /root/bc/genome/out/lineage-A/lineage.jsonl --state /root/bc/genome/out/lineage-A/../arenaA-3/arena --threads 5 --ancestors A1,A3,A7,A8,A20,A67,A107,A129,A137,A141,A161,A177,A196,A259,A263,A314,A324,A335,A341,A352,A494,A509,A514,A543,A548,A615,A622,A637,
```
## tick.log (last 40 lines)
```
hint: the embedded repository and will not know how to obtain it.
hint: If you meant to add a submodule, use:
hint: 
hint: 	git submodule add <url> simspeed-exact-1/suite/base
hint: 
hint: If you added this path by mistake, you can remove it from the
hint: index with:
hint: 
hint: 	git rm --cached simspeed-exact-1/suite/base
hint: 
hint: See "git help submodule" for more information.
[21:28:31] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:33:45] genome: started job simspeed-exact-2 at 654ddbc9f69b2f9495e13a4c1b84362c5ef7ec96
[21:33:45] genome: job promptbench-r1b exited rc=0
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
```
