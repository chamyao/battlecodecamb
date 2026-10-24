# style line (jobs/style/JOBS.md "EC2 resume", 5e4b4b2 + 7dbe1eb). Gate 0 failed (Cham: no newer runs/ than
# remote/style ab19ed2), so per JOBS.md style6-a/c are not resumed (spend sunk; never relaunch style6-c) and
# S2 (style7 a/b/c) starts directly on funsearch/style (24a4393 or later). The box is shared, so the reduced
# per-island threads from JOBS.md: WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3.
# State out: runs/style7-* -> funsearch/style-state (as runs/style_push_state.sh does) and remote/style.
D=/root/bc/style
export WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3
if [ ! -f "$D/.setup-done" ]; then
  clone_nopush funsearch/style "$D" || { log "clone failed"; return 1; }
  cd "$D" && build "$D" || { log "build failed: $(tail -n 3 interp/build/build.log)"; return 1; }
  python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1 || { log "pytest failed: $(tail -n 2 /root/bc/style-pytest.txt)"; return 1; }
  # resume any style7 state already pushed (none expected on first start)
  git fetch -q origin funsearch/style-state 2>/dev/null &&
    git archive origin/funsearch/style-state runs 2>/dev/null | tar -x --wildcards 'runs/style7-*' 2>/dev/null
  touch "$D/.setup-done"
  log "setup ok at funsearch/style $(git rev-parse --short HEAD): $(tail -n 1 /root/bc/style-pytest.txt); budgets: $(tr '\n' ' ' < runs/style_budgets)"
fi
cd "$D" || return 1
# 06:33 UTC HOLD (lead + style line): S2 held until the sim-fidelity check; stop style7 with SIGTERM, never SIGINT.
# STOP files keep the loop below from relaunching; the style line lifts the hold by editing this block.
HOLD=1
if [ "$HOLD" = 1 ]; then
  for x in a b c; do
    for pid in $(pgrep -a -x python3 | grep -E "league --name style7-$x |funsearch.run --run style7-$x-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "HOLD: SIGTERM style7-$x pid $pid"; done
    for g in runs/style7-$x-g*/; do [ -d "$g" ] && touch "${g}STOP"; done
  done
  if [ ! -f runs/ec2-hold-reported ]; then
    sleep 20
    log "HOLD: style7 stopped; spend a/b/c: $(for x in a b c; do python3 -c "import funsearch.league as l; print(round(l.spent('style7-$x'), 3))"; done | tr '\n' ' ')$(for x in a b c; do echo -n " $x:$(cat runs/style7-$x-g1/programs.jsonl 2>/dev/null | wc -l)lines"; done)"
    touch runs/ec2-hold-reported
  fi
fi
for x in a b c; do
  b=$(grep "^$x " runs/style_budgets | cut -d' ' -f2); [ -n "$b" ] || continue
  running "league --name style7-$x " && continue
  ls runs/style7-$x-g*/STOP > /dev/null 2>&1 && continue
  if [ -f runs/style7-$x.ec2-launched ] && tail -n 1 runs/style7-$x.log 2>/dev/null | grep -q 'budget spent'; then
    [ -f runs/style7-$x.ec2-reported ] || { log "style7-$x exited: $(tail -n 1 runs/style7-$x.log)"; touch runs/style7-$x.ec2-reported; }
    continue
  fi
  [ -f runs/style7-$x.ec2-launched ] && log "style7-$x not running: relaunching (resumes from its programs.jsonl)"
  setsid nohup sh runs/style_launch.sh $x $b >> runs/style7-$x.out 2>&1 < /dev/null &
  touch runs/style7-$x.ec2-launched
  log "launched style7-$x (budget \$$b)"
done
# snapshot: complete JSON lines only (like runs/style_push_state.sh), never scripts or budgets
rm -rf /root/bc/style-snap && mkdir -p /root/bc/style-snap/runs
for d in runs/style7-*-g*/; do
  [ -d "$d" ] || continue; mkdir -p "/root/bc/style-snap/$d"
  for f in programs.jsonl proposals.jsonl; do
    [ -f "$d$f" ] && python3 -c '
import sys, json
out = []
for line in open(sys.argv[1]):
    try: json.loads(line); out.append(line)
    except Exception: pass
open(sys.argv[2], "w").writelines(out)' "$d$f" "/root/bc/style-snap/$d$f"
  done
done
cp runs/style7-*.json runs/style7-?.log runs/style7-*-g*.log runs/style7-?.out /root/bc/style-snap/runs/ 2>/dev/null
push_state funsearch/style-state runs /root/bc/style-snap/runs
push_state remote/style remote/style/runs /root/bc/style-snap/runs
