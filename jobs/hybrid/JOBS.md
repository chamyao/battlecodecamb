# Jobs for remote-server: hybrid line

Written by the FunSearch lead session (the hybrid line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `/root/work/battlecodecamb`, branch `funsearch/runs`.

## Job H1 (2026-10-24 04:50 UTC): rebase the league on tune-5 (live ladder v16), resume hyb4-g3

tune-5 is the live ladder bot. Add it as a challenger against the current best (tune-4) and make it
the reference of the ladder-ready check. This is a resume, not a fresh start: nothing in
`runs/hyb4*` is deleted or moved.

1. Pause gracefully: `touch runs/hyb4-g3/STOP`. In-flight children finish, then the run exits and
   the league logs "STOP file present: pausing the league" and exits too. Wait for both PIDs
   (league 35530, run 35531) to be gone. Do not kill them; if one hangs > 15 min, SIGTERM by PID
   (never `pkill -f`).
2. `git pull origin funsearch/runs` (to e5a4fa8 or later). It adds `policies/tune-5.policy` (merge of
   interp/v0 b23330e, policy file only) and `--cambc-ref` in funsearch/league.py. The simulator is
   unchanged, so no rebuild.
3. `echo policies/tune-5.policy >> runs/hyb4.challengers`
4. `rm runs/hyb4-g3/STOP`, then relaunch the league with the same command line as before plus
   `--cambc-ref policies/tune-5.policy`:

   ```
   python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 \
     --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy \
     --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 \
     --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2
   ```
   (members are read from runs/hyb4.json on resume; the CLI value is ignored then.)
5. Check the log line `hyb4-g3: +N programs to the next boundary (M so far), best policies/tune-4.policy`
   with M = the programs already done, and that runs/hyb4.challengers holds tune-5.
6. Push state to `remote/hybrid` and comment on PR #1 with the log tail.

At the g3 boundary tune-5 is judged against tune-4 by the league rule. Comment on PR #1 when the
boundary verdict is logged (promotion or "no promotion"), with the validation lines.
