# Jobs for remote-server: style line

Written by the FunSearch lead session (the style line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/style`, branch `funsearch/style`.

## Job S1 (2026-10-24 04:50 UTC): let style6-{a,b,c} run to their end. Do not start style7.

- style6 runs to its budget and validates on its own; keep it as it is.
- When each island's league exits (budget spent or a promotion), push state to `remote/style` and
  comment on PR #3 with that island's validation lines ("h2h", "cambc", "PROMOTED").
- Do not launch style7 or any new run: the line is out of budget until the lead writes a new job here.

## Job S2 (2026-10-24 ~05:00 UTC): style7 vs tune-5. HELD (06:35 UTC, lead): do not start; stop it (SIGTERM) if running

Status: HELD until the sim-fidelity check is back (the lead holds style7 and its budget). Cham's
style6 runs count as never having happened: skip the style6-a resume (Gate 0 fallback).

Supersedes S1's "do not start style7" ($2 granted for style7). Start only after
ALL THREE style6 leagues (style6-a, -b, -c) have exited and their validation lines (h2h, cambc,
PROMOTED) are pushed to `remote/style` and commented on PR #3 (job S1). Then, in `~/bc/style`:

1. `git fetch origin funsearch/style && git checkout funsearch/style && git merge --ff-only origin/funsearch/style`
   (expect 24a4393 or later). Keep the untracked `runs/` data: style7 uses new run names.
2. `cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j4 --target interp_eval`
   then `python3 -m pytest -q tests` (expect 2012 passed). On a failure, stop and comment.
3. `WORKERS=1 EVAL_THREADS=2 VAL_THREADS=4 sh runs/style_checkin.sh` (needs FUNSEARCH_API_KEY in
   that shell; never print it). It launches style7-a/b/c (seed/bar/cambc-ref policies/tune-5.policy;
   budgets a 0.9, b 0.5, c 0.6 from runs/style_budgets). Same thread use as style6.
4. Comment on PR #3 that style7 started (commit, process list), and push status/state to
   `remote/style` as for style6. On each league exit, comment its h2h/cambc/PROMOTED lines.

## EC2 resume (2026-10-24 ~06:10 UTC): for the EC2 worker (session_01Knzq5vzttJNCCzc9dRHHkQ)

Compute moves from remote-server to EC2 (c7a.4xlarge, 16 threads). Order: style6-a (finish), then
style6-c's lines, then S2 (style7). Threads per island as before: WORKERS=1 EVAL_THREADS=2
VAL_THREADS=4 (about 6 threads/island, 18 for three; drop to WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3
if the box is shared). FUNSEARCH_API_KEY must be in the shell; never print it.

### Gate 0: no double spend (check before ANY style6 resume)
- `remote/style` (ab19ed2) is STALE for a and c: a has 82 program lines, c 114, from 04:15 UTC.
  Cham's machine ran past that point; resuming from the stale files would re-spend money already
  spent there. So resume style6-a ONLY after Cham has pushed his machine's latest `runs/` to
  `remote/style` (a new commit after ab19ed2), and only once style6-a is confirmed stopped on his
  machine. If neither happens, don't resume style6-a/c: their spend is sunk. Go straight to S2.
- style6-c already exited on Cham's machine (07:19 server time, "budget spent $2.31"). It needs no
  resume, only its validation lines (h2h/cambc/PROMOTED) from the pushed `runs/style6-c.log`. Post
  them on PR #3. Never relaunch style6-c: it would spend again.

### style6-a resume (only if Gate 0 passes)
style6-a must finish on its ORIGINAL code (1c9e008: tune-1 bar, old directives), not on 24a4393:
```
cd ~/bc && git -C style fetch origin funsearch/style remote/style
git -C style worktree add ~/bc/style6 1c9e008 && cd ~/bc/style6
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j8 --target interp_eval
# overlay run state, but never the old scripts/budgets carried on remote/style
git archive origin/remote/style remote/style/runs | tar -x --strip-components=2 \
  --exclude='*/style_budgets' --exclude='*/SPEND.md' --exclude='*/style_next_boundary.md'
```
Resume checks (all must hold, else stop and comment on PR #3):
- `wc -l runs/style6-a-g1/programs.jsonl` is higher than 82 and matches the line count Cham reports.
- The spend summed from programs.jsonl matches the last "$ left" in runs/style6-a.log
  (`python3 -c "import funsearch.league as l; print(l.spent('style6-a'))"`; budget 2.3).
- `python3 -m pytest -q tests` passes. Bit-identity: rescore program #0 (tune-1) and it matches its
  stored score.
Then launch exactly the original command (setsid nohup, log to runs/style6-a.out):
```
PYTHONUNBUFFERED=1 python3 -m funsearch.league --name style6-a --budget 2.3 --members policies/tune-1.policy \
  --keep 0 --fixed policies/v7zg-cast.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy \
  --regress 1.0 --z 2.83 --prefix style-a --line style-a --session https://claude.ai/code/session_01T3FQRTdJunBXQYe7M4YBHh \
  --fresh-seeds --directive @funsearch/styles/a_lockdown.txt --require buy_altar_lock,place_altar_lock \
  --workers 1 --eval-threads 2 --threads 4
```
When it exits, post its h2h/cambc/PROMOTED lines on PR #3 and push state to `remote/style`.

### S2 (style7) on EC2
Starts when style6-a has exited (or Gate 0 said to skip it) and style6-c's lines are posted (or
are confirmed lost). Use a separate clone/worktree on funsearch/style at 24a4393 or later:
```
cd ~/bc/style && git fetch origin funsearch/style && git checkout funsearch/style && git merge --ff-only origin/funsearch/style
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j8 --target interp_eval
python3 -m pytest -q tests          # expect 2012 passed
WORKERS=1 EVAL_THREADS=2 VAL_THREADS=4 sh runs/style_checkin.sh
```
style_checkin.sh launches style7-a/b/c via runs/style_launch.sh. Seed, bar and cambc-ref are
tune-5. Budgets come from runs/style_budgets: a 0.9 / b 0.5 / c 0.6. Rerun the same command after
any instance restart: it restarts only dead leagues, and each resumes from its programs.jsonl.
Resume checks after a restart: the program counts in runs/style7-*-g1/programs.jsonl only grow,
and the "$ left" lines in runs/style7-*.log never go up. Comment on PR #3 when style7 starts and
whenever a league exits. runs/style_push_state.sh pushes state to funsearch/style-state; if that
push fails, push to `remote/style` instead.

Island b: unchanged for now (team fights, $0.5). The line is building a "hunter" opponent (lead's
priority job). If island b's $0.5 moves to a hunter island, the line will change
runs/style_launch.sh/style_budgets on funsearch/style and edit this section before S2 starts.
