# panel-A6-final shard 2 (cloud worker 4) — timing

- Job: panel-A3-db2 recipe (`origin/remote/genome:panel-A3-db2/job.sh`), run on arenaA-6's final state
  (`remote/genome:arenaA-6/arena/`), tag `panel-A6-final@648bafd`.
- Checkout: recipe rev 60ec8ba (worktree); runtime pinned to genome/rt-a-fast 648bafd (sim interp policygen
  genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt), genome_eval built fresh (Release).
  B318.genome copied from genome/candidates/ at 60ec8ba before the pin.
- Shard: the 24 live genomes sorted by name, odd indices (12): A61128, A61167, A61173, A61188, A61197, A61202,
  A61205, A61209, A61214, A61218, A61223, A61225. No seed (`--no-seed --names ...`).
- Opponents: the recipe's 13-opponent panel, 80 games per cell.

| | |
|---|---|
| nproc / threads | 4 (Intel Xeon @ 2.10GHz) |
| start (UTC) | 2026-10-25T01:34:14Z |
| end (UTC) | 2026-10-25T01:42:36Z |
| wall time | 502 s (8 min 22 s) |
| cells | 156 (12 genomes x 13 opponents) |
| games | 12,480 |
| games/hour | ~89,500 (~22,400 per core-hour) |

Results: `panel-A6-final-shard2.jsonl` (no errors in the run log, rc=0). Build time is not included.
