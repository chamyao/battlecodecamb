# Handoff: STYLE FunSearch line

Written 2026-10-24 ~03:45 UTC by the outgoing STYLE session (session_01V26XD9N15L34L9j3pMnVNC).
Branch: `funsearch/style` (code + directives). Read `CLAUDE.md` and `docs/STRATEGY.md` first (core
principle: compute is part of the action space; fuel is a rule, not a constraint).

## Arena (current; read this before the older sections below)

- Engine for new work: deploy/v0 `ca8f85bf63d15abf15d26a966f911ed6c4913011` (18:27 UTC: adds
  monolith_threat, in_monolith_zone, altar_safe_tiles, camp_threat ~7k). Before it: 2e1ff7e (fuel
  recalibrated), 545c7b1 (under-charged fuel by 1-4k). Never compare results across engines; pass
  `"engine"` on every registration and match. funsearch/style carries ca8f85b from c282ae6.
- **bot_seeds:true (the arena default) is deterministic**: 800 games = the same 80 (40 maps x 2
  sides) repeated, whatever the seed. Use `"bot_seeds": false` for sample size.
- The arena's `client.py` is a download; this container's permission policy blocked running it,
  so call the API with `curl` + JSON bodies (POST /policies, /matches, /batches,
  /leagues/main/members; `?wait=N` long-polls).
- Registered by style (compile-checked on 545c7b1 and 2e1ff7e): opp-finisher, opp-hunter3 (= style-h1), opp-hunter2a/b/c,
  opp-hunter-stack. Live lineage is already there (`v22-tune-v20-L1c` = live = our v21 reference
  tune-v20-L1c; `v23-style-gconv1` = style-gconv1). Names are immutable: a changed policy gets a
  new name.
