# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 21:49 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 4.80 3.35 5.09 on 16 threads.
Disk: 7.1G used of 38G.

## python3 processes
```
318960 python3 -m genome.search.baseline --out /root/bc/genome/out/panel-A3-db/panel.jsonl --state /root/bc/genome/out/panel-A3-db/../arenaA-3/arena --all --threads 5 --tag panel-A3-db@db3f945 --anchors policies/candidates/style-gconv1.policy,policies/candidates/tune-v20-L1.policy,policies/candidate
```
## tick.log (last 40 lines)
```
[21:07:20] genome: job gatekeeper-8 exited rc=stopped
[21:07:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:12:37] genome: started job panel-A3 at 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
[21:12:49] genome: started job promptbench-r1b at 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
[21:13:00] genome: started job promptbench-r1c at 60ec8ba678521f842dc5e42ecf7bf7c2ce265842
[21:13:02] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:18:08] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:23:14] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[21:28:28] genome: started job simspeed-exact-1 at 16aa3b56ec2ffb0c2b52b08a01b08eedd25dc21b
[21:28:28] genome: job panel-A3 exited rc=0
[21:28:28] genome: job promptbench-2 exited rc=0
warning: adding embedded git repository: simspeed-exact-1/suite/base
hint: You've added another git repository inside your current repository.
hint: Clones of the outer repository will not contain the contents of
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
```
