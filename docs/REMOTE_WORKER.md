# Remote worker: talking through GitHub

The training jobs (hybrid, pure and style FunSearch lines, tune-line screens) run on Cham's own
machine ("remote-server"). It exchanges work with the cloud sessions only through this repository,
never by session messages.

## Branches

- `remote/<line>` (`remote/hybrid`, `remote/pure`, `remote/style`, `remote/tune`): written only by
  remote-server; read by everyone. Each line's run state, logs and promoted policies.
- `jobs/<line>`: written by the line's cloud session; read by remote-server. The work it should
  run next (`jobs/<line>/JOBS.md` plus any files the job needs).

## Each check-in (about every 45 minutes) remote-server

1. `git fetch`, read `jobs/<line>/JOBS.md` for each line it runs, and start, stop or restart jobs
   as written there.
2. Commit to `remote/<line>`:
   - `STATUS.md`: what is running (process, commit, config), the latest log lines, spend so far.
   - `runs/<run>.log` tails, and the database/state files needed to resume elsewhere.
   - Any promoted policy as `policies/<name>.policy`, with its scores in the commit message.
3. Push.

## Rules

- Push access is a fine-grained GitHub token or deploy key limited to `chamyao/battlecodecamb`
  (Contents: read and write), set up by Cham on that machine. It never goes in the repo, a commit,
  a log or a message.
- remote-server never pushes to `main`, `interp/v0`, `deploy/v0` or any line's own branch; only to
  `remote/*`.
- Ladder submissions stay with the coordinator; remote-server never runs `cambc submit`.
- Budgets and promotion rules are the lines' own (docs/STRATEGY.md); JOBS.md can only narrow them.
