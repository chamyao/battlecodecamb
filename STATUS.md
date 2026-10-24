# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 21:28 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 6.98 10.28 11.62 on 16 threads.
Disk: 6.8G used of 38G.

## python3 processes
```
299054 python3 -m genome.search.promptbench --out /root/bc/genome/out/promptbench-r1b/bench --parents-from /root/bc/genome/out/promptbench-r1b/../arenaA-3/arena --no-seed-parent --parents 5 --link-seed 11 --rounds 1 --budget 0.6 --workers 5
299512 python3 -m genome.search.promptbench --out /root/bc/genome/out/promptbench-r1c/bench --parents-from /root/bc/genome/out/promptbench-r1c/../arenaA-3/arena --parents 4 --skip-parents 5 --link-seed 13 --rounds 1 --budget 0.6 --workers 5
```
## tick.log (last 40 lines)
```
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
```
