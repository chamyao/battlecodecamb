# hybrid: remote-server status

Updated 2026-10-24 04:54 UTC.

- Clone: `/root/work/battlecodecamb`, branch `funsearch/runs` at `e5a4fa8 funsearch.league: --cambc-ref (live ladder bot) sets the ladder-ready check; the vs-best check is still logged`
- Running: yes (1 process(es))
- Claude spend recorded in programs.jsonl: $0.71
- Machine load: 12.98 14.04 16.34 on 16 threads

## Processes

```
44094 python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2
```

## runs/hyb4.log (last 8 lines)

```
[05:56:44]   policies/tune-3.policy: builtin:starter 0.985, tune-1 0.630, v7-zerogem 0.770, v7 0.765, v5d-fs2 0.785, locker 0.946, v7zg-cast 0.644, v8 0.647, v7zg-monozone 0.670 | h2h 0.630 over 800 games (clear), worst change vs older -0.005
[06:04:08]   policies/tune-4.policy: builtin:starter 0.983, tune-1 0.645, v7-zerogem 0.775, v7 0.774, v5d-fs2 0.806, locker 0.949, v7zg-cast 0.675, v8 0.671, v7zg-monozone 0.694 | h2h 0.645 over 800 games (clear), worst change vs older -0.003
[06:04:13]     cambc-exact vs tune-1 (all maps x 2 sides): 0.588 -> ladder-ready
[06:04:13]   PROMOTED challenger policies/tune-4.policy: builtin:starter 98.2%, tune-1 64.5%, v7-zerogem 77.5%, v7 77.4%, v5d-fs2 80.6%, locker 94.9%, v7zg-cast 67.5%, v8 67.1%, v7zg-monozone 69.4%, cambc-exact vs tune-1 58.8%
[06:04:13] hyb4-g3: +15 programs to the next boundary (0 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', 'policies/v7.policy', 'policies/locker.policy', 'policies/v7zg-cast.policy', 'policies/v8.policy', 'policies/v7zg-monozone.policy', 'policies/tune-2.policy', 'policies/tune2-focus.policy', 'policies/tune-3.policy'], $9.47 left
[06:14:04] hyb4-g3: +28 programs to the next boundary (2 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', 'policies/v7.policy', 'policies/locker.policy', 'policies/v7zg-cast.policy', 'policies/v8.policy', 'policies/v7zg-monozone.policy', 'policies/tune-2.policy', 'policies/tune2-focus.policy', 'policies/tune-3.policy'], $9.46 left
[06:54:12] hyb4-g3: +0 programs to the next boundary (30 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', 'policies/v7.policy', 'policies/locker.policy', 'policies/v7zg-cast.policy', 'policies/v8.policy', 'policies/v7zg-monozone.policy', 'policies/tune-2.policy', 'policies/tune2-focus.policy', 'policies/tune-3.policy'], $9.11 left
[06:54:12]   challengers: ['policies/tune-5.policy']
```

## runs/hyb4-g3.log (last 3 lines)

```
[32] claude-haiku-5-5 island 1: score 0.453 | best 0.715 (#25) $0.35 | 2061s
[33] claude-haiku-5-5 island 0: score 0.537 | best 0.715 (#25) $0.35 | 2117s
done: 28 programs (1 invalid), spent $0.35; best #25 score 0.715 -> /root/work/battlecodecamb/runs/hyb4-g3/best.policy
```
