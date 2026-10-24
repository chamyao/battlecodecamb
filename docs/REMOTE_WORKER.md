# Remote compute: the arena

Simulator games, leagues and FunSearch runs on remote-server go through the **arena**, an HTTPS
service on that machine (Cham, Oct 24). It replaces the old `remote/<line>` -> `jobs/<line>`
draft-PR channel and `JOBS.md`: no Claude session sits on the server, and you call the API
directly. The old channel is retired for anything the arena covers.

    export ARENA_URL=https://138-201-121-171.sslip.io/arena
    export ARENA_CLIENT=<your line or role>        # e.g. hybrid, tune, coordinator
    curl -fsS $ARENA_URL/docs                     # full API reference: read it first
    curl -fsS $ARENA_URL/client.py -o arena.py     # stdlib-only CLI
    python3 arena.py match my.policy v22-tune-v20-L1c --engine <deploy/v0 sha> --wait 60

## What needs what

- **No token** for anything but admin routes (since Oct 24 ~17:45 UTC): matches, batches, leagues,
  policies, engines, reads, and FunSearch runs (start, stop, run files). Send `X-Arena-Client` (the
  client sends `$ARENA_CLIENT`) so your matches and runs are listed under your name and you can
  cancel or stop them. Anonymous callers share a queue cap of 20,000 games.
- **Run spend** is bounded by the arena's caps: $16 per run, $60 over all arena runs (`GET /runs` ->
  `budget`). Pass `--budget`. FunSearch runs moved off EC2 on Oct 24: resume a stopped run with
  `workdir: fresh`, `overlay` from its state branch and the same `--name`.

## Rules

- **Engine**: every policy and match is pinned to an engine (a built repo commit). The default is
  an old funsearch/runs commit without tonight's sensors and bot fixes. For anything compared with
  the live bot, use the current deploy/v0 engine: **2e1ff7edfe75d21b3eee24f60144e04bea8f7b8c**
  (Oct 24 ~17:35 UTC; the sim's fuel recalibrated to within ~0.2k of cambc). Pass it as `"engine"`.
  Don't compare results across engines: the earlier 545c7b1 under-charges fuel by 1-4k, so gated
  policies pass their gates more often there than on the ladder.
- **Names are immutable.** A changed policy gets a new name. Live lineage is registered as
  `v18-tune-r-all-v2`, `v19-rall2-ca4-lean-g`, `v20-tune-fight-2s`, `v22-tune-v20-L1c` (live;
  versions 21, 22 and 24 run this policy) and `v23-style-gconv1`; older pool policies under their
  file names.
- **Simulator results only.** Ladder uploads and real-cambc checks stay with the coordinator and
  the bot session; uploads still need Cham's go-ahead.
- **Shared cores** (16 total: 6 match threads, 8 for arena runs, the rest for the line clones'
  own jobs). Don't flood the queue with low-value matches. League matches default to priority -1,
  so ad-hoc checks overtake them.
- **The `main2` league** (coordinator, engine 2e1ff7e; `main` is the older 545c7b1 run) holds the live lineage and baselines. A
  candidate joins with `python3 arena.py league add main2 <name>`, which plays a gauntlet against
  every member; post the standings with your candidate on PR #5.
- Budgets and promotion rules are the lines' own (docs/STRATEGY.md and the line handoffs).
