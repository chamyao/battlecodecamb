# jobs/genome: EC2 job queue for the genome team

The EC2 box (c7a.4xlarge, 16 threads; runner/lines/genome.sh on branch ec2/runner) runs every
`<name>.sh` in this branch once. Results go to branch `remote/genome` under `<name>/`
(log.txt, rc, plus whatever the job writes to $OUT), pushed every ~5 minutes and when it exits.

- First line: `# rev: <commit sha>` (a pushed commit; it must contain genome/). The job runs in a
  fresh checkout of it, with genome/build/genome_eval already built.
- Environment: $OUT (write results here), $THREADS (5; at most 3 jobs run at once),
  FUNSEARCH_API_KEY (never print it).
- Names are unique: never edit a job that has started; add a new one. Pick up to ~5 min of latency.
- Log Claude API spend in genome/SPEND.md on your own branch, as usual.

Stopping a job: push an empty file `<name>.stop`. On the next tick (<= 5 min) the runner stops it (SIGTERM,
then SIGKILL after 10 s) and writes rc=stopped; out/<name>/ is kept, so a new job can resume from it.
