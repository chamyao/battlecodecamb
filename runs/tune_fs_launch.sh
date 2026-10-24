#!/bin/sh
# TUNE line fight-block FunSearch (FunSearch lead, 08:09 UTC): seeded from tune-v18g (live v18 + retreat-dash fuel gate), edits restricted to
# the fight block by the directive, scored with --fight-weight 0.3 vs hunter2b and v18; $5 budget.
# usage: runs/tune_fs_launch.sh <budget USD> [league name]
# 10:20 UTC: restarted as tune-fight2, seeded from tune-v19 (live v19), fixed hunter3/hunter2b/campreset, wards forbidden.
cd "$(dirname "$0")/.." || exit 1
BAR=policies/tune-v19.policy
FIXED=policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/tune5-campreset.policy
PYTHONUNBUFFERED=1 exec python3 -m funsearch.league --name "${2:-tune-fight}" --budget "$1" \
  --members "$BAR" --keep 0 --best-weight 3.0 --cambc-ref "$BAR" \
  --fixed "$FIXED" \
  --regress 1.0 --z 2.83 --prefix tune-fight- --line tune --no-commit \
  --session https://claude.ai/code/session_01Ja9BznSBEpiUKCjkDru5e5 \
  --threads "${VAL_THREADS:-3}" --round 60 \
  --fresh-seeds --directive "@funsearch/styles/t_fight.txt" --workers "${WORKERS:-2}" --eval-threads "${EVAL_THREADS:-2}" \
  --fight-weight 0.3 --explore
