#!/bin/bash
# One supervisor tick: run every enabled line script, then push a heartbeat to ec2/status.
cd /root/bc || exit 1
. /root/bc/runner/runner/lib.sh
LINE=runner
python3 -c "import pytest, anthropic" 2>/dev/null ||
  { pip3 install -q --break-system-packages --ignore-installed pytest anthropic > /root/bc/pip.log 2>&1 &&
    log "installed pytest + anthropic"; } || { log "pip install failed: $(tail -n 2 /root/bc/pip.log)"; exit 1; }
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
  echo
  echo "**FINAL (17:58 UTC 2026-10-24): all FunSearch work moved to the arena; nothing runs here.** All lines confirmed:"
  echo "hybrid remote/hybrid fb5107a (+c474b96) = arena run 10; style style/arena-overlay 391f2d4 = arena runs 5/6;"
  echo "pure remote/pure 331d404; tune finished earlier (remote/tune). Instance shutdown is the account owner's call."
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
