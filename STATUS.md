# EC2 runner status


**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:
hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;
pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call.

Updated 2026-11-23 02:51 UTC. Instance up since 2026-11-23 01:57:08 (UTC); load: 16.16 16.06 15.16 on 16 threads.
Disk: 26G used of 38G.

## python3 processes
```
2589 venv/bin/python3 train.py mix.npz run1 --blocks 6 --ch 64 --steps 80000 --batch 256 --every 500 --threads 16 --bf16 --resume run1/start.pt
```
## tick.log (last 40 lines)
```
[23:05:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:10:50] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:15:59] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:21:09] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:26:19] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:31:29] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:36:39] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:41:49] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:47:00] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:52:10] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[23:57:20] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:02:30] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:07:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:12:50] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:18:00] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:23:10] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:28:20] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:33:30] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:38:41] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[00:43:51] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[01:57:35] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:02:45] goban: setup: python env
[02:03:27] goban: setup done; starting from m0014000.pt
[02:03:27] goban: data: downloading and extracting
[02:03:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:09:53] goban: bench: fp32 1076 bf16 2089 positions/s; mode '--bf16'
[02:09:53] goban: training: resume from run1/start.pt
remote: 
remote: Create a pull request for 'remote/goban' on GitHub by visiting:        
remote:      https://github.com/chamyao/battlecodecamb/pull/new/remote/goban        
remote: 
[02:09:54] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:15:09] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:20:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:25:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:30:53] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:36:08] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:41:24] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:46:40] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
[02:51:56] pure: halted: pure moved to the arena (17:40 UTC); final state on remote/pure
```
