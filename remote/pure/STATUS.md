# pure: remote-server status

Updated 2026-10-24 04:15 UTC.

- Clone: `/root/bc-pure`, branch `funsearch/pure` at `699942e pure line: snapshot before moving the league to remote-server; launcher threads 3x2 / 5`
- Running: yes (2 process(es))
- Claude spend recorded in programs.jsonl: $5.14
- Machine load: 22.29 19.96 18.09 on 16 threads

## Processes

```
9711 python3 -m funsearch.league --name pure4 --budget 9.71 --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt --policy-prefix fs-p --line pure --session https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX --workers 3 --eval-threads 2 --threads 5
9714 /usr/bin/python3 -m funsearch.run --run pure4-g3 --budget 5.17 --max-programs 137 --seed-policy policies/fs-p2.policy --opponents builtin:starter@0.25,policies/fs-p2.policy@3.0,policies/tune-3.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy --workers 3 --eval-threads 2
```

## runs/pure4.log (last 8 lines)

```
[02:45:40]     cambc-exact vs tune-1: 0.388
[02:51:04]   #135 (run score 0.723): builtin:starter 0.979, fs-p1 0.675, tune-1 0.357, v5d 0.635, v4 0.730, locker 0.906, fs-2 0.676 | h2h 0.675, worst change vs older +0.037
[02:56:24]   #120 (run score 0.721): builtin:starter 0.979, fs-p1 0.679, tune-1 0.360, v5d 0.640, v4 0.735, locker 0.906, fs-2 0.667 | h2h 0.679, worst change vs older +0.037
[02:56:24]   PROMOTED fs-p2.policy: builtin:starter 98.2%, fs-p1 69.2%, tune-1 38.4%, v5d 64.2%, v4 73.6%, locker 87.9%, fs-2 69.2%, cambc-exact vs fs-p1 65.0%, cambc-exact vs tune-1 38.8%
[02:56:26] pure4-g3: +151 programs (to 151), best policies/fs-p2.policy, league ['policies/tune-1.policy', 'policies/v5d.policy', 'policies/v4.policy', 'policies/locker.policy', 'policies/fs-2.policy'], $5.36 left
[03:07:46] pure4-g3: +151 programs (to 151), best policies/fs-p2.policy, league ['policies/tune-3.policy', 'policies/v5d.policy', 'policies/v4.policy', 'policies/locker.policy', 'policies/fs-2.policy'], $5.35 left
[03:31:22] STOP file present: pausing the league
[05:34:19] pure4-g3: +137 programs (to 151), best policies/fs-p2.policy, league ['policies/tune-3.policy', 'policies/v5d.policy', 'policies/v4.policy', 'policies/locker.policy', 'policies/fs-2.policy'], $5.17 left
```

## runs/pure4-g2.log (last 3 lines)

```
[149] claude-haiku-5-5 island 0: score 0.711 | best 0.729 (#140) $0.65 | 1755s
[150] claude-opus-5-5 island 0: score 0.709 | best 0.729 (#140) $0.65 | 1858s
done: 42 programs (1 invalid), spent $0.65; best #140 score 0.729 -> /home/user/battlecodecamb/runs/pure4-g2/best.policy
```

## runs/pure4-g3-oldbuild.log (last 3 lines)

```
seed score 0.647
[4] claude-haiku-5-5 island 2: score 0.496 | best 0.647 (#0) $0.01 | 183s
[5] claude-haiku-5-5 island 2: score 0.538 | best 0.647 (#0) $0.02 | 356s
```

## runs/pure4-g3.log (last 3 lines)

```
[46] claude-haiku-5-5 island 1: error: NameError: line 133: dest already defined | best 0.660 (#23) $0.60 | 2109s
[47] claude-haiku-5-5 island 0: score 0.544 | best 0.660 (#23) $0.61 | 2161s
[48] claude-haiku-5-5 island 0: score 0.620 | best 0.660 (#23) $0.61 | 2245s
```
