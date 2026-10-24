"""Run a benchmark/league job on one EC2 instance with no SSH, no S3 and no secrets on the box.

Written for an IAM user with EC2 rights but no S3 bucket creation or SSM parameter reads, driven
from a cloud container that cannot open outbound SSH. So:
  code in:     the repo is public; user-data downloads the exact commit from codeload.github.com
               (no token anywhere).
  results out: the instance prints `FSB|`-prefixed lines to the serial console and we poll
               ec2:GetConsoleOutput (last 64 KB; we accumulate across polls).
  safety:      InstanceInitiatedShutdownBehavior=terminate, `shutdown -h +N` dead-man switch, and
               this script terminates the instance in a `finally` and waits for 'terminated'.
AWS credentials come from the environment (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY).

    python3 scripts/ec2_launch.py --job bench --rev <pushed commit sha>
"""
import argparse
import subprocess
import time

import boto3
from botocore.exceptions import ClientError

UBUNTU = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
CANONICAL = "099720109477"
REPO = "chamyao/battlecodecamb"
OPPS = ("builtin:starter@0.25,policies/tune-3.policy@3,policies/v7-zerogem.policy,policies/v7.policy,"
        "policies/locker.policy,policies/v7zg-cast.policy,policies/v7zg-monozone.policy")

SETUP = r"""
step apt bash -c 'apt-get update -q && DEBIAN_FRONTEND=noninteractive apt-get install -y -q build-essential cmake python3-pip'
step pip pip3 install -q --break-system-packages pytest
step build bash -c 'cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release && cmake --build interp/build -j --target interp_eval'
step compile bash -c 'for p in tune-2 tune-3; do python3 -c "from policygen.compile import to_prefix; from policygen.text import parse; import sys; print(to_prefix(parse(open(sys.argv[1]).read())))" policies/$p.policy > /root/$p.pol; done'
"""
SIM = "interp/build/interp_eval --a /root/tune-3.pol --b /root/tune-2.pol --games 160 --threads {} maps/*.map26a"
CAMBC = ("python3 -c \"from funsearch.league import cambc_check; "
         "print(cambc_check(open('policies/tune-2.policy').read(), 'policies/tune-1.policy', {}))\"")
FS = ("python3 -m funsearch.run --run ec2test-w{w} --proposer mutate --max-programs {n} --workers {w} "
      "--eval-threads 2 --seed-policy policies/tune-3.policy --opponents " + OPPS)

JOBS = {
    "bench": SETUP + rf"""
step pytest python3 -m pytest -q tests
step sim16 bash -c '{SIM.format(16)}'
step sim4 bash -c '{SIM.format(4)}'
step cambc {CAMBC.format(16)}
step fs_w8 {FS.format(w=8, n=60)}
step fs_w16 {FS.format(w=16, n=60)}
""",
    # 2-vCPU free-tier box: checks the pipeline end to end and measures per-core speed
    "smoke": SETUP + rf"""
step pytest python3 -m pytest -q tests
step sim2 bash -c '{SIM.format(2)}'
step cambc {CAMBC.format(2)}
step fs_w1 {FS.format(w=1, n=12)}
""",
}

