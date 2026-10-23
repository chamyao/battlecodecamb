#!/bin/sh
# PURE line launcher (resumable: league state in runs/pure.json, programs in runs/pure-g*/programs.jsonl)
cd "$(dirname "$0")/.." || exit 1
exec python3 -m funsearch.league --name pure --budget 10 \
  --members policies/fs-1.policy --keep 0 \
  --fixed policies/v5d.policy,policies/v4.policy,policies/locker.policy,policies/fs-2.policy \
  --policy-prefix fs-p --line pure \
  --session https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX
