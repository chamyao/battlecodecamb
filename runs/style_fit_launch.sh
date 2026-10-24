#!/bin/sh
# STYLE line fitting run (resumable): evolve an opponent whose sim stats vs our versions match the real top-team
# stats in a target file (funsearch/fit.py). The budget is a total: spend already in the run's programs.jsonl is
# subtracted on every (re)start, so restarts never double-spend.
# usage: runs/style_fit_launch.sh <run name> <total budget USD> <target.json> [seed policy] [inject policies,...]
cd "$(dirname "$0")/.." || exit 1
run=$1; total=$2; target=$3; seed=${4:-policies/opp-hunter3.policy}; inject=${5:-}
left=$(python3 -c "
import json, sys, pathlib
p = pathlib.Path('runs/$run/programs.jsonl')
spent = sum(json.loads(l)['metrics'].get('cost', 0.0) for l in open(p)) if p.exists() else 0.0
print(f'{max(0.0, $total - spent):.2f}')")
echo "fit run $run: \$$left left of \$$total"
[ "$left" = "0.00" ] && exit 0
PYTHONUNBUFFERED=1 exec python3 -m funsearch.run --run "$run" --budget "$left" --max-programs "${MAX_PROGRAMS:-400}" \
  --seed-policy "$seed" --opponents builtin:starter --fit-target "$target" --games "${FIT_GAMES:-24}" \
  --fresh-seeds --workers "${WORKERS:-2}" --eval-threads "${EVAL_THREADS:-5}" \
  --directive @funsearch/styles/fit_hunter.txt ${inject:+--inject $inject}
