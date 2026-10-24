#!/bin/bash
# systemd entry point: pull the control branch, run one tick, repeat. Survives reboots and spot stop/start.
cd /root/bc/runner || exit 1
while true; do
  git fetch -q origin ec2/runner && git reset -q --hard origin/ec2/runner
  timeout 1200 bash runner/tick.sh >> /root/bc/tick.log 2>&1
  sleep 300
done
