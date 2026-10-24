# Handoff: PURE FunSearch line

Updated 2026-10-24 ~17:40 UTC by session_01Rbeaeb1EjHHutSParz5EPd (reports to the FunSearch lead,
session_01YJxccSM2xmnTtoiFjrAzf3). Branch: `funsearch/pure`. Read `CLAUDE.md`, `docs/STRATEGY.md`,
`docs/FUNSEARCH.md` and `docs/REMOTE_WORKER.md` (on main: the arena) first.

## STATUS 19:30 UTC: ALL TRAINING PAUSED by Cham. Start no FunSearch runs (incl. the A/B arms) until he resumes.
Latest pure4 state: branch pure/arena-state da35ac4 (g5 at 207 programs, target 301, $0.16 left under --budget 15.15).

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
(engines deploy/v0 545c7b1 and 2e1ff7e; the live comparison league is `main2` on 2e1ff7e).

Fuel caveat: on arena engine 2e1ff7e (recalibrated fuel) fs-p3 averaged 307 fuel suspensions per game on
00ambush (arena match 150). Pure's pinned build under-prices fuel, so the lineage evolved fuel-heavy play.
Lead: keep the current A/B arms on the pinned build; the NEXT comparison series starts on a build >= 2e1ff7e
with the baseline re-run there.

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
   RESULT: stratified wins (Pearson 0.83 vs 0.77, Spearman 0.725 vs 0.655, bias −0.003 vs −0.062, top-5 3 vs 2).
   `funsearch.run --stratify` (screen only) is on branch funsearch/pure-ab d85a9d8 (= f27e0e2 + flag) and is pure's
   default screen from now on (lead).
Next (lead's order): live A/B for `--helpers funsearch/helpers-pure.json` (built from pure runs only),
equal $ per arm, same parent/seeds/opponents: arena arms pab-ctl / pab-hlp on ref d85a9d8 with --stratify, $3.2 each.

## Where things run

- **EC2** (stopped and HALTed 17:45 UTC; final state on `pure/arena-state` 4a4aeb6, runs/ at the root) (`ec2/runner`, `runner/lines/pure.sh`, state pushed to `remote/pure`, mirrored): pure4 league,
  g5 extension on 0af36c4 with the old cap; it stops at "budget spent" soon. The runner file holds several
  one-shot blocks (advance without promotion, opponent syncs, lockfix build switch, a DISARMED tune restart,
  stale-STOP cleanup); read it before changing anything. Promotions there are committed to funsearch/pure
  by hand from `remote/pure` (the league's own push fails on the detached HEAD).
- **Arena** (Cham, 24 Oct; replaces the remote/pure -> jobs/pure PR channel and JOBS.md): matches, batches,
  leagues now (`X-Arena-Client: pure`, leagues at priority -1). FunSearch runs there need a pure
  ARENA_TOKEN from Cham (asked for via the coordinator); never put it in the repo or a message. No token is
  needed for runs any more (caps $16/run, $60 total). Arena runs (17:55 UTC, ref f27e0e2): #7 pure4 resume
  (overlay pure/arena-state), #8 pab-ctl, #9 pab-hlp (+ --helpers), all --no-tune-children, 4 threads each. After g5's extension, pure's runs
  move to the arena on a pure engine built from a pinned funsearch/pure commit (POST /engines), both arms on it.

## Budget

Pure line cap $30. Spent ~$19.61: 0.28 (pure/pure2/pure3) + 4.57 lost on remote-server (it ran past the 04:15
snapshot until 09:16 UTC) + 14.76 recorded in pure4 programs (5.14 before the snapshot + 9.62 on EC2). Committed in
the arena: pure4 resume <= 0.39 (league --budget 15.15) + A/B arms 3.2 + 3.2. `runs/SPEND.md` is current.

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
