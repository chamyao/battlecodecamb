#!/bin/sh
# PURE line check-in: resume the league if it died (container restart), then commit+push progress.
cd "$(dirname "$0")/.." || exit 1
if ! pgrep -f "funsearch.league --name pure" >/dev/null; then
  [ -x interp/build/interp_eval ] || { cmake -S interp -B interp/build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build interp/build -j4 --target interp_eval >/dev/null; }
  python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
  ls runs/pure-g*/STOP >/dev/null 2>&1 || { nohup runs/pure_launch.sh >> runs/pure.out 2>&1 & echo "restarted league"; }
fi
tail -5 runs/pure.log
for f in runs/pure-g*.log; do tail -1 "$f"; done
git add -f runs/pure.log runs/pure.json runs/pure-g*/programs.jsonl runs/pure-g*/proposals.jsonl 2>/dev/null
git commit -qm "runs: pure line progress

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX" && git push -q origin funsearch/pure
