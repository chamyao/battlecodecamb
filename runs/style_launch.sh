#!/bin/sh
# STYLE line launcher: one resumable league per style island (state runs/style8-<x>.json).
# usage: runs/style_launch.sh <a|b|c|h> <budget USD>
# a/b/c: style islands vs the bar tune5-campreset (also the cambc-ref). h: hunter island, seeded with
# opp-hunter2b and scored with a fight score (--fight-weight) against tune5-campreset, tune5-reset and tune-5.
cd "$(dirname "$0")/.." || exit 1
BAR=policies/tune5-campreset.policy
FIXED=policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2b.policy,policies/opp-hunter2a.policy,policies/v7zg-cast.policy,policies/fs-2.policy
case "$1" in
  a) dir=funsearch/styles/a_lockdown.txt; req=buy_altar_lock,place_altar_lock ;;
  b) dir=funsearch/styles/b_combat.txt; req=set_team_target,team_target ;;
  c) dir=funsearch/styles/c_monolith.txt; req=monolith_tiles,claim_count ;;
  h) dir=funsearch/styles/h_hunter.txt; req=set_team_target ;;
  *) echo "usage: $0 <a|b|c|h> <budget>"; exit 1 ;;
esac
if [ "$1" = h ]; then
  members=policies/opp-hunter2b.policy; best_w=0.5; extra="--fight-weight 0.5"
  FIXED=policies/tune-v18.policy,$BAR,policies/tune5-reset.policy,policies/tune-5.policy,policies/opp-hunter2a.policy
else
  members=$BAR; best_w=3.0; extra=""
fi
PYTHONUNBUFFERED=1 exec python3 -m funsearch.league --name "style8-$1" --budget "$2" \
  --members "$members" --keep 0 --best-weight "$best_w" --cambc-ref "$BAR" \
  --fixed "$FIXED" \
  --regress 1.0 --z 2.83 --prefix "style-$1" --line "style-$1" \
  --session https://claude.ai/code/session_01T3FQRTdJunBXQYe7M4YBHh \
  --threads "${VAL_THREADS:-4}" \
  --fresh-seeds --directive "@$dir" --require "$req" --workers "${WORKERS:-2}" --eval-threads "${EVAL_THREADS:-2}" $extra
