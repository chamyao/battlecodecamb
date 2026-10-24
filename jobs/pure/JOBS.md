# Jobs for remote-server: pure line

Written by the FunSearch lead session (the pure line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `/root/bc-pure`, branch `funsearch/pure`.

## Job P1 (2026-10-24 04:50 UTC): tune-5 (live ladder v16) replaces tune-3 from pure4-g4. No restart.

1. `git pull origin funsearch/pure` (to 56de9fe or later): adds `policies/tune-5.policy` only (merge of
   interp/v0 b23330e). Simulator unchanged: no rebuild, and do not stop the league.
2. In `runs/pure_fixed.txt` and `runs/pure_send.txt` replace `policies/tune-3.policy` with
   `policies/tune-5.policy` (all other lines unchanged).
   The league re-reads both files: pure_fixed at the next generation (g3 keeps its frozen
   opponents), pure_send at the next promotion check.
3. Push state to `remote/pure` and comment on PR #2 with the two files' contents.

## EC2 resume (2026-10-24 06:10 UTC, pure line session_01Rbeaeb1EjHHutSParz5EPd)

For the EC2 runner (c7a.4xlarge, 16 threads). Resumes pure4 generation 3 where Cham's machine left
it. **Update 06:40 UTC (Cham via the lead):** remote-server's runs after the snapshot are
discarded, so resume from the `remote/pure` 04:15 UTC snapshot as it is (3e8dfad: 49 lines in
`pure4-g3/programs.jsonl`). Their API spend was real but is unrecorded, estimated at ~$1.62, so the
league budget is **18.10** for g3 and g4 ($20 line cap from 06:35 UTC - 0.28 earlier runs - 1.62 lost); see `runs/SPEND.md` on funsearch/pure bbea6ee. Only one
machine may run pure4: if remote-server's league is still alive, it must be stopped.

### Why g3 runs at 81ab84b and not at the tip of funsearch/pure

`funsearch/pure` d5dbfa1 changes the LLM prompt (it replaces the KEY TOOL camp-skip formula). That
change is for g4 and later, never mid-generation. A fresh `funsearch.run` process reads the prompt
at start, so finish g3 at **81ab84b**. That commit has tune-5.policy and the validation cache, but
not the prompt change. Pass `--max-generations 3` so the league exits right after g3's promotion.
Pass `--no-commit` because promotions can't be pushed from a detached HEAD.
If g3 validation does not promote, the league itself extends g3 by 150 more programs, still on
the old prompt; that is correct.

### 1. Checkout, build, tests

```sh
git clone https://github.com/chamyao/battlecodecamb ~/bc-pure && cd ~/bc-pure
git checkout 81ab84b
pip install anthropic pytest            # plus whatever docs/FUNSEARCH.md lists
cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j16 --target interp_eval
python3 -m pytest -q tests              # ~2012 passed on remote-server
python3 -c "from pathlib import Path; from funsearch.league import cambc_check; print(cambc_check(Path('policies/fs-p2.policy').read_text(), 'policies/tune-3.policy', 16))"
# must print 0.3625 (the bit-identical check)
```
`FUNSEARCH_API_KEY` must be in the environment. Never print it.

### 2. State (runs/ is gitignored: copy it from remote/pure)

```sh
git fetch origin remote/pure
git archive origin/remote/pure remote/pure/runs | tar -x --strip-components=2 -C .   # -> ./runs/...
ls runs/   # must include pure4.json, pure4.log, pure4-g1/ pure4-g2/ pure4-g3/ AND pure4-g2-b/ pure4-g3-oldbuild/
```
The abandoned `pure4-g2-b/` and `pure4-g3-oldbuild/` dirs must come along. `spent('pure4')` globs
`runs/pure4-g*/programs.jsonl`, so without them the budget under-counts by about $0.6. Do not
delete them.

P1 contents (write these after copying; the snapshot still has tune-3). g3 keeps its frozen
opponents from pure4.json; these files take effect at the g3 promotion check (send) and at g4
(fixed):
- `runs/pure_fixed.txt`:
  ```
  policies/tune-5.policy
  policies/v5d.policy
  policies/v4.policy
  policies/locker.policy
  policies/fs-2.policy
  ```
- `runs/pure_send.txt`: `policies/tune-5.policy`

### 3. Resume checks (before launching)

- `runs/pure4.json` must be `{"gen": 3, "members": ["policies/fs-p2.policy"], "fixed": [tune-3, v5d,
  v4, locker, fs-2], "target": 151}` (target may be higher if g3 already got a no-promotion extension).
  Do not edit it: "fixed"/"target" are frozen for g3.
- `N=$(wc -l < runs/pure4-g3/programs.jsonl)`
- `python3 -c "from funsearch.league import spent; print(round(spent('pure4'), 2))"` -> S
  must print 5.14 at the snapshot. Expected `left` = 18.10 - 5.14 = $12.96. N must be 49.

### 4. Launch g3 (to the end of generation 3)

```sh
setsid nohup python3 -m funsearch.league --name pure4 --budget 18.10 \
  --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt \
  --policy-prefix fs-p --line pure --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd \
  --workers 3 --eval-threads 2 --threads 5 --max-generations 3 --no-commit >> runs/pure.out 2>&1 &
```
(`--members fs-1` is ignored on resume; the state's members win.) These are the same 3x2 / 5
threads as `runs/pure_launch.sh`. Raise them only with the pure line's OK: they change nothing in
results, but keep them equal across the line's history for timing.

Proof that it resumed and did not restart:
- `runs/pure4.log` gets `pure4-g3: +102 programs (to 151), best policies/fs-p2.policy, league
  ['policies/tune-3.policy', ...], $12.96 left`. A `+150`/`+151` or a gen other than g3 means
  it restarted: STOP it at once.
- `runs/pure4-g3.log` has no new `seed score` line; the next program line is `[<N>] ...`.

### 5. At the g3 -> g4 boundary (the league exits after a promotion)

1. Promotion: `runs/pure4.log` shows `PROMOTED fs-p3.policy: ...` and `policies/fs-p3.policy`
   exists but is uncommitted. `runs/pure4.json` is now gen 4 with no fixed/target.
2. Check out funsearch/pure **2a874b7** exactly (coord/blocks merged: rebuild required) (the vetted g4 commit, also G4_REV in ec2/runner runner/lines/pure.sh; not the moving tip): COMBAT + TOP_TEAMS_RULES prompt (13facf9), tune5-campreset opponent files. `runs/` holds tracked files that you changed, so a plain
   checkout refuses. Keep your state and take the tip's launcher and opponent files:
   ```sh
   cp -a runs ~/runs-g3-backup
   git fetch origin funsearch/pure && git checkout -f -B funsearch/pure origin/funsearch/pure
   rm -rf runs && cp -a ~/runs-g3-backup runs
   git checkout funsearch/pure -- runs/pure_launch.sh runs/pure_fixed.txt runs/pure_send.txt
   cat runs/pure4.json   # must be gen 4, members [policies/fs-p3.policy], no fixed/target
   ```
   `policies/fs-p3.policy` is untracked and survives. Commit and push it to funsearch/pure, with
   the PROMOTED line in the message. Do not commit `runs/` state files from EC2 unless the pure
   line asks.
3. Rebuild only if `interp/` changed between 81ab84b and the tip.
4. Relaunch with `runs/pure_launch.sh` (no `--max-generations`, no `--no-commit`). It carries
   the same `--budget 18.10` (funsearch/pure c44a0a3). g4 then uses the new
   prompt and fixed = tune5-campreset (send check vs tune5-campreset and tune-5). Its first log line must read `pure4-g4: +150 programs (to 151), best
   policies/fs-p3.policy, league ['policies/tune5-campreset.policy', ...], $<about 11> left`.
5. Report the promotion (all PROMOTED rates, incl. cambc-exact vs tune-5) on PR #2.

If the spot instance is reclaimed mid-g3, redo steps 2-4 from the runner's own last `runs/`. Never
use the older remote/pure snapshot then. Validation games are cached in
`runs/validation_cache.jsonl`, so keep that file too.
