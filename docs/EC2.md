# Running the FunSearch league on EC2

Test of 2026-10-24 (`scripts/ec2_launch.py`). Nothing here contains a secret.

## What the AWS account allows today

The `fs` IAM user is in an AWS Organization whose SCPs and IAM policy allow, in practice:

- EC2 **only in us-east-2** (every other region gets an explicit SCP deny, including us-east-1).
- **No spot** (RunInstances with spot options is denied by an SCP).
- **AWS Free plan**: RunInstances refuses any type that is not free-tier eligible
  ("The specified instance type is not eligible for Free Tier"). Eligible types are all 2 vCPU
  (t3/t4g/t8i micro/small, c7i-flex.large, m7i-flex.large). **c7a.4xlarge cannot be launched**
  until the account is upgraded to a paid plan.
- No `s3:CreateBucket` or `s3:ListAllMyBuckets`, and no `ssm:GetParameter` (so the SSM public
  AMI parameter can't be read either; the script uses DescribeImages with Canonical's owner id).
- Allowed: DescribeImages/Instances/VPCs, RunInstances (on-demand, free-tier types),
  TerminateInstances, GetConsoleOutput, CreateSecurityGroup/KeyPair (unused).

The Claude cloud container cannot open outbound TCP 22, so SSH is not an option from here.

## Transport that works (no SSH, no S3, no token)

- Code: the repo is public, so user-data runs
  `curl https://codeload.github.com/chamyao/battlecodecamb/tar.gz/<sha>` for a pushed commit.
- Results: the instance writes `FSB|` lines to `/dev/ttyS0`; the launcher polls
  `ec2:GetConsoleOutput` (last 64 KB per call) and accumulates them. Console output lags by up to a
  minute or so.
- Safety: `InstanceInitiatedShutdownBehavior=terminate`, a `shutdown -h +N` dead-man switch at
  boot, and the launcher terminates in `finally` and waits for state `terminated`.

## Measured (c7i-flex.large, 2 vCPU, free tier, on-demand)

| | c7i-flex.large (EC2) | this container (4 vCPU) |
|---|---|---|
| apt + pip + build | 44 s | n/a |
| `pytest tests` | 2012 passed, 6 s | |
| sim 160 games, 2 threads | 26.5 s = **6.0 games/s** | 19.9 s = 8.0 games/s |
| sim 160 games, 4 threads | n/a | 10.1 s = **15.8 games/s** |
| `cambc_check(tune-2 vs tune-1)` | **0.575** (expected 0.575) | |
| funsearch mutate, 12 programs, w1×2 threads | cut off by the 45-min limit | 1915 s = 22.6 programs/h |

Simulator results are bit-identical between EC2 and the container (same win rate, gems and rounds),
so the box is a drop-in. FunSearch throughput scales with games/s (it is simulator bound), so the
container's 22.6 programs/h at 2 threads → ~45/h on all 4 cores; a 2-vCPU flex box is slower than
the container and is not worth using for the league.

c7a.4xlarge (16 physical cores, no SMT) is untested because of the free-plan block. A rough
estimate from the numbers above is ~4× this container (~60 games/s, ~150-180 programs/h with
`--workers 8 --eval-threads 2`). Measure it once the account allows it:
`python3 scripts/ec2_launch.py --job bench --rev <pushed sha>` (about 60-80 min, ~$1 on-demand).

## Recipe for the real league

1. Upgrade the AWS account to a paid plan (or use a different account). Optionally ask the org
   admin to allow spot in us-east-2 (c7a.4xlarge ≈ $0.22-0.26/h spot vs ~$0.82/h on-demand).
2. Push the commit to run, then `python3 scripts/ec2_launch.py --job <job> --rev <sha> --max-minutes N`.
   Add a `league` job to `JOBS` with the `python3 -m funsearch.league ...` command line.
3. Results: the console works for progress lines. For full run directories (`runs/<name>/`) you
   need a place to write. Either grant `s3:PutObject` on one fixed bucket and attach an instance
   role, or, without any AWS permission changes, push results to a branch with a fine-grained
   GitHub token scoped to this repo (contents: write), stored as below.
4. **API key for the Claude proposer, never in user-data** (user-data is readable by anyone with
   DescribeInstanceAttribute and is logged on the box): store it as an SSM Parameter Store
   `SecureString` (or a Secrets Manager secret), create an instance profile whose role may only
   `ssm:GetParameter` + `kms:Decrypt` on that one parameter, and have the job read it at runtime:
   `export ANTHROPIC_API_KEY=$(aws ssm get-parameter --name /funsearch/anthropic --with-decryption --query Parameter.Value --output text)`.
   This needs `iam:PassRole` plus the parameter permissions for whoever launches the box; the `fs`
   user has neither today.
5. The instance stays up only while the job runs, so no idle reclaim, but the launcher's poll loop
   does have to keep running somewhere. For long leagues, run the launcher detached (or rely on
   the dead-man switch and read the console later with `aws ec2 get-console-output`).
