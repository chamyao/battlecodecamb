#!/bin/sh
# Resume the hybrid league after a container restart (no-op if it is running).
cd "$(dirname "$0")/.." || exit 1
pgrep -a -x python3 | grep -q "league --name hyb4" && { echo running; exit 0; }
[ -f "$HOME/.funsearch.env" ] && . "$HOME/.funsearch.env"
nohup setsid "$HOME/bc/notify_exit.sh" 1 hybrid hyb4-league runs/hyb4.log python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy \
  --fixed policies/locker.policy \
  --prefix fs-h --line hybrid --round 30 --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2 >> runs/hyb4.out 2>&1 < /dev/null &
echo resumed
