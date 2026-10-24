# Handoff: PURE FunSearch line

Updated 2026-10-24 ~17:40 UTC by session_01Rbeaeb1EjHHutSParz5EPd (reports to the FunSearch lead,
session_01YJxccSM2xmnTtoiFjrAzf3). Branch: `funsearch/pure`. Read `CLAUDE.md`, `docs/STRATEGY.md`,
`docs/FUNSEARCH.md` and `docs/REMOTE_WORKER.md` (on main: the arena) first.

## Purpose (Cham, 24 Oct): improve the training loop, not produce a winning bot

Pure is the loop testbed and control:
- No hand-written policy code as seed or parent (lineage only from FunSearch outputs). Hand-written bots
  may be opponents.
- No analysis-derived gap sensors (the 13 gap blocks are merged on the tip but are NOT run for pure).
- Fixed opponent pool and fixed build for comparability: g5 set = tune-v20-L1c (v21), v5d, v4, locker,
  fs-2, opp-hunter3 (+ best at weight 3, builtin:starter 0.25), build funsearch/pure 0af36c4 (deploy/v0
  dc15600 + lockfix). Do not swap in new live bots; do not mix builds across A/B arms.
- Loop changes go in one at a time and are measured per arm: validated h2h gain vs the previous best per $
  and per hour, invalid rate, promotion rate, $ used. Post a results table on PR #2 and a one-line
  summary to the lead after each comparison.

## Lineage and strength

fs-1 -> pure4-g1 #155 = fs-p1 -> pure4-g2 #140 = fs-p2 -> (g3: no promotion) -> pure4-g4 #147 = fs-p3
-> (g5: no promotion). Round robin on 0af36c4 (400 fresh games): fs-p1 vs fs-1 86.8%; fs-p2 vs fs-p1
67.7%; fs-p3 vs fs-p2 66.2%, vs fs-p1 76.7%, vs fs-1 93.2%. vs v21: 12.0 / 14.2 / 21.5%; vs hunter3:
23.3 / 31.0 / 42.0%. fs-p3 cambc-exact vs v21 0.175. fs-p3 is registered in the arena as `fs-p3`
(engine deploy/v0 545c7b1).

## Loop A/B results so far (PR #2)

1. Offline g4 replay ($0, `funsearch/loop_ab.py`, `runs/ab-g4.json`): per-child climb (funsearch/runs
   settings) accepted mutations on 2/24 children (+0.034/−0.021, noise) at +30–40% time per program;
   league tuning stage (`--stage-tune-steps`, top 3, 6 steps x 8 games + holdout) kept 0/3 at +13% of
   validation time. Both OFF.
2. g5 baseline (no loop changes): $3.06, 3.75 h for 151 programs, 12.2% invalid, no promotion: top
   screens 0.611–0.616 > fs-p3's 0.578 but validated h2h vs fs-p3 only 0.475–0.490 (screen over-selects).
3. Running: screen A/B (`--arms screen`, `runs/ab-g4-screen.json`): the screen uses seed 0 = 14 of 40 maps,
   the same for every program; `evaluate(stratify=True)` tiles all maps across opponents at the same
   games. Compared against an all-maps x both-sides truth on 60 g4 programs.
Next (lead's order): live A/B for `--helpers funsearch/helpers-pure.json` (built from pure runs only),
equal $ per arm, same parent/seeds/opponents; the stratified screen as default if A/B #2 favours it.

## Where things run

- **EC2** (`ec2/runner`, `runner/lines/pure.sh`, state pushed to `remote/pure`, mirrored): pure4 league,
  g5 extension on 0af36c4 with the old cap; it stops at "budget spent" soon. The runner file holds several
  one-shot blocks (advance without promotion, opponent syncs, lockfix build switch, a DISARMED tune restart,
  stale-STOP cleanup); read it before changing anything. Promotions there are committed to funsearch/pure
  by hand from `remote/pure` (the league's own push fails on the detached HEAD).
- **Arena** (Cham, 24 Oct; replaces the remote/pure -> jobs/pure PR channel and JOBS.md): matches, batches,
  leagues now (`X-Arena-Client: pure`, leagues at priority -1). FunSearch runs there need a pure
  ARENA_TOKEN from Cham (asked for via the coordinator); never put it in the repo or a message. Until a
  token exists, FunSearch runs stay on EC2.

## Budget

Pure line cap $30 (raised from $20 by the lead for the A/B work). Spent ~$15.5: 0.28 (pure/pure2/pure3) +
9.71 recorded/lost on remote-server (it kept running after the 04:15 snapshot until 09:16 UTC) + ~5.5 on
EC2 (g3 rest, g4, g5). League `--budget` 15.15 in `runs/pure_launch.sh` reflects the old $20 cap; the A/B
arms are funded from the extra $10. `runs/SPEND.md` is current through the remote-server correction.

## Code on funsearch/pure (vs funsearch/runs)

- `funsearch/league.py`: pure's own (lineage header, `--policy-prefix/--line/--session`, cambc gate and
  `--cambc-also`, frozen per-generation fixed/target, validation cache) + the tuning stage
  (`--stage-tune-steps/-games/-k`, off).
- `funsearch/run.py`, `llm.py`, `tune.py`: funsearch/runs 41e1191 (per-child climb `--tune-*`, `--helpers`);
  llm.py's "already in the current best" paragraph describes fs-p3; tune.py also has `tune_named`.
- `funsearch/evaluate.py`: `stratify=True` option. `funsearch/loop_ab.py`: offline A/B arms.
- `funsearch/catalog.py`: funsearch/runs aa032ba + merged block docs (gap blocks listed on the tip, so a run
  from the tip WOULD show them: pin a pre-gap-block commit such as f27e0e2 / 0af36c4 for pure runs).

## Things only I know

- `runs/pure4-g2-b`, `pure4-g3-oldbuild`, `pure4-g5-oldbuild` are abandoned but counted by `spent('pure4')`
  (glob `pure4-g*`); keep them.
- Stale STOP files once appeared in remote/pure because push_state did not mirror deletions; fixed
  (ec2/runner e2336dc).
- fs-p3 vs v21 numbers taken before the lockfix merge (0.45) were build artifacts; use 0.175.
