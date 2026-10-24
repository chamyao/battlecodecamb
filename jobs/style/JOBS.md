# Jobs for remote-server: style line

Written by the FunSearch lead session (the style line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/style`, branch `funsearch/style`.

## Job S1 (2026-10-24 04:50 UTC): let style6-{a,b,c} run to their end. Do not start style7.

- style6 runs to its budget and validates on its own; keep it as it is.
- When each island's league exits (budget spent or a promotion), push state to `remote/style` and
  comment on PR #3 with that island's validation lines ("h2h", "cambc", "PROMOTED").
- Do not launch style7 or any new run: the line is out of budget until the lead writes a new job here.

## Job S2 (re-aimed 06:55 UTC): style7 = hunter + combat islands, $12. RELEASED, GATED on fuel costs

Status: RELEASED by the lead ($12; sim fidelity confirmed), but DO NOT LAUNCH until the gate below
holds. Code: funsearch/style 486cc5b or later.

Gate: slot_stun/slot_range/slot_radius (new blocks, coord/blocks 84f3aa9) must have calibrated
entries in interp/src/block_costs_gen.inc. Today they don't, and any policy using them fails ("no
calibrated fuel cost"). The catalog tells children to use them, so launching now would waste spend
on invalid children. The line will name the commit that fixes this here and comment on PR #3.
Check: `grep -c 'slot_stun\|slot_range\|slot_radius' interp/src/block_costs_gen.inc` prints 3.

Islands (runs/style_launch.sh, budgets in runs/style_budgets):
- h 4.0: HUNTER island. Seed opp-hunter2b (self weight 0.5), fixed tune5-reset, tune-5, opp-hunter2a,
  fight score (--fight-weight 0.5: champion-kill margin blended with the usual score).
- b 3.5: combat micro (funsearch/styles/b_combat.txt), requires set_team_target/team_target.
- a 2.25 lockdown, c 2.25 monolith, both with a combat note.
- a/b/c bar and cambc-ref: policies/tune5-reset.policy; fixed tune-5, opp-hunter2b/2a, v7zg-cast, fs-2.

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
Starts when the S2 gate holds. The style6 runs are skipped (sunk). Use the style clone on
funsearch/style at 486cc5b or later:
```
cd ~/bc/style && git fetch origin funsearch/style && git checkout funsearch/style && git merge --ff-only origin/funsearch/style
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j8 --target interp_eval
python3 -m pytest -q tests          # expect 2012 passed
grep -c 'slot_stun\|slot_range\|slot_radius' interp/src/block_costs_gen.inc   # must print 3
WORKERS=1 EVAL_THREADS=2 VAL_THREADS=4 sh runs/style_checkin.sh
```
style_checkin.sh launches style7-h/b/a/c via runs/style_launch.sh (budgets h 4.0, b 3.5, a 2.25,
c 2.25 = $12). That is 4 islands at about 6 threads each; on 16 threads use WORKERS=1
EVAL_THREADS=2 VAL_THREADS=3 if anything else shares the box. Rerun the same command after any
restart: it restarts only dead leagues, and each resumes from its programs.jsonl. Restart checks:
program counts in runs/style7-*-g1/programs.jsonl only grow, and "$ left" in runs/style7-*.log never
goes up. Comment on PR #3 when style7 starts and whenever a league exits (h2h/cambc/PROMOTED
lines). Push state with runs/style_push_state.sh (funsearch/style-state), or to remote/style if
that fails. Kill only with SIGTERM, by PID: `pkill -f` patterns match your own shell.
