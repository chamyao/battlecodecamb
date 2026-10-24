# Handoff: PURE FunSearch line

Written 2026-10-24 ~04:15 UTC by the outgoing pure-line session (session_019SuVFgxah8yS3STZJvAcWX).
Branch: `funsearch/pure`. Read `CLAUDE.md`, `docs/STRATEGY.md` (core principle: compute is part of
the action space; fuel is a rule, not a constraint) and `docs/FUNSEARCH.md` first.

## Goal and rules of the line

- FunSearch where programs descend only from FunSearch outputs. Seed was `policies/fs-1.policy`;
  parents always come from this line's own database. No hand-written policy (v3, v4, v4a, v5, v5d,
  tune-*, v7*) and nothing descended from one (fs-2, v5d-fs2, v7zg-cast, ...) may be a seed or
  parent, and their code must never be copied. They may be opponents.
- Promoted bests: `policies/fs-p<n>.policy`, header `# line: pure` plus `# lineage:` (the league
  writes both).
- Scoring (same for both FunSearch lines): own current best at weight 3; fixed opponents from
  `runs/pure_fixed.txt` (now tune-3, v5d, v4, locker, fs-2); `builtin:starter` at weight 0.25.
- Promotion: >= +5 points head to head vs the current best on 2 x 400 fresh games (per-game seeds,
  not `--bot-seeds`), no drop > 3 points vs any fixed opponent, AND cambc-exact (all 40 maps x 2
  sides with `--bot-seeds`, reproduces real cambc) >= 0.55 vs the current best. Always fuel_mult 1.0.
- Ladder candidate (report to the coordinator as one) only if cambc-exact vs the live ladder bot
  (`runs/pure_send.txt`, now tune-3) >= 0.55. Never submit to the ladder yourself.
- Budget: $10 for the line, Claude API key in env as `FUNSEARCH_API_KEY` (never print it; base_url
  pinned in `funsearch/llm.py`). Log spend in `runs/SPEND.md`. Model mix: Haiku 5.5, every 10th
  call Opus 5.5.

## Current base policy

`policies/fs-p2.policy` (commit 050e389): fs-1 -> pure4-g1 #155 = fs-p1 -> pure4-g2 #140 = fs-p2,
both Haiku children. Both carry a stray Haiku-written comment line `# v2: ...` in the body; it is
NOT v2's text (checked with `git log -S`) and does not affect play.

| policy | h2h vs parent (800 fresh) | starter | v5d | v4 | locker | fs-2 | tune-1 | cambc-exact vs parent | vs tune-3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fs-p1 | 87.0% vs fs-1 | 94.8% | 51.7% | 62.4% | 86.9% | 52.5% | 31.25% (cambc) | 0.8625 | — |
| fs-p2 | 69.2% vs fs-p1 | 98.2% | 64.2% | 73.6% | 87.9% | 69.2% | 38.4% | 0.650 | 0.3625 |

fs-1 vs tune-3 class bots is ~0.09-0.11 cambc-exact; the line has gained a lot but is far from the
0.55 send bar against tune-3.

## What is running, where