USER_DATA = r"""#!/bin/bash
shutdown -h +{max_minutes}
exec > /var/log/job.log 2>&1
say() {{ echo "$*" | sed 's/^/FSB|/' > /dev/ttyS0; }}
step() {{ local n=$1; shift; say "=== $n start $(date +%s)"
  # stream funsearch progress lines live so a run cut short still reports its throughput
  ( "$@" ) 2>&1 | tee /root/out/$n.txt | grep --line-buffered -E '^\[|^seed|^done' | sed -u 's/^/FSB|/' > /dev/ttyS0
  local rc=${{PIPESTATUS[0]}}
  say "=== $n rc=$rc end $(date +%s)"; say "$(tail -c 1500 /root/out/$n.txt)"; }}
mkdir -p /root/out /root/work && cd /root/work
export HOME=/root
say "boot $(date +%s) nproc=$(nproc) $(lscpu | grep 'Model name')"
curl -sSL https://codeload.github.com/{repo}/tar.gz/{rev} | tar xz --strip-components=1
{job}
say "DONE $(date +%s)"
sleep 20
shutdown -h now
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="bench", choices=sorted(JOBS))
    ap.add_argument("--type", default="c7a.4xlarge")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--wait-verification", type=int, default=0,
                    help="minutes to keep retrying while a new account is PendingVerification")
    ap.add_argument("--rev", default="HEAD", help="must be pushed to GitHub")
    ap.add_argument("--max-minutes", type=int, default=85, help="instance self-terminates after this")
    ap.add_argument("--out", default="ec2_out.txt")
    args = ap.parse_args()
    rev = subprocess.run(["git", "rev-parse", args.rev], check=True, capture_output=True, text=True).stdout.strip()

    ec2 = boto3.client("ec2", region_name=args.region)
    imgs = ec2.describe_images(Owners=[CANONICAL], Filters=[{"Name": "name", "Values": [UBUNTU]},
                                                            {"Name": "architecture", "Values": ["x86_64"]}])
    ami = max(imgs["Images"], key=lambda i: i["CreationDate"])["ImageId"]
    ud = USER_DATA.format(max_minutes=args.max_minutes, repo=REPO, rev=rev, job=JOBS[args.job])
    spec = dict(ImageId=ami, InstanceType=args.type, MinCount=1, MaxCount=1, UserData=ud,
                InstanceInitiatedShutdownBehavior="terminate",
                BlockDeviceMappings=[{"DeviceName": "/dev/sda1",
                                      "Ebs": {"VolumeSize": 30, "VolumeType": "gp3", "DeleteOnTermination": True}}],
                TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": "funsearch-test"}]}])
    deadline = time.time() + args.wait_verification * 60
    while True:
        market = "spot"
        try:
            try:
                r = ec2.run_instances(**spec, InstanceMarketOptions={"MarketType": "spot", "SpotOptions": {
                    "SpotInstanceType": "one-time", "InstanceInterruptionBehavior": "terminate"}})
            except ClientError as e:
                if e.response["Error"]["Code"] == "PendingVerification":
                    raise
                print("spot failed, falling back to on-demand:", e.response["Error"]["Code"], flush=True)
                market = "on-demand"
                r = ec2.run_instances(**spec)
            break
        except ClientError as e:
            if e.response["Error"]["Code"] != "PendingVerification" or time.time() > deadline:
                raise
            print(time.strftime("%H:%M:%S"), "account still PendingVerification; retrying in 2 min", flush=True)
            time.sleep(120)
    iid = r["Instances"][0]["InstanceId"]
    t0 = time.time()
    lines = []
    try:
        print(f"launched {iid} ({market}, {args.type}, {ami}, rev {rev[:10]})", flush=True)
        while time.time() - t0 < (args.max_minutes + 5) * 60:
            time.sleep(30)
            out = ec2.get_console_output(InstanceId=iid, Latest=True).get("Output", "")
            new = [l.split("FSB|", 1)[1] for l in out.splitlines() if "FSB|" in l]
            # the console window slides; append only the part after the longest overlap with what we have
            k = next((k for k in range(min(len(new), len(lines)), 0, -1) if lines[-k:] == new[:k]), 0)
            for l in new[k:]:
                print(l, flush=True)
            lines += new[k:]
            state = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]["State"]["Name"]
            if any(l.startswith("DONE ") for l in lines) or state in ("shutting-down", "terminated"):
                break
    finally:
        with open(args.out, "w") as f:
            f.write("\n".join(lines) + "\n")
        ec2.terminate_instances(InstanceIds=[iid])
        ec2.get_waiter("instance_terminated").wait(InstanceIds=[iid])
        state = ec2.describe_instances(InstanceIds=[iid])["Reservations"][0]["Instances"][0]["State"]["Name"]
        print(f"{iid} {state}; instance time {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