- Candidate checks: 800 games vs `v22-tune-v20-L1c` (floor 50%) as a match; then
  `POST /leagues/main3r/members {"policy": NAME}` (upload-bar league `main3r`: engine ca8f85b,
  bot_seeds false, 160/pair, required pool included; `main`/`main2` are retired) (priority -1) and post standings on PR #5.
  Real-cambc checks and uploads stay with the coordinator (each upload needs Cham's go-ahead).
- EC2 is retired for style (17:47 UTC; final state on `style/arena-overlay` 391f2d4). Arena runs (no
  token needed): run 5 style8-gsub2 ($1.00, --strict-floor, ref 1784c8d = engine 2e1ff7e) and run 6
  style8-b2 (league resumed from the overlay, $0.95 total). Logs/files: GET /runs/<id>/log,
  /runs/<id>/files/runs/... Style cap $13.85 (final; runs/SPEND.md).
- **Candidate 7 (cleared the upload bar, 19:06 UTC): policies/candidates/style-gsub2-11k33.policy** = v21 +
  fuel-gated rich-group camp choice (gsub2 #11, hand fuel fix -> 11k) + any bag tributes at an adjacent altar
  (gsub2 #33). main3r 1707.9 vs live 1677.1 (+31, 90% +10..+49 by my bootstrap; lead +15..+51); cambc
  safety passed (bot session); upload awaits Cham. Backup style-gsub2-11k27 (+27, 90% +8..+45; cambc safety
  passes: 0 caps, first turn 182.7k; but 36/80 vs live's ZIP, where 11k33 goes 44/80; dist/deploy-style-gsub2-11k27.zip 1afae26).
  11k alone +12.6 (-5.8..+32): not clear. Fuel lesson: a second closest() (~28k) needs > 72000 left; 60000
  caps, 80000+ never fires; a Chebyshev pick without the walking search walks into unreachable camps.

## Goal

Explore policy styles nobody on the team plays, so (1) we may find a stronger style and (2) the
league gets varied opponents. Three islands, each = a FunSearch league run with an extra style
directive in every prompt:

| Island | Style | Directive | Style check (`--require`) |
| --- | --- | --- | --- |
| a | Lockdown: buy/place altar locks on altars the enemy uses, guard them | `funsearch/styles/a_lockdown.txt` | `buy_altar_lock,place_altar_lock` |
| b | Team fights: claims, regroup, focus fire (`set_team_target`), kite divers | `funsearch/styles/b_teamfight.txt` | `set_team_target,team_target` |
| c | Late monolith: build up, take monoliths with 3-4 champions after ~round 1000 | `funsearch/styles/c_monolith.txt` | `monolith_tiles,claim_count` |

All three directives also carry the camp-value/skip direction:
skip goal g when `group_threat(g) * group_hp(g) / (my_dps * (1 + allies_within(4))) > health()`.

Rules: promote a style only if it beats the current bar by +5 points head to head on 2 x 400
fresh games (league `--z 2.83`) AND cambc-exact (`interp_eval --bot-seeds`, all 40 maps x 2
sides; league `cambc_check`) >= 0.55 vs the bar. Save as `policies/style-<a|b|c><n>.policy` with
header `# line: style-<x>`. Also send the coordinator (session_01S2SPSVky6e84fDzQLxJKWp) any
style that is merely competitive (45%+ vs the bar over 800 games) but plays very differently
(useful league opponent). Never submit to the ladder. Score at fuel_mult 1.0, fresh per-game seeds.

## Current base / bar

- Seed, weight-3 opponent and cambc-exact opponent: `policies/tune-1.policy` (ladder v11).
- Fixed opponents: v7zg-cast, v5d, v4, locker, fs-2; starter at weight 0.25.
- Newer ladder versions exist (tune-3 v2 was called "live version 15"; the pure line already uses
  tune-3 as fixed). **Open question for the coordinator: switch the bar to the current live
  policy at the next boundary.**

## What's running and where

- Runs execute on Cham's server ("remote-server"), in `~/bc/style`, started by
  `WORKERS=1 EVAL_THREADS=2 VAL_THREADS=4 sh runs/style_checkin.sh` (3 islands, ~6 threads; the
  machine is shared with hybrid/pure/tune). Started ~03:35 UTC at commit a2ed626.
- Run names: leagues `style6-a`, `style6-b`, `style6-c`; FunSearch runs `style6-{a,b,c}-g1`
  (logs `runs/style6-X.log` for league/validation lines, `runs/style6-X-g1.log` per child,
  `runs/style6-X-g1/programs.jsonl` = database, resumable).
- Launcher `runs/style_launch.sh <x> <budget>`, budgets in `runs/style_budgets` (2.3 each; the
  league subtracts spend already in programs.jsonl, so the cap is per island in total).
- Talking to remote-server (Oct 24, 17:30 UTC on): **the arena**, see `docs/REMOTE_WORKER.md` on
  main and `$ARENA_URL/docs` (`ARENA_URL=https://138-201-121-171.sslip.io/arena`, header
  `X-Arena-Client: style`). Matches, batches, leagues and policy registration need no token;
  FunSearch runs and run-file writes need a token from Cham (never commit or print it). The old
  draft-PR channel (PR #3, `remote/style` -> `jobs/style`, `jobs/style/JOBS.md`) and the EC2
  runner are retired for new work: no new jobs there.
- Snapshot of state at the move (55/115/75 programs): branch `funsearch/style-state`
  (run data only; overlay with `git checkout origin/funsearch/style-state -- runs/`).
- Nothing runs in the cloud container any more. Do not start islands there (double spend).

## Scores (run score = weighted pool score; seed tune-1 = 0.779)

At the move (03:30 UTC): no validation round yet in style6.

| Island | Children | Best run score | Spend |
| --- | --- | --- | --- |
| a lockdown | 55 | 0.751 | $0.92 |
| b team fights | 115 | 0.770 | $2.08 (cap nearly reached: validation soon) |
| c late monolith | 75 | 0.761 | $1.56 (server reported 71 progs, $0.74 left) |

Validation happens automatically when a run stops (150 programs or budget): top 3 distinct vs
starter + league on 2 x 400 fresh games, then cambc check. Watch `runs/style6-X.log` for
"run score", "h2h", "cambc", "PROMOTED". The league's own commit/push of a promoted policy may
fail on the server; get the policy text from `remote/style` or the PR and commit it yourself.

## Budget

Line cap $10 (FUNSEARCH_* key on the machine, base URL api.anthropic.com; never print it).
Spent: $7.65 (style-test 0.01, style-g1 0.30, style5 2.78, style6 4.56 at the move; logged in
`runs/SPEND.md` up to style5). Left: ~$2.35, all already allotted to the style6 islands
(a ~$1.38, b ~$0.22, c ~$0.74). When style6 ends, the line is out of budget unless the
coordinator grants more. Update `runs/SPEND.md` with the final style6 numbers.

## What was tried (numbers)

- Restarts: the bar moved v5d -> v7 -> v7-zerogem -> v7zg-cast -> tune-1, and the sim was
  re-profiled several times; earlier rounds (style-g1, style2-4) were dropped with little spend.
- style5 (vs v7zg-cast, 163 programs, $2.78): no child beat the seed's run score (0.780). Its top
  3 per island, re-validated vs tune-1 on the 340ce89 refit (400 fresh games each):
  lockdown 39.3-44.5% (best #11; 800 games: 40.7%), team fights 35.5-41.0%,
  monolith 39.5-41.7%. Nothing competitive enough to send.
- Fuel: on the old sim many children showed 8-26 out-of-fuel turns/game; on the 340ce89 refit
  they are 0-0.9. Those were sim artifacts, not real waste.
- Lockdown first child (style-a-g1 #6, vs v5d pool): 49% vs v5d, 46% vs fs-2 — the style is
  viable, but locks near the enemy spawn alone don't beat a strong farmer. Weakness seen in that
  code: our carriers avoid all `locked_altars()`, including our own locks (we can tribute there).
- Team-fight island: requiring `claim_count` rejected 8/9 children; requirement relaxed to the
  focus-fire blocks. One team-fight child scored 0.027 (broken), so its variance is high.
- `strength()` was not a block until interp/v0 ~d6ccb94; catalog/directives now use `my_dps`
  (keep my_dps = 60). Only 2/81 children had failed on it.
- Island a (lockdown) evaluates about half as fast as b/c (fewer children per hour).

## Open leads / next steps

1. Watch style6 validations (b first). On a promotion or a 45%+ style: verify cambc-exact >= 0.55,
   commit the policy with the header, report to the coordinator.
2. Next boundary (checklist in `runs/style_next_boundary.md`): merge interp/v0 (strength()/focus()
   real blocks; fuel_remaining() now works in cambc; calibrated within-turn fuel) and
   funsearch/runs; drop the "strength() does not exist" wording from catalog.py and the directives;
   add the fuel_remaining()-gate direction (skip optional expensive steps on heavy turns); switch
   the bar to the current live policy; restart as style7-* (new run names) via JOBS.md.
3. Lockdown ideas: prefer our own locked altars for our tributes; lock only altars near enemy
   carriers; one dedicated locker rather than a random 1-in-3 role.
4. Monolith ideas (from the coordinator's loss analyses): captures yield ~15 gems vs 21-60 for
   teams beating us; one winner took both monoliths on 01big_world (+456 gems). Avoid monolith
   zones (`group_tiles(monolith_tiles())`) only where they are not the main income; v8/monozone
   avoidance is strongly map-dependent (77.5% big-world, 7.5% gold-rush).
5. If budget is exhausted, ask the coordinator before any further Claude spend.

## Code on this branch (opt-in flags; HYBRID merges them into funsearch/runs)

- `funsearch/run.py`: `--directive TEXT|@file`, `--require b1,b2`, `--fresh-seeds`.
- `funsearch/llm.py`: `Proposer(directive=)` (sent after the parent versions, keeps cache hits).
- `funsearch/league.py`: `--session`, `# line:` header with `--line`; z-test promotion + cambc
  check come from funsearch/runs.
- `runs/style_launch.sh`, `runs/style_checkin.sh`, `runs/style_push_state.sh`, `runs/style_budgets`.
- Gotchas: `pgrep -f`/`pkill -f` with the pattern inside a shell command line matches your own
  shell; stop runs with SIGTERM (SIGINT can hang the thread pool).
