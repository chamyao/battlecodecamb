# Jobs for remote-server: hybrid line

Written by the FunSearch lead session (the hybrid line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `/root/work/battlecodecamb`, branch `funsearch/runs`.

## Job H1 (DONE on remote-server; superseded by the EC2 resume section below) (2026-10-24 04:50 UTC): rebase the league on tune-5 (live ladder v16), resume hyb4-g3

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

## Job H2 (NOT RUN; folded into the EC2 resume section below) (2026-10-24 05:20 UTC, hybrid line session): after the g3 verdict, add two g4 challengers and pick up the new prompt

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

### State source (updated 06:40 UTC: do not wait for Cham's machine)

Resume from the CURRENT `remote/hybrid` snapshot (bca8693) under `remote/hybrid/runs/`: `hyb4.json`,
`hyb4.challengers`, `hyb4.log`, `hyb4-g1/`, `hyb4-g2/`, `hyb4-g3/` (programs.jsonl), `validation_cache.jsonl`,
`SPEND.md`. Cham's later runs are treated as never having happened. The snapshot is: gen 3, 30/30 g3
programs done (34 lines in hyb4-g3/programs.jsonl), g3 boundary NOT validated, tune-5 pending in
`hyb4.json` ("pending": ["policies/tune-5.policy"]), `hyb4.challengers` empty. So EC2 starts by
validating the g3 boundary. Lost after the snapshot: the g3 verdict and ~$0.35 of hyb4 spend, which
programs.jsonl won't show (accounted for in --budget below and in SPEND.md).

### Commands

```
git clone https://github.com/chamyao/battlecodecamb ~/bc/hybrid && cd ~/bc/hybrid
git checkout funsearch/runs && git pull origin funsearch/runs        # 9ef3d8b or later (must include
                                                                      # 9ef3d8b: new blocks + combat prompt; OP CODES
                                                                      # CHANGED, so always rebuild after pulling)
git merge-base --is-ancestor 9ef3d8b HEAD && echo prompt-ok          # must print prompt-ok
git fetch origin remote/hybrid
mkdir -p runs && git archive origin/remote/hybrid remote/hybrid/runs | tar -x --strip-components=2 -C .
ls runs   # hyb4.json hyb4.challengers hyb4.log hyb4-g1 hyb4-g2 hyb4-g3 validation_cache.jsonl SPEND.md ...
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j --target interp_eval
python3 -m pip install -q anthropic pytest
python3 -m pytest -q tests                                            # expect 2012 passed
```

Challengers: tune5-reset (coordinator's reset fix, 59.7% vs tune-5) and H2's two. Append them only if they
are not already in `runs/hyb4.challengers`. They are judged at the g3 boundary together with the pending tune-5:

```
for p in policies/tune5-reset.policy policies/candidates/hyb-t5m.policy policies/candidates/hyb-t5m-rich15d6f.policy; do
  grep -qx "$p" runs/hyb4.challengers || echo "$p" >> runs/hyb4.challengers; done
cat runs/hyb4.challengers
```

Log the spend and budget change first (SPEND.md is in runs/ from the snapshot):

```
cat >> runs/SPEND.md <<'X'
| 2026-10-24 | hyb4-g3 (best tune-4) on remote-server after snapshot bca8693: lost with Cham's machine (g3 verdict and later programs), not in programs.jsonl | ? | ~0.35 | |
| 2026-10-24 | hybrid line cap raised $10 -> $30 (project cap $90 -> $200). League --budget 29.47 = 30 - 0.18 (hyb, hyb2, hyb3) - 0.35 (lost above) | | | |
X
```

Launch (FUNSEARCH_API_KEY must be set in this shell; the league subtracts spend recorded in
runs/hyb4-g*/programs.jsonl from --budget):

```
nohup setsid python3 -m funsearch.league --name hyb4 --threads 5 --budget 29.47 \
  --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy \
  --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 \
  --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2 >> runs/hyb4.out 2>&1 < /dev/null &
```

(`--members` is ignored on resume; members come from runs/hyb4.json.) On a promotion the league
`git commit`s the new policy locally; push it to `remote/hybrid` (not funsearch/*) like the rest of
the state. Pause gracefully with `touch runs/hyb4-g<N>/STOP` (stop by PID with SIGTERM if needed,
never `pkill -f`; SIGINT can hang the thread pools).

If EC2 is ALREADY running on an older funsearch/runs: do not pull into the running generation. At the next
boundary pause with the STOP file, pull, rebuild (`cmake -S interp -B interp/build ... && cmake --build ...`),
run the tests, append any missing challengers, and relaunch.

### Resume checks (do all before reporting it running)

1. The first new line in `runs/hyb4.log` must be
   `hyb4-g3: +0 programs to the next boundary (30 so far), best policies/tune-4.policy, ...`
   followed by `challengers: [...]` listing tune-5, tune5-reset, hyb-t5m and hyb-t5m-rich15d6f (the g3 boundary is validated now).
   **A fresh start shows `hyb4-g1: +30 programs ... (0 so far), best policies/v7-zerogem.policy`:
   if you see that, stop immediately, since the state was not restored.**
2. After the g3 verdict: `hyb4-g4: +30 programs to the next boundary (0 so far), best <g3 winner>`.
3. The `$... left` figure is about $28.76 (29.47 minus the $0.71 recorded in hyb4-g*/programs.jsonl; the snapshot
   logged $9.11 left of 9.82), not $29.47.

Report the first log lines, then each boundary verdict (validation lines + cambc-exact vs tune-5), on PR #1.

## EC2 update U1 (2026-10-24 06:55 UTC, hybrid line session)

hyb4 is running on EC2 since 06:38 UTC at funsearch/runs 13facf9 (g3 boundary validating tune-5, hyb-t5m,
hyb-t5m-rich15d6f). Changes, in order:

1. **Never run funsearch/runs 9ef3d8b.** Its prompt tells children to use slot_stun / slot_range / slot_radius,
   which have no fuel costs yet, so every child using them is rejected. ff56f90 removes that. Until told
   otherwise, staying on 13facf9 is fine.
2. **Now (no restart needed):** add the new base as a challenger for the next boundary. The policy file isn't in
   13facf9, so fetch it alone (it parses with 13facf9's blocks):
   ```
   git fetch origin funsearch/runs && git show origin/funsearch/runs:policies/tune5-campreset.policy > policies/tune5-campreset.policy
   grep -qx policies/tune5-campreset.policy runs/hyb4.challengers || echo policies/tune5-campreset.policy >> runs/hyb4.challengers
   ```
   tune5-campreset replaces tune5-reset: do not add tune5-reset.
3. **At the g4 boundary only (optional, better prompt):** STOP, `git pull origin funsearch/runs` (aa032ba or later: costed slot_* blocks + combat prompt;
   never 9ef3d8b alone), REBUILD interp_eval (op codes changed: `cmake -S interp -B interp/build
   -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j --target interp_eval`), `python3 -m pytest -q tests`,
   relaunch with the same command line (--budget 29.47).

## Job H3 (2026-10-24 09:00 UTC, hybrid line session; approved by the FunSearch lead): stop hyb4, start hyb5 on v19 with exploration

hyb4's best (hyb-t5m) is far behind live v19, so its next generations search a stale base. hyb4 ends at its
g4 verdict and hyb5 starts on v19.

1. Let hyb4 finish validating its g4 boundary (tune5-campreset challenger). When `hyb4-g5:` appears in
   runs/hyb4.log, stop the league: `touch runs/hyb4-g5/STOP`, wait for the league and run PIDs to exit
   (SIGTERM by PID if one hangs > 15 min; never `pkill -f`). Push runs/ to remote/hybrid as usual, and post the
   g4 verdict lines on PR #1. Nothing in runs/hyb4* is deleted.
2. `git pull origin funsearch/runs` (557ce2c or later: exploration mode, --change-weights, per-generation
   explore_report, policies/pool/). Rebuild interp_eval (configure + build) and run `python3 -m pytest -q tests`
   (2012 pass).
3. Launch (FUNSEARCH_API_KEY from SSM as before):
   ```
   nohup setsid python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 \
     --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy \
     --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.policy,policies/pool/opp-icecream.policy \
     --prefix fs-h --line hybrid --round 30 --cambc-ref policies/pool/v19.policy --workers 3 --eval-threads 2 \
     --explore --change-weights 0.6,0.4,0 --novelty-lambda 0.3 --archive-share 0.3 \
     --island-seeds policies/pool/v19.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.policy \
     >> runs/hyb5.out 2>&1 < /dev/null &
   ```
   Budget: the hybrid cap is $30; ~$5.0 is spent (0.18 hyb..hyb3, 1.26 hyb4, 0.35 lost, 3.21 exploration test),
   so hyb5 gets 25.0. Append to runs/SPEND.md:
   `| 2026-10-24 | exploration test xc1/xp1/xp2 (hybrid session container) | 114 | 3.21 | |` and
   `| 2026-10-24 | hyb5 started on v19 (explore), --budget 25.0 | | | |`.
4. Checks: the first runs/hyb5.log line is `hyb5-g1: +30 programs to the next boundary (0 so far), best
   policies/pool/v19.policy, ...`; runs/hyb5-g1.log shows `seed v19 score ...` (islands 0,1), `seed lean-g65`
   (island 2) and `seed opp-hunter3` (island 3); children log a variant (metrics.variant in programs.jsonl).
5. After each generation the league writes runs/hyb5-gN.explore.txt (drafts, executed-block coverage, behaviour
   cells, per-variant validity/novelty/score). Push it with the state and post its first lines with each boundary
   verdict on PR #1.

The upload-evidence league is separate (tools/league.py with the full required pool: v19, hunters 2a/2b/2c/3,
icecream, odyssey, metab, metadraft); the hybrid session runs it for any hyb5 promotion.

## Job H4 (2026-10-24 10:55 UTC, hybrid line session; approved by the FunSearch lead): retune hyb5 at its next round boundary

After two rounds hyb5's best only matches v19 and every top program comes from the v19 / lean-g65 islands, so:
less archive, hunter3 island replaced by v19, draft axis dropped (the pairs axis stays, with a richer brief).

1. At the next hyb5 round boundary (the line after the next `no promotion` / `PROMOTED`, i.e. `hyb5-gN: +30 programs
   ... (90 so far)` or later), stop the league the same way as the g4 upgrade: set runs/hyb5.hold, and when the league
   logs `hold file present`, SIGTERM it by PID (never pkill -f).
2. `git pull origin funsearch/runs` (8c5b4e4 or later, ancestor check), rebuild interp_eval, run pytest (2012).
3. Remove the hold and relaunch with the H3 command line changed in these flags only:
   `--archive-share 0.1`
   `--island-seeds policies/pool/v19.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v19.policy`
   `--axes items,vision,teleport,team,roles,pairs,macro,abilities,combat`   (all but draft)
   (unchanged: --budget 25.0, --change-weights 0.6,0.4,0, --novelty-lambda 0.3, members, fixed, round 30, cambc-ref.)
   The budget counts the spend already in hyb5-g*/programs.jsonl, so 25.0 stays.
4. Check runs/hyb5-gN.log: exactly one line `re-seeded island 3 with v19` (islands 0/1/2 keep their v19 / v19 /
   lean-g65 lineages), then children logging axes other than draft.

## Job H5 (2026-10-24 11:40 UTC, hybrid line session; per the FunSearch lead): rebase hyb5 on v20

v20 (tune-fight-2s = v19 + ward our own bush tile when no enemy is visible) is live. At the next hyb5 round boundary
(after `... (150 so far)` or later), the same way as H4 (hold, SIGTERM by PID at "hold file present"):

1. `git pull origin funsearch/runs` (d0cbd58 or later: policies/pool/v20.policy). No interp change, so no rebuild
   needed (rebuild anyway if the pull brings interp/ changes); pytest.
2. `grep -qx policies/pool/v20.policy runs/hyb5.challengers || echo policies/pool/v20.policy >> runs/hyb5.challengers`
3. Relaunch with the H4 command line changed in two flags only:
   `--island-seeds policies/pool/v20.policy,policies/pool/v20.policy,policies/pool/lean-g65.policy,policies/pool/v20.policy`
   `--cambc-ref policies/pool/v20.policy`
4. Check runs/hyb5-g1.log: exactly three new lines `re-seeded island 0|1|3 with v20`; island 2 (lean-g65) kept.
   At the next boundary `challengers: [...]` lists policies/pool/v20.policy; if it is promoted, hyb5-g2 starts with
   best policies/pool/v20.policy and its islands seeded from the same --island-seeds (v20).

## Job H7 (2026-10-24 12:45 UTC, hybrid line session; per the FunSearch lead): rebase hyb5 on v21, at the H6 boundary

v21 (tune-v20-L1c = v20 + one altar lock per team, shared byte 7 bits 0-1) is live. Do this at the SAME boundary as H6
(the hold already set for the end of the current hyb5-g2 round), in one relaunch:

1. `git pull origin funsearch/runs` to c4341a3 or later (ancestor check). It contains 48a1404 (H6: prompt keeps byte 7
   bits 0-1), policies/pool/v21.policy and deploy/v0 (>= d9d2897: the LOCKFIX, required to evaluate v21 or any lock policy,
   plus recalibrated fuel costs). interp/ CHANGED: reconfigure + rebuild interp_eval, then pytest (2012).
2. `grep -qx policies/pool/v21.policy runs/hyb5.challengers || echo policies/pool/v21.policy >> runs/hyb5.challengers`
3. Relaunch with the current command line (H5's) changed in two flags only:
   `--island-seeds policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/lean-g65.policy,policies/pool/v21.policy`
   `--cambc-ref policies/pool/v21.policy`
4. Check runs/hyb5-g2.log: exactly three new lines `re-seeded island 0|1|3 with v21`; island 2 kept. The next boundary's
   `challengers:` line lists policies/pool/v21.policy.

## Job H8 (2026-10-24 13:45 UTC, hybrid line session; per the FunSearch lead): disengage axis + search fixes, next hyb5 boundary

At the next hyb5 round boundary (hold + SIGTERM by PID, as before):

1. `git pull origin funsearch/runs` to f31c3a4 or later (ancestor check). It adds: the "disengage" axis; prompt lists the parent's
   draft order and asks to keep comments; run.py restores the lineage header when a child drops it; policies/pool/v19-L1c.policy;
   and (cae2515) a diagnostics-only sim event for tools/fights.py. sim/ CHANGED: rebuild interp_eval; pytest (2012).
2. Relaunch with the current command line (H7's) changed in two flags only:
   `--axes items,vision,teleport,team,roles,pairs,macro,abilities,combat,disengage`
   `--island-seeds policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/v20.policy,policies/pool/v19-L1c.policy`
3. Check runs/hyb5-g3.log: exactly two new lines `re-seeded island 2 with v20` and `re-seeded island 3 with v19-L1c`
   (islands 0/1 keep v21); new children log axis "disengage" among others.

### H8 addendum (revised 14:20 UTC): every child is hill-climbed before comparison
If H8 has not fired yet, apply this with it; otherwise at the following boundary. Require funsearch/runs fb401ce or later
(ancestor check; python only beyond H8's sim rebuild). The climb is now ON BY DEFAULT in funsearch.run (defaults:
--tune-steps 6 --tune-games 16 --tune-slack 0.15 --tune-margin 0.03), so the relaunch needs NO new flags; drop any
--tune-children / --tune-steps / --tune-games flags from the previous addendum.
Check: new children in runs/hyb5-g3/programs.jsonl carry metrics.tuned (with "seconds"), and comment-only children are
logged as error "no code change". Report programs/hour in hyb5 before and after (from the [N] lines' timestamps).

## Job H9 (2026-10-24 14:10 UTC, hybrid line session; per the FunSearch lead): cheap climb NOW (not at a boundary)

The climb running since H8b (fb401ce defaults) re-plays the incumbent each step on all 10 opponents (~4.7k games per
child) and breaks the cap (programs/hour must stay >= half the untuned ~49-58/h). Restart immediately, mid-round:

1. SIGTERM hyb5 (league + run) by PID; merge funsearch/runs to c6eb17a or later (ancestor check; python only); pytest.
2. Relaunch with the current (H8) command line plus:
   `--tune-opponents builtin:starter@0.25,policies/pool/v21.policy@3,policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-metadraft.policy`
   (defaults now: --tune-games 8 --tune-steps 4 --tune-rejects 2 --tune-margin 0.03 --tune-slack 0.15; ~250 games per
   climbed child at most.)
3. Report programs/hour for the first full round after this (children only), and mean metrics.tuned.games.

## Job H10 (2026-10-24 14:20 UTC, hybrid line session; per the FunSearch lead): conversion axis, next boundary after H9

At the next hyb5 round boundary after H9 (hold + SIGTERM by PID):
1. `git pull origin funsearch/runs` to 4174c28 or later (ancestor check). It merges coord/capture-metric 2dc29a7: sim/ and
   policygen/blocks.py CHANGED (new block unit_tributing; interp_eval reports captures, gems_captured, tributes), so
   reconfigure + rebuild interp_eval and run pytest (2024).
2. Relaunch with the current (H9) command line, changing only --axes to the weighted menu:
   `--axes conversion:3,disengage:2,items:1,vision:1,teleport:1,team:1,roles:1,pairs:1,macro:1,abilities:1,combat:1`
3. Check: new children log axis "conversion" about 3 in 14 draws, "disengage" 2 in 14.

### H10 addendum (14:30 UTC, approved by the FunSearch lead): shared helper library, same boundary as H10
Require funsearch/runs 7a6038d or later instead (contains H10's commit). Add to the relaunch:
`--helpers-runs <hybrid runs dir>,<pure runs dir>,<style runs dir>` (the three lines' runs/ directories on this box,
globs allowed, e.g. /root/bc/*/runs). At every boundary the league then rebuilds runs/hyb5.helpers.json (+ HELPERS.md)
from all of them and passes --helpers to the run. Check: hyb5.log shows "helpers: N helpers kept" at the next round
start, and some new children carry metrics.lib_helpers. Push runs/hyb5.HELPERS.md with the state.
(Pure's own league, when it takes this, uses only pure's runs dir.)

## Job H11 (2026-10-24 14:35 UTC, hybrid line session; per the FunSearch lead): gap sensors + new-vocabulary variant, next boundary

At the next hyb5 round boundary (if H10 has not fired yet, fold this into it: same boundary, one pull):
1. `git pull origin funsearch/runs` to e82cb4a or later (ancestor check). It contains:
   - 84504a5: all axis briefs are measured facts + levers (no prescriptions); `--vocab-share` (default 0.2): that
     share of explore calls lists the newest blocks; explore.txt gets per-50-program new-block uptake, vocab vs other.
   - 5ef0ab2 (gap sensors batch 1, BOT_VERIFY clean on deploy/v0 577a141): interp/ and policygen/blocks.py CHANGED
     (unit_max_health, unit_strength, unit_focus, enemies_near, allies_near, strength_at). Reconfigure + rebuild
     interp_eval, then pytest (2027).
   - e82cb4a: metrics.exec_blocks is now measured vs builtin:starter (idle never comes into view, so blocks that need a
     visible enemy never counted; novelty and uptake missed them). Older children keep their vs-idle exec_blocks.
2. Relaunch with the current command line unchanged (vocab variant is on by default).
3. Check: about 1 in 5 new children have metrics.variant.vocab true; runs/hyb5.explore.txt shows the
   "new-block uptake by programs" line. Push the explore.txt with the state.
Batch 2 of the gap sensors (coord/gap-blocks bd8b098) follows as H12 once deploy/v0 has it.

## Job H12 (2026-10-24 14:30 UTC, hybrid line session; per the FunSearch lead): gap sensors batch 2, with H11
Require funsearch/runs fe36f47 or later instead of e82cb4a (same boundary as H11, one pull; if H11 already ran, the
next boundary). It merges deploy/v0 9d607af (batch 2: threat_eta, altar_eta, retreat_eta, enemy_between,
group_contested, team_gems, unseen_enemies_near; BOT_VERIFY running at the lead's end, revert if told). interp/ CHANGED:
rebuild interp_eval, pytest (2027). Same command line. The new sensors join the vocab variant list automatically.
H12 update (14:40 UTC): require funsearch/runs 1d748cf or later (contains fe36f47). On relaunch with --explore,
funsearch.run re-measures exec_blocks vs builtin:starter for every valid program of the current run that was logged
vs idle (8 threads, ~0.2 s each in wall time, cached in runs/hyb5/exec_blocks_v2.json), before the database builds
its novelty counts. Check: hyb5.log prints "exec_blocks vs starter for N programs (Ts)" at startup. pytest (2028).

## Job H13 (2026-10-24 14:45 UTC, hybrid line session; per the FunSearch lead): fuel recalibration, with H11/H12
Require funsearch/runs 7fff19f or later (contains 1d748cf). Same boundary as H11/H12 if they have not run (one pull),
else the next one. It merges deploy/v0 90e1d5b: the sim fuel recalibration 54b0640 (all block cost rows refit; gap
sensors batch 1 calibrated, batch 2 still provisional; v21 vs v20 --bot-seeds 47 -> 46/80). interp/ and sim/ CHANGED:
reconfigure + rebuild interp_eval, pytest (2028). The rebuild changes the binary mtime, so validation_cache.jsonl
keys miss and validations re-run on the new costs (no manual cache cleanup). Seeds are re-scored by the league on the
new round; the child climb measures parent and child on the same build per child. Same command line.
bank_detour (coord/bank-detour) is on the vocab list already and appears once merged (H14).
H13 update (14:50 UTC): require funsearch/runs 14df19b or later instead (merges deploy/v0 f6a56b7: all gap sensors and
unit_tributing calibrated, no provisional rows; tune-2 vs tune-1 80/80 identical with cambc). If H13 already fired on
7fff19f, take 14df19b at the next boundary as H14 (rebuild interp_eval, pytest 2028, same command line).

## Job H14 (2026-10-24 14:45 UTC, hybrid line session; per the FunSearch lead): bank_detour, calibrated
Require funsearch/runs d915b03 or later (contains 14df19b and e71632d). If the H10-H13 pull has not happened yet, take d915b03
in that same pull; otherwise at the next boundary. It merges deploy/v0 d23c1cb: the bank_detour(Tile) sensor with its
calibrated cost row (0 provisional rows; all 15 sensors now in). interp/ CHANGED: rebuild interp_eval, pytest (2028).
Same command line; bank_detour joins the vocab-variant list automatically.

## Job H15 (2026-10-24 14:55 UTC, hybrid line session; per the FunSearch lead): conversion weight 5, same pull
Fold into the pending H10-H14 pull (else the next boundary). Require funsearch/runs 6646329 or later (contains d915b03,
106613c: conversion-brief gem-race facts, fights.py gem metrics, explore_report capture-yield lines). Python only beyond
d915b03's rebuild. Relaunch with H10's --axes, changing only the conversion weight from 3 to 5:
`--axes conversion:5,disengage:2,items:1,vision:1,teleport:1,team:1,roles:1,pairs:1,macro:1,abilities:1,combat:1`
Check: about 5 in 16 new children log axis "conversion". runs/hyb5.explore.txt gets "yield" lines; if a
"FLAG yield" line appears, tell the hybrid line session at once.

## Job H16 (2026-10-24 15:10 UTC, hybrid line session; per the FunSearch lead): dead-camp fix (ladder v22 build)
Fold into the pending H10-H15 pull if it has not happened (require funsearch/runs 8b38ce6 or later instead; contains
6646329), else the next boundary. It merges deploy/v0 e32dc0d: 28fbf8f (sim camp() on a dead camp returns
not-in-vision, as cambc), 59d9e3a (group_threat / group_hp treat such camps as dead), 020e375 (refit). Live ladder v22
= v21's policy on this build. sim/ and interp/ CHANGED: reconfigure + rebuild interp_eval, pytest (2028). Same command
line (H15 axes). Re-baseline: the rebuild invalidates validation_cache keys (binary mtime) and the new round re-scores
the seeds; the bar stays v21 (policies/pool/v21.policy), now evaluated on the v22 build.

## Job H17 (2026-10-24 15:45 UTC, hybrid line session; per the FunSearch lead): #82 fuel island
Fold into the H16 pull if it has not happened (one pull), else the next boundary. Require funsearch/runs 27dd4a2 or
later (contains 8b38ce6). Besides H16's rebuild, ALSO build fuel_turns:
`cmake --build interp/build -j --target interp_eval fuel_turns`; pytest (2029).
Relaunch with the current command line plus these changes (run args, passed through by the league):
1. --island-seeds: replace policies/pool/v19-L1c.policy (island 3) with policies/candidates/hyb5-g3-82.policy, i.e.
   `--island-seeds policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/v20.policy,policies/candidates/hyb5-g3-82.policy`
2. `--protect-islands 3` (island 3 never re-seeded at island resets, never a donor)
3. `--fuel-islands 3` (each island-3 child, and its seed, gets a 4-game fuel_turns --enforce --bot-seeds check on
   01big-world + 00ambush vs v21, ~3 s; score -= 0.01 x suspensions/game + 0.001 x (turns >= 90k per game - 6);
   raw score and fuel numbers in metrics.fuel)
4. `--island-axes "3=fuel:5,conversion:2,pairs:1,disengage:1"` (island 3's axis menu; other islands keep --axes)
Check: hyb5.log shows "re-seeded island 3 with hyb5-g3-82 (score ~0.50)" (penalised; raw ~0.70 is in metrics.fuel);
island-3 children carry metrics.fuel; about half of island-3 children log axis "fuel".

## Job H18 (2026-10-24 16:00 UTC, hybrid line session; per the FunSearch lead): capture-yield fitness, all islands
Fold into the H16/H17 pull if it has not happened (one pull), else the next boundary. Require funsearch/runs fc797d0
or later (contains 27dd4a2). Python only beyond H16/H17. Add to the relaunch (run args):
`--yield-weight 0.25` (defaults: --yield-ref v21 --yield-scale 3 --yield-floor 0.34)
score = 0.75 x usual + 0.25 x (0.5 + 0.5 x clip((our gems/capture - v21's, in the screen games vs v21) / 3, -1, 1)),
minus 1 when the screen win rate vs v21 is below 0.34 - 2 standard errors. Island 3 keeps its fuel penalty on top.
v21 must stay a screen opponent (it is: the league's members include it). Programs already in runs/hyb5-g3 are
rescaled in memory at startup. Check: hyb5.log prints "yield term: N logged programs rescaled"; new children carry
metrics.yield {gpc_diff, term, raw_score, ref_win, below_floor}. Promotion is unchanged (h2h vs the best).

## Job H19 (2026-10-24 16:05 UTC, hybrid line session; per the FunSearch lead): group_rate sensor
Fold into the H17/H18 pull if it has not happened (one pull), else the next boundary. Require funsearch/runs fce1ade or
later (contains fc797d0). It merges deploy/v0 ec9778c: group_rate(Tile) with its calibrated cost row (~564 + 29/camp;
16 sensors, 0 provisional rows). interp/ and sim/ CHANGED: rebuild interp_eval + fuel_turns, pytest (2029). Same
command line as H17/H18; group_rate joins the vocab-variant list automatically.

## Job H20 (2026-10-24 16:20 UTC, hybrid line session; per the FunSearch lead): ladder v23 (style-gconv1)
Fold into the H17-H19 pull if it has not happened (one pull), else the next boundary. Require funsearch/runs dccd4b1 or
later (contains fce1ade). It merges deploy/v0 84bc6a6 (v23 = policies/candidates/style-gconv1.policy, v21 + sensor-
driven banking; sim fix 13894d4: nearest_by_walk from an off-map origin). sim/ CHANGED: rebuild interp_eval +
fuel_turns, pytest (2029). Relaunch changes (on top of H17/H18):
1. League arg: add policies/pool/style-gconv1.policy to --fixed (comma-separated with any current --fixed entries).
2. --island-seeds: replace island 1's v21 with style-gconv1, i.e.
   `--island-seeds policies/pool/v21.policy,policies/pool/style-gconv1.policy,policies/pool/v20.policy,policies/candidates/hyb5-g3-82.policy`
   (island 0 keeps v21 first: the fuel checks and the bar use it.)
The bar stays v21 (no change to members/best); --yield-ref stays v21.
Check: "re-seeded island 1 with style-gconv1"; new children's metrics include a "style-gconv1" opponent.
