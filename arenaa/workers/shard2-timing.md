# panel-A5-final shard 2 (cloud worker 2) — timing

- Job: panel-A3-db2 recipe (`origin/remote/genome:panel-A3-db2/job.sh`), run on arenaA-5's final state
  (`remote/genome:arenaA-5/arena/`), tag `panel-A5-final@648bafd`.
- Checkout: recipe rev 60ec8ba; runtime pinned to genome/rt-a-fast 648bafd (sim interp policygen genome/runtime
  genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt), genome_eval rebuilt (Release).
  B318.genome copied from genome/candidates/ at 60ec8ba before the pin.
- Shard: the 24 live genomes sorted by name, odd indices (12): A1205, A1237, A1259, A1265, A1274, A1282, A1287,
  A1291, A1296, A1300, A1303, A1311. No seed (`--no-seed --names ...` instead of `--all`; no filtered state needed).
- Opponents: the recipe's 13-opponent panel, 80 games per cell.

| | |
|---|---|
| nproc / threads | 4 (Intel Xeon @ 2.10GHz) |
| start (UTC) | 2026-10-24T23:59:18Z |
| end (UTC) | 2026-10-25T00:07:57Z |
| wall time | 519 s (8 min 39 s) |
| cells | 156 (12 genomes x 13 opponents) |
| games | 12,480 |
| games/hour | ~86,600 (~21,600 per core-hour) |

Results: `panel-A5-final-shard2.jsonl` (no errors in the run log, rc=0). Build time (~1-2 min) is not included.
