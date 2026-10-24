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
cp runs/style6-*.json runs/style6-?.log runs/style6-*-g*.log runs/SPEND.md "$W/runs/" 2>/dev/null
cd "$W" && git add -f runs && git commit -qm "STYLE island state snapshot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01V26XD9N15L34L9j3pMnVNC" && git push -q origin HEAD:funsearch/style-state
cd - >/dev/null; git worktree remove --force "$W"
