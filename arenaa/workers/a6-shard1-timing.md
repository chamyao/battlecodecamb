# panel-A6-final shard 1 — timing (cloud session worker-3)

- Job: recipe of `remote/genome:panel-A3-db2/job.sh` (rev 60ec8ba), runtime pinned to genome/rt-a-fast 648bafd
  (sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt),
  fresh Release build of genome_eval; B318.genome from genome/candidates/ at 4e4c9cd (last touched 2013533).
- State: `remote/genome:arenaA-6/arena/` (06e022e). 24 live genomes sorted by name; shard 1 = even indices:
  A61090,A61158,A61171,A61180,A61191,A61200,A61203,A61206,A61213,A61217,A61220,A61224, plus the seed (genome/seeds/v23.genome).
  Selected with `--names`.
- Tag `panel-A6-final@648bafd`; 13 opponents as in the recipe; 80 games per cell.
- Machine: nproc = 4 (Intel Xeon @ 2.80GHz, 15 GB RAM), THREADS = 4.
- Games: start 1792892050, end 1792892915 (unix UTC) → wall 865 s (14.4 min), excluding the build.
- Played: 13 genomes × 13 opponents = 169 cells × 80 = **13,520 games**.
- Throughput: **~56,000 games/hour** (15.6 games/s; ~3.9 games/s per core). About half the A5 shard-1 rate
  (worker-1, 29.5 games/s) on a nominally faster CPU; presumably the A6 genomes/games are heavier or the host was shared.
- No errors (rc=0, no non-JSON output).
