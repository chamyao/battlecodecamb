#!/bin/sh
# STYLE line gap search (resumable): improve ONE measurable gap of our bot (a funsearch/fights.py stat vs the
# reference, e.g. out_death_share:min:0.1) while staying >= the win floor vs the reference (default v21, 50%).
# The budget is a total: spend already in the run's programs.jsonl is subtracted on every (re)start.
# usage: runs/style_gap_launch.sh <run> <total budget USD> <metric:min|max:scale> [seed policy] [directive file]
# Final check of a candidate (exact floor, large sample):
#   python3 runs/hunter/fights.py <candidate.policy> policies/tune-v21.policy 800 <fresh seed>
cd "$(dirname "$0")/.." || exit 1
run=$1; total=$2; metric=$3; seed=${4:-policies/tune-v21.policy}; directive=${5:-funsearch/styles/b_combat.txt}
ref=${GAP_REF:-policies/tune-v21.policy}
left=$(python3 -c "
import json, pathlib
p = pathlib.Path('runs/$run/programs.jsonl')
spent = sum(json.loads(l)['metrics'].get('cost', 0.0) for l in open(p)) if p.exists() else 0.0
print(f'{max(0.0, $total - spent):.2f}')")
echo "gap run $run ($metric vs $ref): \$$left left of \$$total"
[ "$left" = "0.00" ] && exit 0
PYTHONUNBUFFERED=1 exec python3 -m funsearch.run --run "$run" --budget "$left" --max-programs "${MAX_PROGRAMS:-400}" \
  --seed-policy "$seed" \
  --opponents "${GAP_OPPONENTS:-builtin:starter@0.25,$ref@3,policies/tune-v20.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/tune5-campreset.policy}" \
  --gap-metric "$metric" --gap-ref "$ref" --gap-weight "${GAP_WEIGHT:-0.5}" --gap-games "${GAP_GAMES:-40}" \
  --win-floor "${WIN_FLOOR:-0.5}" --fresh-seeds --workers "${WORKERS:-2}" --eval-threads "${EVAL_THREADS:-2}" \
  --directive "@$directive" --helpers "${HELPERS:-funsearch/helpers.json}" \
  --tune-steps 4 --tune-games 8 --tune-rejects 2 \
  --tune-opponents "${TUNE_OPPONENTS:-$(echo "${GAP_OPPONENTS:-$ref,policies/tune-v20.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/tune5-campreset.policy}" | tr ',' '\n' | grep -v '^builtin:' | sed 's/@[0-9.]*$//' | head -5 | paste -sd,)}"
