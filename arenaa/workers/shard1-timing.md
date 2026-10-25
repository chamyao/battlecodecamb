# panel-A5-final shard 1 — timing (cloud session worker-1)

- Job: recipe of `remote/genome:panel-A3-db2/job.sh` (rev 60ec8ba), runtime pinned to genome/rt-a-fast 648bafd
  (sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt),
  fresh Release build of genome_eval; B318.genome from genome/candidates/ at 412ca52.
- State: `remote/genome:arenaA-5/arena/` (ba6a226). 24 live genomes sorted by name; shard 1 = even indices:
  A1117,A1223,A1249,A1261,A1267,A1279,A1285,A1289,A1294,A1299,A1301,A1308, plus the seed (genome/seeds/v23.genome).
  Selected with `--names` (baseline.py has it; no filtered state needed).
- Tag `panel-A5-final@648bafd`; 13 opponents as in the recipe; 80 games per cell.
- Machine: nproc = 4 (Intel Xeon @ 2.10GHz, 15 GB RAM), THREADS = 4.
- Games: start 1792886351, end 1792886810 (unix UTC) → wall 459 s (7.65 min), excluding the ~1-2 min build.
- Played: 13 genomes × 13 opponents = 169 cells × 80 = **13,520 games**.
- Throughput: **~106,000 games/hour** (29.5 games/s; ~7.4 games/s per core).
- No errors (rc=0).
