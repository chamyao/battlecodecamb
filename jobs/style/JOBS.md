# Jobs for remote-server: style line

Written by the FunSearch lead session (the style line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/style`, branch `funsearch/style`.

## Job S1 (2026-10-24 04:50 UTC): let style6-{a,b,c} run to their end. Do not start style7.

- style6 runs to its budget and validates on its own; keep it as it is.
- When each island's league exits (budget spent or a promotion), push state to `remote/style` and
  comment on PR #3 with that island's validation lines ("h2h", "cambc", "PROMOTED").
- Do not launch style7 or any new run: the line is out of budget until the lead writes a new job here.

## Job S2 (07:15 UTC): style8 = hunter + combat islands, $12. RELEASED: launch now

Status: RELEASED (lead). Code: funsearch/style 5c47501 or later (slot_* fuel costs merged).
The old-plan style7-a/b/c (4f8ce7e, stopped 06:58 UTC, $0.04) stay archived. Leave their STOP
files and state in place; the new islands use NEW names style8-h/b/a/c and start fresh.

Islands (runs/style_launch.sh, budgets in runs/style_budgets: h 3.95, b 3.5, a 2.25, c 2.25):
- h: HUNTER island (group hunter / opp-hunter3 work). Seed opp-hunter2b (self weight 0.5); fixed
  tune5-campreset, tune5-reset, tune-5, opp-hunter2a; fight score --fight-weight 0.5.
- b: combat micro (funsearch/styles/b_combat.txt), requires set_team_target/team_target.
- a lockdown and c monolith, both with a combat note.
- a/b/c bar and cambc-ref: policies/tune5-campreset.policy (the upload candidate); fixed tune5-reset,
  tune-5, opp-hunter2b/2a, v7zg-cast, fs-2.

## Job S3 (07:35 UTC): islands a and c PAUSED, h gets their threads (lead)

- Pause style8-a and style8-c: STOP files in runs/style8-a-g1/ and runs/style8-c-g1/, then SIGTERM
  each league and its funsearch.run child by PID. Budgets stay in runs/style_budgets for later
  (a $2.25, c $2.25 minus what they spent). Don't restart them until a job here says so.
- Island h on funsearch/style 3d34e37 or later: --round 40 (validates every 40 programs), v18 in its
  fixed opponents, extra directions in h_hunter.txt. Run it with its own threads:
  `H_WORKERS=2 H_EVAL_THREADS=2 WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3 sh runs/style_checkin.sh`
  (restart h only: SIGTERM the h league and child by PID first; b keeps running).
- Comment h's validation lines (and b's) on PR #3 at each boundary.

## Job S12 (16:05 UTC): gconv -> gyield (two-term gap), and b -> b2 (bar v21) after b's boundary verdict

On funsearch/style 983462f or later (deploy/v0 ec9778c group_rate + v22 fix; rebuild interp_eval, configure first;
pytest 2024).
1. gconv: SIGTERM its funsearch.run by PID and leave it stopped (it is done at $0.72; its best child is
   policies/style-gconv1.policy). Start the fresh two-term run:
```
GAP_OPPONENTS="builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraft.policy" \
WORKERS=2 EVAL_THREADS=2 setsid nohup sh runs/style_gap_launch.sh style8-gyield 1.27 \
  conversion:max:0.05,gems_per_capture:max:3 policies/style-gconv1.policy funsearch/styles/g_conversion.txt \
  >> runs/style8-gyield.out 2>&1 &
```
   Resumable like gconv (rerun the same command after a restart). First lines: two "gap metric ..." lines and
   "gap: 2 term(s)".
2. b: when runs/style8-b.log logs its first boundary verdict ("no promotion" / "PROMOTED"), put a STOP file in
   runs/style8-b-g1/, SIGTERM b by PID, and let the check-in start b2 (bar/cambc-ref tune-v21, $0.95, same
   directive and threads as b). If b PROMOTED, comment the lines on PR #3 first.

## Job S8 (14:20 UTC; released 14:45 on 6e8cc17): conversion gap run, $2 (lead-released)

On funsearch/style 6e8cc17 or later (deploy/v0 d23c1cb: all 15 sensors calibrated; hill-climb + helpers). Rebuild interp_eval (configure first)
and run pytest (2012). Then launch one resumable run, style8-gconv, alongside h2/b (a/c stay paused):
```
GAP_OPPONENTS="builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraft.policy" \
WORKERS=2 EVAL_THREADS=2 setsid nohup sh runs/style_gap_launch.sh style8-gconv 2.0 conversion:max:0.05 \
  policies/tune-v21.policy funsearch/styles/g_conversion.txt >> runs/style8-gconv.out 2>&1 &
```
The launcher subtracts recorded spend on every start; rerun the same command after any restart. Push
runs/style8-gconv/programs.jsonl, runs/style8-gconv.out and the run log with the usual state push. It is a plain
funsearch.run (no league, no validation boundaries); the line hand-validates the best children (800 games vs v21).

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

### S2 (style8) on EC2
In the style clone on funsearch/style (5c47501 or later):
```
cd ~/bc/style && git fetch origin funsearch/style && git checkout funsearch/style && git merge --ff-only origin/funsearch/style
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j8 --target interp_eval
python3 -m pytest -q tests          # expect 2012 passed
grep -c 'slot_stun\|slot_range\|slot_radius' interp/src/block_costs_gen.inc   # must print 3
WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3 sh runs/style_checkin.sh    # shared box: the reduced threads
```
style_checkin.sh launches style8-h/b/a/c via runs/style_launch.sh. Rerun the same command after any
restart: it restarts only dead leagues, and each resumes from its programs.jsonl. In
runner/lines/style.sh, point the restart loop at style8 (names, budgets from runs/style_budgets),
not style7. Restart checks: program counts in runs/style8-*-g1/programs.jsonl only grow, and "$ left"
in runs/style8-*.log never goes up. Comment on PR #3 when style8 starts and whenever a league exits
(h2h/cambc/PROMOTED lines). Push state with runs/style_push_state.sh (funsearch/style-state) or to
remote/style. Kill only with SIGTERM, by PID: `pkill -f` patterns match your own shell.