- League name `pure4`, generation 3 (`runs/pure4-g3`), best fs-p2, target 151 programs
  (`runs/pure4.json`: `{"gen": 3, "members": ["policies/fs-p2.policy"], "fixed": [...tune-3...],
  "target": 151}`). At handoff g3 had 11 programs (best #9 screen 0.640, seed fs-p2) and was
  STOPPED in the cloud container for the move to remote-server.
- Launcher: `runs/pure_launch.sh` (league `pure4`, `--budget 9.71` which nets out $0.28 spent by
  the earlier pure/pure2/pure3 runs; `--workers 3 --eval-threads 2 --threads 5`; fixed opponents and
  send check read from `runs/pure_fixed.txt` / `runs/pure_send.txt` at each new generation).
  Resumes from disk; `touch runs/pure4-g<k>/STOP` pauses gracefully.
- Move to remote-server (Cham's Ryzen box, Remote Control session "remote-server"): setup steps
  were sent at ~03:40 asking it to clone into `~/bc-pure`, checkout `funsearch/pure` (state also on
  `funsearch/pure-state` @699942e), build `interp_eval`, `pytest -q tests`, sanity check
  `cambc_check(fs-p2, tune-3) == 0.3625`, then `setsid nohup runs/pure_launch.sh >> runs/pure.out`.
  **Unconfirmed**: no report came back, `remote/pure` still has only the STATUS.md placeholder and
  PR #2 has no comments. First thing to do: check whether it is running there (see next section).
  Do NOT run the league in a cloud container at the same time (double spend, conflicting pushes).
- Talking to remote-server: use the GitHub protocol in `docs/REMOTE_WORKER.md` on `main`, not
  session messages. Channel = draft PR #2 (`remote/pure` -> `jobs/pure`, "[remote] pure");
  subscribe to it; write durable instructions to `jobs/pure/JOBS.md` (currently the empty initial
  file, so it does "keep running what is already running"). Its status goes to
  `remote/pure/STATUS.md`. If it never launched, write the launch steps above into JOBS.md
  (adapted to the protocol: it pushes state to `remote/pure`, not `funsearch/pure`).
- `runs/pure_checkin.sh` no longer relaunches anything (league is remote); local check-ins only
  read.

## Budget

Spent $4.82 of $10 (pure-g1 0.16, pure2-g1 0.10, pure3-g1 0.02, pure4-g1 1.75, pure4-g2 first
attempt 0.59, pure4-g2 2.02 incl. 0.01 of discarded g3, pure4-g3 0.18 so far). Left ~$5.17 (the
league's own `spent('pure4')` = 4.54 against its 9.71 cap). A generation of ~150 programs costs
~$1.7-2.0, so about 2.5 more generations. `runs/SPEND.md` is up to date through pure4-g2; add
pure4-g3 when it ends.

## Code changes on funsearch/pure (vs funsearch/runs)

All in `funsearch/league.py`: `--policy-prefix`, `--line` (lineage header), `--session`;
`cambc_check()` with `--cambc-min` (gate vs best) and `--cambc-also @file` (logged vs ladder bot);
`--fixed @file` re-read each generation and frozen per generation in the state; a per-generation
`target` program count in the state so a resume after a restart does not restart the round count
(this bug cost a lot before: each resume ran 150 more). funsearch/runs has since grown its own
features (validation cache on disk b441fe6, challengers 23a1f27, logging of failed evals b927b5d);
they are NOT merged here. Merging funsearch/runs' league.py will conflict with mine; resolve by
keeping both feature sets, or port the validation cache (useful: container restarts redid
validation games).

`funsearch/catalog.py` = funsearch/runs @22cbdf1 version (strength() is a real block; KEY TOOL camp
skip formula; fuel_remaining() gate note; tuning exhausted -> structural camp choice). Build:
interp/v0 @5287a08 (strength()/focus(), working fuel_remaining, calibrated within-turn fuel timing,
group_gems/threat/hp, rich_spawns, group_tiles). interp/v0 now has b23330e (tune-5 policy only).

## What worked / didn't (numbers)

- Worked: Haiku children with Opus every 10th; best programs of g1/g2 were Haiku. pure4-g1 took
  fs-1 (0.339 screen) to 0.726 confirmed (#104), promoted #155 at 87% h2h. pure4-g2 on the
  group_threat build went 0.593 -> 0.729 (#140), promoted at 69.2% h2h. g2's top programs used
  `group_threat` (camp-skip direction landed).
- Prompt bug: the skip formula used `strength()` before it existed: 16 of ~80 g2 children failed
  "no block strength()". Fixed (now strength() is real). Invalid rate otherwise ~3-10%.
- Restarts wasted a lot: five fresh restarts (pure, pure2, pure3, pure4-g2-b, g3 discard) for sim
  re-profiles / opponent changes, ~$0.9 total. Only merge interp/v0 at generation boundaries,
  and after a promotion stop the new generation immediately, merge, rebuild (cmake configure
  first), move the new gen dir aside, drop "fixed"/"target" from `runs/pure4.json`, relaunch.
- Sim trust: my build reproduces real cambc exactly where checked: v7 vs v5d-fs2 0.5875, tune-1 vs
  v7zg-cast 0.6125, tune-3 vs tune-2 0.500 (real 39/80).
- Validation noise: confirmed (160-game) scores of the top programs cluster within ~0.01; the
  2 x 400 validation always picked one clearly (h2h 0.67-0.87). Candidates #2/#3 of a round are
  rarely better than #1.

## Open leads / next steps

1. Confirm remote-server runs pure4-g3 (PR #2, `remote/pure`); if not, launch it via JOBS.md.
2. At the next boundary: merge origin/interp/v0 (tune-5 policy) and consider funsearch/runs'
   league improvements; ask whether tune-5 is the live ladder bot; if so swap it into
   `runs/pure_fixed.txt` and `runs/pure_send.txt`.
3. The gap to tune-3 is the draft and camp choice: fs-p2's draft is still fs-1's (vesper_vale,
   else random). The prompt hints a fixed draft chain; nothing in the pure line has found one yet.
   A deliberate available() chain is the cheapest big lever and stays pure if the model writes it.
4. fuel_remaining() gates are free now (2-9 fuel); no pure child uses them yet.
5. When the budget nears its end, the league stops itself (`budget spent`); write the last
   SPEND.md row and a final report (best policy, cambc-exact vs ladder bot).

## Things only I know

- `runs/pure4-g2-b` (42 programs, first g2 attempt on 9a0ac5b prices) and `runs/pure4-g3-oldbuild`
  (6 programs) are abandoned but counted in `spent('pure4')` because the glob is `pure4-g*`; don't
  delete them or the budget accounting under-counts.
- League log lines "cambc-exact vs ..." are only computed for candidates that already pass h2h and
  regression, so absence means the candidate failed earlier.
- `top_distinct` takes the 3 best by confirmed score; validation of 3 candidates plus the bar takes
  ~25 min at 4 threads.
