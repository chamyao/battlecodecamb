#!/bin/sh
# Snapshot the STYLE island state (runs/ is gitignored) to branch funsearch/style-state and push it.
# Only complete JSON lines are copied, so a run writing at that moment is safe.
cd "$(dirname "$0")/.." || exit 1
W=$(mktemp -d)
git fetch -q origin funsearch/style-state 2>/dev/null
git worktree add -q --detach "$W" origin/funsearch/style-state 2>/dev/null || git worktree add -q --detach "$W" HEAD
for d in runs/style6-*-g*/; do
  mkdir -p "$W/$d"
  for f in programs.jsonl proposals.jsonl; do
    [ -f "$d$f" ] && python3 -c '
import sys, json
out = []
for line in open(sys.argv[1]):
    try:
        json.loads(line); out.append(line)
    except Exception:
        pass
open(sys.argv[2], "w").writelines(out)' "$d$f" "$W/$d$f"
  done
done
cp runs/style6-*.json runs/style6-?.log runs/style6-*-g*.log "$W/runs/" 2>/dev/null
# state only: never carry scripts or budgets, so overlaying runs/ from this branch cannot clobber code
cd "$W" && git rm -rq --cached --ignore-unmatch runs/style_launch.sh runs/style_checkin.sh runs/style_push_state.sh runs/style_budgets runs/style_next_boundary.md runs/SPEND.md runs/pure_launch.sh runs/pure_checkin.sh >/dev/null && rm -f runs/style_*.sh runs/style_budgets runs/style_next_boundary.md runs/SPEND.md runs/pure_*.sh && git add -f runs && git commit -qm "STYLE island state snapshot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01V26XD9N15L34L9j3pMnVNC" && { git push -q origin HEAD:funsearch/style-state 2>/dev/null || echo "state push failed (no push credentials?)"; }
cd - >/dev/null; git worktree remove --force "$W"
