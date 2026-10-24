#!/bin/sh
# PURE line check-in: resume the league if it died (container restart), then commit+push progress.
cd "$(dirname "$0")/.." || exit 1
# The league runs on remote-server since 2026-10-24 03:40; never relaunch it here.
tail -5 runs/pure4.log
for f in runs/pure*-g*.log; do tail -1 "$f"; done
for f in runs/pure.log runs/pure.json runs/pure2.log runs/pure2.json runs/pure3.log runs/pure3.json runs/pure4.log runs/pure4.json runs/pure*-g*.log runs/pure*-g*/programs.jsonl runs/pure*-g*/proposals.jsonl runs/pure_checkin.sh runs/pure_launch.sh runs/pure_fixed.txt runs/pure_send.txt; do [ -f "$f" ] && git add -f "$f"; done
git commit -qm "runs: pure line progress

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019SuVFgxah8yS3STZJvAcWX" && git push -q origin funsearch/pure
