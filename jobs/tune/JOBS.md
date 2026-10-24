# Jobs for remote-server: tune line

Written by the FunSearch lead session (the tune line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/tune`, branch `tune/runs`. CPU only, no API key.
Run every job at `nice -n 15` so the FunSearch lines get the CPU first.

## Job A: done (combo_confirm tune-5 re-confirm: h2h 0.531, cambc 0.5875).

## Job B: `funsearch/altar_bag.py` (on tune-3). Let it finish; comment its log when it exits.

## Job C (2026-10-24 04:50 UTC): map fixes rebased on tune-5 (live ladder v16). Start after job B exits.

1. `git pull origin tune/runs` (to 9a934e0 or later): adds `funsearch/t5_mapfix.py`. Same simulator
   build (c92239d), no rebuild.
2. `nice -n 15 python3 funsearch/t5_mapfix.py > runs/tune/t5mapfix.out 2>&1`
   Candidates on tune-5: t5-starv (round > 800 monolith fallback + T240 threat banking = tune-6's
   edits), t5-alt1 / t5-alt2 (altar-count bag, k = 2 / 3), t5-starv+alt1, t5-starv+alt2; plus tune-5
   itself per map as the baseline. Each: 2 x 400 fresh (seeds 9027/9028), gauntlet, cambc80, maps
   lost on both sides, per-map vs opp-icecream / v7zg-cast / opp-metab. Roughly 2-3 h.
   Results go to `runs/tune/t5mapfix.log`, one JSON line per candidate, and `runs/tune/cand-t5-*.policy`.
3. When it exits, push state to `remote/tune` (the log and the cand-t5-*.policy files) and comment
   on PR #4 with the full log.

## EC2 resume (2026-10-24 06:05 UTC, tune-line session session_01Ja9BznSBEpiUKCjkDru5e5)

Setup: clone branch `tune/runs` at **e0b932e or later** into `~/bc/tune`, build the simulator
(`cd interp/build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j4 interp_eval fuel_turns`; it must be
interp/v0 c92239d, the build every tune number so far used; `tune/runs` carries it), and `mkdir -p runs/tune`.
Run every job at `nice -n 15` with the scripts' default 4 threads. Base for everything: `policies/tune-5.policy` (live v16).

- **Job B (altar_bag on tune-3): do not re-run.** It's obsolete: tune-3 is no longer the base, its visible result
  (starv+alt2: 45.75% all-map, 37/80, six maps lost on both sides) fails, and job C re-tests the altar bag on tune-5.
- **Job C: run it** (nothing from it exists yet):
  `nice -n 15 python3 funsearch/t5_mapfix.py > runs/tune/t5mapfix.out 2>&1`
  Candidates t5-starv, t5-alt1, t5-alt2, t5-starv+alt1, t5-starv+alt2 (+ tune-5 per map). Output:
  `runs/tune/t5mapfix.log` (one JSON line each) and `runs/tune/cand-t5-*.policy`.
- **Job D (new): draft screen vs the ladder meta composition**, after C or alongside it if threads allow:
  `nice -n 15 python3 funsearch/draft_meta.py m1 9411 > runs/tune/draftmeta.out 2>&1`
  122 orders x (200 vs opp-metadraft + 200 vs tune-5). Output: `runs/tune/draftmeta-m1.log`, ranked
  `runs/tune/draftmeta-m1.json`.
- Not needed on EC2: the bank-rule screen (done in the tune session: no variant helps) and the 00lost-world
  monolith-group confirm (`funsearch/mgroup_confirm.py`, running in the tune session).

When each job exits: push the logs (and cand-*.policy files) to `remote/tune` and comment on PR #4 with the full log.
The tune session is subscribed to #4.
