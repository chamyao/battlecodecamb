# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-10-24 19:55 UTC. Instance up since 2026-10-24 06:21:47 (UTC); load: 13.46 13.28 12.05 on 16 threads.
Disk: 4.1G used of 38G.

## python3 processes
```
164542 python3 -m genome.search.arena --out /root/bc/genome/out/arenaA-1/arena --tag A --seed genome/seeds/v23.genome --budget 8 --threads 5
164789 python3 -m genome.search.arena --out /root/bc/genome/out/arenaB-1/arena --tag B --seed genome/seeds/v23.genome --budget 3 --threads 5 --intel-branch genome/intel
```
## tick.log (last 40 lines)
```
remote: 
[17:47:41] style: S15: pushed style/arena-overlay 391f2d4:  45 files changed, 2901 insertions(+); style tick stops here
[17:52:45] hybrid: FINAL: ec2-final-check.txt + hyb5.cmdline pushed (remote/hybrid c474b96)
[17:52:45] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[17:57:47] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:02:59] genome: started job smoke1 at ff86746cf72a
remote: 
remote: Create a pull request for 'remote/genome' on GitHub by visiting:        
remote:      https://github.com/chamyao/battlecodecamb/pull/new/remote/genome        
remote: 
[18:03:01] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:08:03] genome: job smoke1 exited rc=0
[18:08:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:13:16] genome: started job evo-policy-1 at fb14c783bda3090568092fef92757f19af026464
[18:13:26] genome: started job evo-starter-pilot at fb14c783bda3090568092fef92757f19af026464
[18:13:27] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:18:31] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:23:35] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:28:39] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:33:42] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:38:45] genome: job evo-starter-pilot exited rc=0
[18:38:46] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:43:50] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:48:55] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:53:57] genome: job evo-policy-1 exited rc=0
[18:53:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[18:59:01] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:04:04] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:09:06] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:14:09] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:19:21] genome: started job arenaA-1 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[19:19:31] genome: started job arenaB-1 at 681e2e3a90741660b8a8b51e2c0609461f6fddff
[19:19:32] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:24:36] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:29:41] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:34:45] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:39:49] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:44:54] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:49:58] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[19:55:03] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
