# Jobs for remote-server: style line

Written by the FunSearch lead session (the style line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/style`, branch `funsearch/style`.

## Job S1 (2026-10-24 04:50 UTC): let style6-{a,b,c} run to their end. Do not start style7.

- style6 runs to its budget and validates on its own; keep it as it is.
- When each island's league exits (budget spent or a promotion), push state to `remote/style` and
  comment on PR #3 with that island's validation lines ("h2h", "cambc", "PROMOTED").
- Do not launch style7 or any new run: the line is out of budget until the lead writes a new job here.

## Job S2 (2026-10-24 ~05:00 UTC): style7 vs tune-5. HELD again (05:12 UTC): do not act until this line reads "APPROVED"

Status: HELD. The directives are being changed (the camp-skip formula is out). The line will name
the new commit here and comment on PR #3.

Supersedes S1's "do not start style7" ($2 granted for style7). Start only after
ALL THREE style6 leagues (style6-a, -b, -c) have exited and their validation lines (h2h, cambc,
PROMOTED) are pushed to `remote/style` and commented on PR #3 (job S1). Then, in `~/bc/style`:

1. `git fetch origin funsearch/style && git checkout funsearch/style && git merge --ff-only origin/funsearch/style`
   (expect 1b03fa5 or later). Keep the untracked `runs/` data: style7 uses new run names.
2. `cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j4 --target interp_eval`
   then `python3 -m pytest -q tests` (expect 2012 passed). On a failure, stop and comment.
3. `WORKERS=1 EVAL_THREADS=2 VAL_THREADS=4 sh runs/style_checkin.sh` (needs FUNSEARCH_API_KEY in
   that shell; never print it). It launches style7-a/b/c (seed/bar/cambc-ref policies/tune-5.policy;
   budgets a 0.9, b 0.5, c 0.6 from runs/style_budgets). Same thread use as style6.
4. Comment on PR #3 that style7 started (commit, process list), and push status/state to
   `remote/style` as for style6. On each league exit, comment its h2h/cambc/PROMOTED lines.
