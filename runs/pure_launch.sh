#!/bin/sh
# PURE line launcher. pure3: fresh after interp/v0 f88ae73 (v7 added to the fixed opponents);
# pure-g1 ($0.16, old prices) and pure2-g1 ($0.096, no v7) were stopped. Resumable via runs/pure3.json + runs/pure3-g*/programs.jsonl
cd "$(dirname "$0")/.." || exit 1
exec python3 -m funsearch.league --name pure3 --budget 9.73 \
  --members policies/fs-1.policy --keep 0 \
  --fixed policies/v7.policy,policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy \
  --cambc-also policies/v7.policy \
  --policy-prefix fs-p --line pure \
  --session https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX
