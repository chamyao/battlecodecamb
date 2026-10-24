# ec2/runner: control branch for the EC2 FunSearch box

One long-lived c7a.4xlarge spot instance (persistent request, interruption = stop) runs the lines.
There is no SSH: the box is driven entirely from this branch.

- `runner/supervise.sh` runs as a systemd service. Every 5 minutes it pulls this branch and runs
  `runner/tick.sh`, so a pushed change here takes effect within ~5 minutes.
- `runner/tick.sh` runs each enabled `runner/lines/<line>.sh`. A line script must be idempotent:
  set up once, start each job only if it is not running and not done, and push state with
  `push_state` (from `runner/lib.sh`). Disable a line by renaming its script to `*.off`.
- Each line works in its own clone `/root/bc/<line>`. State goes to that line's `remote/<line>`
  branch, as on remote-server. A heartbeat goes to `ec2/status` (STATUS.md).
- Secrets: the instance role reads SSM SecureStrings `/funsearch/anthropic` and `/funsearch/github`
  into root-only files. They are never in user-data, logs or commits. Line scripts get
  FUNSEARCH_API_KEY from `/root/.funsearch.env`.
- Stopping a job gracefully is line-specific (STOP files; see each line's JOBS.md). Never use `pkill -f`.

Launch, stop and status: `scripts/ec2_runner.py` on branch infra/ec2-test.
