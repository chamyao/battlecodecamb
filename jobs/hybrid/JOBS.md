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

## Job H2 (2026-10-24 05:20 UTC, hybrid line session): after the g3 verdict, add two g4 challengers and pick up the new prompt

Do this only once the g3 boundary verdict is logged (promotion or "no promotion") and g4 has started.
Do not touch the g3 validation in progress.

1. Pause gracefully: `touch runs/hyb4-g4/STOP`, then wait for the league and run PIDs to exit. Do not kill
   them; if one hangs > 15 min, SIGTERM by PID (never `pkill -f`).
2. `git pull origin funsearch/runs` (to bfd869c or later). It adds:
   - 3654e36: prompt fix. The KEY TOOL camp-skip formula cost 25 points (half of g2's children used it);
     the stale ladder-loss list is trimmed. This is why the restart is needed.
   - bfd869c: `policies/candidates/hyb-t5m.policy` and `policies/candidates/hyb-t5m-rich15d6f.policy`.
   No simulator change, so no rebuild. Run `python3 -m pytest -q tests` (2012 pass).
3. `printf 'policies/candidates/hyb-t5m.policy\npolicies/candidates/hyb-t5m-rich15d6f.policy\n' >> runs/hyb4.challengers`
4. `rm runs/hyb4-g4/STOP`, then relaunch with exactly the H1 command line (including
   `--cambc-ref policies/tune-5.policy`).
5. Check the log line `hyb4-g4: +N programs to the next boundary (M so far)` and that runs/hyb4.challengers
   holds both files. Push state to `remote/hybrid` and comment on PR #1 with the log tail.

At the g4 boundary both are judged against the best by the league rule. Comment on PR #1 with the
validation lines when the verdict is logged.

## EC2 resume (2026-10-24 06:05 UTC, hybrid line session)

Compute moves from remote-server to EC2 (c7a.4xlarge spot, 16 threads; bit-identical results). This
section replaces remote-server for hyb4. It is a RESUME of hyb4, never a fresh start: nothing in
`runs/hyb4*` or `runs/validation_cache.jsonl` may be deleted, renamed or regenerated.

### State source

The hyb4 state lives on branch `remote/hybrid` under `remote/hybrid/runs/`: `hyb4.json`, `hyb4.challengers`,
`hyb4.log`, `hyb4-g1/`, `hyb4-g2/`, `hyb4-g3/` (programs.jsonl), `validation_cache.jsonl`, `SPEND.md`.
**It is stale** (snapshot 04:54 UTC: gen 3, 30/30 programs, g3 boundary not yet validated). Wait until
Cham has pushed his machine's latest `runs/` to `remote/hybrid`, and check that `remote/hybrid/STATUS.md`
is dated after the remote-server league was stopped. Using the stale snapshot is safe (the league
re-validates the g3 boundary, and the validation cache makes that cheap), but any g4 programs made
on remote-server since would be lost and re-bought.

### Commands

```
git clone https://github.com/chamyao/battlecodecamb ~/bc/hybrid && cd ~/bc/hybrid
git checkout funsearch/runs && git pull origin funsearch/runs        # bfd869c or later
git fetch origin remote/hybrid
mkdir -p runs && git archive origin/remote/hybrid remote/hybrid/runs | tar -x --strip-components=2 -C .
ls runs   # hyb4.json hyb4.challengers hyb4.log hyb4-g1 hyb4-g2 hyb4-g3 validation_cache.jsonl SPEND.md ...
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j --target interp_eval
python3 -m pip install -q anthropic pytest
python3 -m pytest -q tests                                            # expect 2012 passed
```

H2's challengers: append them only if they are not already in `runs/hyb4.challengers`:

```
for p in policies/candidates/hyb-t5m.policy policies/candidates/hyb-t5m-rich15d6f.policy; do
  grep -qx "$p" runs/hyb4.challengers || echo "$p" >> runs/hyb4.challengers; done
cat runs/hyb4.challengers
```

Launch (FUNSEARCH_API_KEY must be set in this shell; budget is the line's cap, already partly spent;
the league subtracts spend recorded in runs/hyb4-g*/programs.jsonl):

```
nohup setsid python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 \
  --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy \
  --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 \
  --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2 >> runs/hyb4.out 2>&1 < /dev/null &
```

(`--members` is ignored on resume; members come from runs/hyb4.json.) On a promotion the league
`git commit`s the new policy locally; push it to `remote/hybrid` (not funsearch/*) like the rest of
the state. Pause gracefully with `touch runs/hyb4-g<N>/STOP` (stop by PID with SIGTERM if needed,
never `pkill -f`; SIGINT can hang the thread pools).

### Resume checks (do all before reporting it running)

1. The first new line in `runs/hyb4.log` must be `hyb4-g3: ... (30 so far), best policies/tune-4.policy`
   with `+0 programs` (the g3 boundary is re-validated), or, if Cham's push already has the g3 verdict,
   `hyb4-g4: +N programs to the next boundary (M so far), best <g3 winner>` with M matching
   `wc -l runs/hyb4-g4/programs.jsonl` minus 4.
   **A fresh start shows `hyb4-g1: +30 programs ... (0 so far), best policies/v7-zerogem.policy`:
   if you see that, stop immediately, since the state was not restored.**
2. The `challengers:` log line at the next boundary lists tune-5 (if g3 is not yet validated) and the
   two H2 policies.
3. The `$... left` figure continues from the last logged one (~$9.11 at 04:54 UTC), not $9.82.

Report the first log lines, then each boundary verdict (validation lines + cambc-exact vs tune-5), on PR #1.
