#!/bin/sh
# PURE line check-in: resume the league if it died (container restart), then commit+push progress.
cd "$(dirname "$0")/.." || exit 1
if ! pgrep -f "^python3 -m funsearch.league --name pure4 " >/dev/null; then
  [ -x interp/build/interp_eval ] || { cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build interp/build -j4 --target interp_eval >/dev/null; }
  python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
  ls runs/pure4-g*/STOP >/dev/null 2>&1 || { setsid nohup runs/pure_launch.sh >> runs/pure.out 2>&1 & echo "restarted league"; }
fi
tail -5 runs/pure4.log
for f in runs/pure*-g*.log; do tail -1 "$f"; done
for f in runs/pure.log runs/pure.json runs/pure2.log runs/pure2.json runs/pure3.log runs/pure3.json runs/pure4.log runs/pure4.json runs/pure*-g*.log runs/pure*-g*/programs.jsonl runs/pure*-g*/proposals.jsonl runs/pure_checkin.sh runs/pure_launch.sh runs/pure_fixed.txt runs/pure_send.txt; do [ -f "$f" ] && git add -f "$f"; done
git commit -qm "runs: pure line progress

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX" && git push -q origin funsearch/pure
