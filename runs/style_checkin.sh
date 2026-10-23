#!/bin/sh
# STYLE line check-in: restart any island league that died (container restart), commit+push progress.
cd "$(dirname "$0")/.." || exit 1
[ -x interp/build/interp_eval ] || { cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build interp/build -j4 --target interp_eval >/dev/null; }
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
for x in a b c; do
  b=$(grep "^$x " runs/style_budgets 2>/dev/null | cut -d' ' -f2)
  [ -n "$b" ] || continue
  if ! pgrep -f "funsearch.league --name style3-$x " >/dev/null; then
    ls runs/style3-$x-g*/STOP >/dev/null 2>&1 || { setsid nohup runs/style_launch.sh $x $b >> runs/style3-$x.out 2>&1 & echo "restarted style-$x"; }
  fi
  tail -n 3 runs/style3-$x.log 2>/dev/null
  for f in runs/style3-$x-g*.log; do [ -f "$f" ] && tail -n 1 "$f"; done
done
git add -f runs/style*.log runs/style*.json runs/style*-g*/programs.jsonl runs/style*-g*/proposals.jsonl runs/SPEND.md 2>/dev/null
git commit -qm "runs: style line progress

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01V26XD9N15L34L9j3pMnVNC" && git push -q origin funsearch/style
