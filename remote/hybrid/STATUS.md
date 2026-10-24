# hybrid: remote-server status

Updated 2026-10-24 04:15 UTC.

- Clone: `/root/work/battlecodecamb`, branch `funsearch/runs` at `23a1f27 funsearch.league: keep consumed challengers pending until their boundary is validated (restart-safe)`
- Running: yes (2 process(es))
- Claude spend recorded in programs.jsonl: $0.36
- Machine load: 21.91 19.77 18.00 on 16 threads

## Processes

```
35530 python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 --workers 3 --eval-threads 2
35531 /usr/bin/python3 -m funsearch.run --run hyb4-g3 --budget 9.46 --max-programs 28 --seed-policy policies/tune-4.policy --opponents builtin:starter@0.25,policies/tune-4.policy@3.0,policies/tune-1.policy,policies/v7-zerogem.policy,policies/v7.policy,policies/locker.policy,policies/v7zg-cast.policy,policies/v8.policy,policies/v7zg-monozone.policy,policies/tune-2.policy,policies/tune2-focus.policy,policies/tune-3.policy --workers 3 --eval-threads 2
```

## runs/hyb4.log (last 8 lines)

```
[05:42:09]   policies/tune-2.policy: builtin:starter 0.985, tune-1 0.634, v7-zerogem 0.769, v7 0.764, v5d-fs2 0.784, locker 0.946, v7zg-cast 0.642, v8 0.645, v7zg-monozone 0.667 | h2h 0.634 over 800 games (clear), worst change vs older -0.005
[05:49:24]   policies/tune2-focus.policy: builtin:starter 0.981, tune-1 0.614, v7-zerogem 0.762, v7 0.750, v5d-fs2 0.782, locker 0.939, v7zg-cast 0.632, v8 0.637, v7zg-monozone 0.662 | h2h 0.614 over 800 games (clear), worst change vs older -0.013
[05:56:44]   policies/tune-3.policy: builtin:starter 0.985, tune-1 0.630, v7-zerogem 0.770, v7 0.765, v5d-fs2 0.785, locker 0.946, v7zg-cast 0.644, v8 0.647, v7zg-monozone 0.670 | h2h 0.630 over 800 games (clear), worst change vs older -0.005
[06:04:08]   policies/tune-4.policy: builtin:starter 0.983, tune-1 0.645, v7-zerogem 0.775, v7 0.774, v5d-fs2 0.806, locker 0.949, v7zg-cast 0.675, v8 0.671, v7zg-monozone 0.694 | h2h 0.645 over 800 games (clear), worst change vs older -0.003
[06:04:13]     cambc-exact vs tune-1 (all maps x 2 sides): 0.588 -> ladder-ready
[06:04:13]   PROMOTED challenger policies/tune-4.policy: builtin:starter 98.2%, tune-1 64.5%, v7-zerogem 77.5%, v7 77.4%, v5d-fs2 80.6%, locker 94.9%, v7zg-cast 67.5%, v8 67.1%, v7zg-monozone 69.4%, cambc-exact vs tune-1 58.8%
[06:04:13] hyb4-g3: +15 programs to the next boundary (0 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', 'policies/v7.policy', 'policies/locker.policy', 'policies/v7zg-cast.policy', 'policies/v8.policy', 'policies/v7zg-monozone.policy', 'policies/tune-2.policy', 'policies/tune2-focus.policy', 'policies/tune-3.policy'], $9.47 left
[06:14:04] hyb4-g3: +28 programs to the next boundary (2 so far), best policies/tune-4.policy, league ['policies/tune-1.policy', 'policies/v7-zerogem.policy', 'policies/v7.policy', 'policies/locker.policy', 'policies/v7zg-cast.policy', 'policies/v8.policy', 'policies/v7zg-monozone.policy', 'policies/tune-2.policy', 'policies/tune2-focus.policy', 'policies/tune-3.policy'], $9.46 left
```

## runs/hyb4-g3.log (last 3 lines)

```
seed score 0.703
[4] claude-haiku-5-5 island 3: score 0.515 | best 0.703 (#0) $0.01 | 111s
[5] claude-haiku-5-5 island 3: score 0.596 | best 0.703 (#0) $0.01 | 112s
```
