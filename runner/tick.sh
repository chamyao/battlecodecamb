#!/bin/bash
# One supervisor tick: run every enabled line script, then push a heartbeat to ec2/status.
cd /root/bc || exit 1
. /root/bc/runner/runner/lib.sh
for f in /root/bc/runner/runner/lines/*.sh; do
  [ -e "$f" ] || continue
  LINE=$(basename "$f" .sh)
  ( . "$f" ) || log "line script exited $?"
done
LINE=runner
mkdir -p /root/bc/status
{
  echo "# EC2 runner status"
  echo
  echo "Updated $(date -u '+%Y-%m-%d %H:%M') UTC. Instance up since $(uptime -s) (UTC); load: $(cut -d' ' -f1-3 /proc/loadavg) on $(nproc) threads."
  echo "Disk: $(df -h / | awk 'NR==2{print $3" used of "$2}')."
  echo
  echo '## python3 processes'
  echo '```'
  pgrep -a -x python3 | cut -c1-300
  echo '```'
  echo '## tick.log (last 40 lines)'
  echo '```'
  tail -n 40 /root/bc/tick.log
  echo '```'
} > /root/bc/status/STATUS.md
push_state ec2/status . /root/bc/status
