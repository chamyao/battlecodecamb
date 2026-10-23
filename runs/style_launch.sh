#!/bin/sh
# STYLE line launcher: one resumable league per style island (state runs/style-<x>.json).
# usage: runs/style_launch.sh <a|b|c> <budget USD>
cd "$(dirname "$0")/.." || exit 1
case "$1" in
  a) dir=funsearch/styles/a_lockdown.txt; req=buy_altar_lock,place_altar_lock ;;
  b) dir=funsearch/styles/b_teamfight.txt; req=set_team_target,team_target,claim_count ;;
  c) dir=funsearch/styles/c_monolith.txt; req=monolith_tiles,claim_count ;;
  *) echo "usage: $0 <a|b|c> <budget>"; exit 1 ;;
esac
exec python3 -m funsearch.league --name "style-$1" --budget "$2" \
  --members policies/v5d.policy --keep 0 \
  --fixed policies/v4.policy,policies/locker.policy,policies/fs-2.policy \
  --regress 1.0 --prefix "style-$1" --line "style-$1" \
  --session https://claude.ai/code/session_01V26XD9N15L34L9j3pMnVNC \
  --fresh-seeds --directive "@$dir" --require "$req" --workers 2 --eval-threads 2
