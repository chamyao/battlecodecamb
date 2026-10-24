#!/bin/sh
# STYLE line check-in: restart any island league that died (container restart), commit+push progress.
cd "$(dirname "$0")/.." || exit 1
[ -x interp/build/interp_eval ] || { cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build interp/build -j4 --target interp_eval >/dev/null; }
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
for x in a b c; do
  b=$(grep "^$x " runs/style_budgets 2>/dev/null | cut -d' ' -f2)
  [ -n "$b" ] || continue
  if ! pgrep -f "funsearch.league --name style6-$x " >/dev/null; then
    ls runs/style6-$x-g*/STOP >/dev/null 2>&1 || { setsid nohup runs/style_launch.sh $x $b >> runs/style6-$x.out 2>&1 & echo "restarted style-$x"; }
  fi
  tail -n 3 runs/style6-$x.log 2>/dev/null
  for f in runs/style6-$x-g*.log; do [ -f "$f" ] && tail -n 1 "$f"; done
done
runs/style_push_state.sh
