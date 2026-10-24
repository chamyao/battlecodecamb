#!/bin/sh
# STYLE line launcher: one resumable league per style island (state runs/style-<x>.json).
# usage: runs/style_launch.sh <a|b|c> <budget USD>
cd "$(dirname "$0")/.." || exit 1
case "$1" in
  a) dir=funsearch/styles/a_lockdown.txt; req=buy_altar_lock,place_altar_lock ;;
  b) dir=funsearch/styles/b_teamfight.txt; req=set_team_target,team_target ;;
  c) dir=funsearch/styles/c_monolith.txt; req=monolith_tiles,claim_count ;;
  *) echo "usage: $0 <a|b|c> <budget>"; exit 1 ;;
esac
PYTHONUNBUFFERED=1 exec python3 -m funsearch.league --name "style7-$1" --budget "$2" \
  --members policies/tune-5.policy --keep 0 --cambc-ref policies/tune-5.policy \
  --fixed policies/tune-1.policy,policies/v7zg-cast.policy,policies/v5d.policy,policies/locker.policy,policies/fs-2.policy \
  --regress 1.0 --z 2.83 --prefix "style-$1" --line "style-$1" \
  --session https://claude.ai/code/session_01T3FQRTdJunBXQYe7M4YBHh \
  --threads "${VAL_THREADS:-4}" \
  --fresh-seeds --directive "@$dir" --require "$req" --workers "${WORKERS:-2}" --eval-threads "${EVAL_THREADS:-2}"
