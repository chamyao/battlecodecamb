#!/bin/sh
# PURE line launcher. pure4: fresh on interp/v0 752a2ee (fog camps block pathing, recalibrated);
# v7-zerogem (ladder v8) replaces v7 as fixed opponent and send check. Earlier: pure-g1 $0.16,
# pure2-g1 $0.10, pure3-g1 $0.016 (all stopped on sim/opponent changes). Resumable via runs/pure4.json + runs/pure4-g*/
# Fixed opponents: runs/pure_fixed.txt, read at each new generation (frozen per generation in runs/pure4.json);
# send check (cambc-exact, informational): runs/pure_send.txt.
cd "$(dirname "$0")/.." || exit 1
exec python3 -m funsearch.league --name pure4 --budget 9.71 \
  --members policies/fs-1.policy --keep 0 \
  --fixed @runs/pure_fixed.txt \
  --cambc-also @runs/pure_send.txt \
  --policy-prefix fs-p --line pure \
  --session https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX
