# Jobs for remote-server: pure line

Written by the FunSearch lead session (the pure line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `/root/bc-pure`, branch `funsearch/pure`.

## Job P1 (2026-10-24 04:50 UTC): tune-5 (live ladder v16) replaces tune-3 from pure4-g4. No restart.

1. `git pull origin funsearch/pure` (to 56de9fe or later): adds `policies/tune-5.policy` only (merge of
   interp/v0 b23330e). Simulator unchanged: no rebuild, and do not stop the league.
2. In `runs/pure_fixed.txt` and `runs/pure_send.txt` replace `policies/tune-3.policy` with
   `policies/tune-5.policy` (all other lines unchanged).
   The league re-reads both files: pure_fixed at the next generation (g3 keeps its frozen
   opponents), pure_send at the next promotion check.
3. Push state to `remote/pure` and comment on PR #2 with the two files' contents.
