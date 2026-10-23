#!/bin/sh
# PURE line launcher (pure2: fresh after the 9a0ac5b re-profile; pure-g1 spent $0.16 on old prices). Resumable via runs/pure2.json + runs/pure2-g*/programs.jsonl
cd "$(dirname "$0")/.." || exit 1
exec python3 -m funsearch.league --name pure2 --budget 9.84 \
  --members policies/fs-1.policy --keep 0 \
  --fixed policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy \
  --policy-prefix fs-p --line pure \
  --session https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX
