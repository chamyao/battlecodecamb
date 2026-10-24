#!/bin/sh
# PURE line launcher. pure4: fresh on interp/v0 752a2ee (fog camps block pathing, recalibrated);
# v7-zerogem (ladder v8) replaces v7 as fixed opponent and send check. Earlier: pure-g1 $0.16,
# pure2-g1 $0.10, pure3-g1 $0.016 (all stopped on sim/opponent changes). Resumable via runs/pure4.json + runs/pure4-g*/
# Fixed opponents: runs/pure_fixed.txt, read at each new generation (frozen per generation in runs/pure4.json);
# send check (cambc-exact, informational): runs/pure_send.txt.
# Ran on remote-server (Cham's Ryzen box) 03:40-?; from 2026-10-24 ~06:30 on EC2 (c7a.4xlarge), resumed from the
# remote/pure 04:15 snapshot. g3 runs with --budget 8.09 (old $10 line cap: 9.71 minus ~$1.62 estimated
# lost remote-server spend). From g4 (this script) 18.10 = $20 line cap - 0.28 (pure/pure2/pure3) - 1.62 (lost est.).
# 3 workers x 2 eval threads, 5 validation threads.
cd "$(dirname "$0")/.." || exit 1
exec python3 -m funsearch.league --name pure4 --budget 18.10 \
  --members policies/fs-1.policy --keep 0 \
  --fixed @runs/pure_fixed.txt \
  --cambc-also @runs/pure_send.txt \
  --policy-prefix fs-p --line pure \
  --session https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd \
  --workers 3 --eval-threads 2 --threads 5
