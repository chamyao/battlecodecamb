# tune: remote-server status

Updated 2026-10-24 04:26 UTC.

- Clone: `/root/bc/tune`, branch `tune/runs` at `64326d0 tune line: bag threshold by altar count (hooks lead)`
- Running: yes (2 process(es))
- Machine load: 22.54 21.53 19.82 on 16 threads

## Processes

```
38168 python3 funsearch/altar_bag.py
38957 python3 /root/bc/remote_publish.py tune --msg remote/tune: job A combo-t3-dash2-jungle2-b finished: h2h_mean 0.531, cambc_check 0.5875 --comment tune: job A (combo_confirm combo-t3-dash2-jungle2-b, seeds 9025/9026) finished with no errors. Full log:
```json
{"h2h": [0.4825, 0.58], "h2h_mean": 0.53125, "gauntlet": {"v4": [0.87125, 0.8512500000000001], "locker": [0.95375, 0.92625], "fs-2": [0.8787499999999999, 0.86375], "starter": [0.98125, 0.9875], "v5d-fs2": [0.8049999999999999, 0.7849999999999999], "v7": [0.78625, 0.74625], "v7-zerogem": [0.78125, 0.7424999999999999], "v7zg-cast": [0.68875, 0.6699999999999999], "opp-icecream": [0.7949999999999999, 0.74375], "opp-odyssey": [0.82875, 0.83125], "opp-metab": [0.8687499999999999, 0.855]}, "cambc_check": 0.5875}
```
h2h 0.4825 / 0.58 (mean 0.531), cambc_check 0.5875; same change as the live tune-5. Job B (altar_bag) is running now; its exit will comment here.
```

## runs/tune/jobs.out (last 8 lines)

```

```

## runs/tune/altarbag.out (last 8 lines)

```

```

## runs/tune/combo-t3-dash2-jungle2-b.log (last 3 lines)

```
{"h2h": [0.4825, 0.58], "h2h_mean": 0.53125, "gauntlet": {"v4": [0.87125, 0.8512500000000001], "locker": [0.95375, 0.92625], "fs-2": [0.8787499999999999, 0.86375], "starter": [0.98125, 0.9875], "v5d-fs2": [0.8049999999999999, 0.7849999999999999], "v7": [0.78625, 0.74625], "v7-zerogem": [0.78125, 0.7424999999999999], "v7zg-cast": [0.68875, 0.6699999999999999], "opp-icecream": [0.7949999999999999, 0.74375], "opp-odyssey": [0.82875, 0.83125], "opp-metab": [0.8687499999999999, 0.855]}, "cambc_check": 0.5875}
```

## runs/tune/altarbag.log (last 3 lines)

```

```
