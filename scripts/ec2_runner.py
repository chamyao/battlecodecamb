"""Long-lived EC2 box for the FunSearch lines, driven from branch ec2/runner (no SSH).

    python3 scripts/ec2_runner.py launch      # persistent spot c7a.4xlarge with role funsearch-ec2
    python3 scripts/ec2_runner.py status      # instance state + recent FSB| console lines
    python3 scripts/ec2_runner.py stop        # cancel the spot request, terminate, wait

Secrets never pass through here: the instance role reads the SSM SecureStrings /funsearch/anthropic
and /funsearch/github at boot into root-only files. The spot request is persistent with interruption
behaviour "stop": AWS stops the box (EBS and local runs/ survive) and starts it again when capacity
returns; the systemd supervisor resumes the lines. See README.md on branch ec2/runner.
"""
import argparse
import sys
import time

import boto3

UBUNTU = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
CANONICAL = "099720109477"
NAME = "funsearch-runner"

USER_DATA = r"""#!/bin/bash
exec > /var/log/runner-boot.log 2>&1
say() { echo "FSB|boot: $*" > /dev/ttyS0; }
say "start $(date -u +%FT%TZ)"
export DEBIAN_FRONTEND=noninteractive HOME=/root
for i in 1 2 3 4 5; do apt-get -o DPkg::Lock::Timeout=600 update -q &&
  apt-get -o DPkg::Lock::Timeout=600 install -y -q build-essential cmake python3-pip rsync git && break; sleep 15; done
pip3 install -q --break-system-packages boto3 anthropic pytest
umask 077
python3 - <<'EOF'
import json, urllib.request, boto3
tok = urllib.request.urlopen(urllib.request.Request("http://169.254.169.254/latest/api/token", method="PUT",
      headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})).read().decode()
region = json.loads(urllib.request.urlopen(urllib.request.Request(
      "http://169.254.169.254/latest/dynamic/instance-identity/document",
      headers={"X-aws-ec2-metadata-token": tok})).read())["region"]
ssm = boto3.client("ssm", region_name=region)
get = lambda n: ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"].strip()
open("/root/.funsearch.env", "w").write("FUNSEARCH_API_KEY=%s\n" % get("/funsearch/anthropic"))
open("/root/.git-credentials", "w").write("https://x-access-token:%s@github.com\n" % get("/funsearch/github"))
EOF
umask 022
[ -s /root/.funsearch.env ] && [ -s /root/.git-credentials ] && say "secrets ok" || say "SECRETS MISSING"
git config --global credential.helper store
git config --global user.name ec2-runner
git config --global user.email ec2-runner@users.noreply.github.com
mkdir -p /root/bc && git clone -q --branch ec2/runner https://github.com/chamyao/battlecodecamb /root/bc/runner
cat > /etc/systemd/system/funsearch-runner.service <<'EOF'
[Unit]
Description=FunSearch EC2 runner supervisor
After=network-online.target
Wants=network-online.target
[Service]
ExecStart=/bin/bash /root/bc/runner/runner/supervise.sh
Restart=always
RestartSec=30
KillMode=process
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable --now funsearch-runner.service
say "supervisor started $(date -u +%FT%TZ)"
"""


def ec2(region):
    return boto3.client("ec2", region_name=region)


def find(e):
    r = e.describe_instances(Filters=[{"Name": "tag:Name", "Values": [NAME]},
                                      {"Name": "instance-state-name",
                                       "Values": ["pending", "running", "stopping", "stopped"]}])
    return [i for res in r["Reservations"] for i in res["Instances"]]


def launch(a):
    e = ec2(a.region)
    if find(e):
        sys.exit("a runner instance already exists; use status/stop")
    imgs = e.describe_images(Owners=[CANONICAL], Filters=[{"Name": "name", "Values": [UBUNTU]},
                                                          {"Name": "architecture", "Values": ["x86_64"]}])
    ami = max(imgs["Images"], key=lambda i: i["CreationDate"])["ImageId"]
    r = e.run_instances(
        ImageId=ami, InstanceType=a.type, MinCount=1, MaxCount=1, UserData=USER_DATA,
        IamInstanceProfile={"Name": "funsearch-ec2"},
        MetadataOptions={"HttpTokens": "required"},
        InstanceMarketOptions={"MarketType": "spot", "SpotOptions": {
            "SpotInstanceType": "persistent", "InstanceInterruptionBehavior": "stop"}},
        BlockDeviceMappings=[{"DeviceName": "/dev/sda1",
                              "Ebs": {"VolumeSize": a.disk, "VolumeType": "gp3", "DeleteOnTermination": True}}],
        TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Name", "Value": NAME}]},
                           {"ResourceType": "spot-instances-request", "Tags": [{"Key": "Name", "Value": NAME}]}])
    print("launched", r["Instances"][0]["InstanceId"], a.type, ami)


def status(a):
    e = ec2(a.region)
    for i in find(e):
        print(i["InstanceId"], i["State"]["Name"], i.get("InstanceLifecycle", "on-demand"), i["LaunchTime"])
        out = e.get_console_output(InstanceId=i["InstanceId"], Latest=True).get("Output", "")
        lines = [l.split("FSB|", 1)[1] for l in out.splitlines() if "FSB|" in l]
        print("\n".join(lines[-a.lines:]))


def stop(a):
    e = ec2(a.region)
    insts = find(e)
    reqs = [i["SpotInstanceRequestId"] for i in insts if i.get("SpotInstanceRequestId")]
    reqs += [q["SpotInstanceRequestId"] for q in e.describe_spot_instance_requests(Filters=[
        {"Name": "tag:Name", "Values": [NAME]}, {"Name": "state", "Values": ["open", "active", "disabled"]}])[
        "SpotInstanceRequests"]]
    if reqs:
        e.cancel_spot_instance_requests(SpotInstanceRequestIds=sorted(set(reqs)))
        print("cancelled", sorted(set(reqs)))
    ids = [i["InstanceId"] for i in insts]
    if ids:
        e.terminate_instances(InstanceIds=ids)
        e.get_waiter("instance_terminated").wait(InstanceIds=ids)
    for i in ids:
        s = e.describe_instances(InstanceIds=[i])["Reservations"][0]["Instances"][0]["State"]["Name"]
        print(i, s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["launch", "status", "stop"])
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--type", default="c7a.4xlarge")
    ap.add_argument("--disk", type=int, default=40)
    ap.add_argument("--lines", type=int, default=40)
    a = ap.parse_args()
    {"launch": launch, "status": status, "stop": stop}[a.cmd](a)


if __name__ == "__main__":
    main()
