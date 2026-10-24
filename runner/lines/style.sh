# style line: S2 released as style8 (jobs/style/JOBS.md, jobs/style 4ce5116), code funsearch/style 5c47501.
# Fresh islands style8-h/b/a/c; budgets from runs/style_budgets (h 3.95, b 3.5, a 2.25, c 2.25 = $11.95).
# The old style7-a/b/c state (stopped 06:58 UTC by the hold, STOP files) stays in runs/ archived; nothing resumes it.
# Shared box: WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3. State out: runs/style8-* -> funsearch/style-state, remote/style.
D=/root/bc/style
REV=5c47501
export WORKERS=1 EVAL_THREADS=1 VAL_THREADS=3
[ -f "$D/HALT" ] && { log "halted: $(cat "$D/HALT")"; return 0; }
if [ ! -d "$D/.git" ]; then clone_nopush "$REV" "$D" || { log "clone failed"; return 1; }; fi
cd "$D" || return 1
if [ ! -f "$D/.setup-$REV" ]; then
  git fetch -q origin funsearch/style && git checkout -q -f "$REV" || { log "checkout $REV failed"; return 1; }
  n=$(grep -c 'slot_stun\|slot_range\|slot_radius' interp/src/block_costs_gen.inc)
  [ "$n" = 3 ] || { echo "gate check printed $n, expected 3" > "$D/HALT"; log "HALT: gate check printed $n"; return 1; }
  build "$D" || { log "build failed: $(tail -n 3 interp/build/build.log)"; return 1; }
  python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1 || { log "pytest failed: $(tail -n 2 /root/bc/style-pytest.txt)"; return 1; }
  touch "$D/.setup-$REV"
  log "style8 setup ok at $REV: gate 3, $(tail -n 1 /root/bc/style-pytest.txt); budgets: $(tr '\n' ' ' < runs/style_budgets)"
fi
# 07:30 UTC (style line): restart ONLY island h on b59e19e (adds policies/tune-v18.policy to h's FIXED; script and
# policy only, no rebuild). b/a/c keep running on their loaded code. One-shot; the loop below relaunches h.
if [ ! -f runs/ec2-h-v18 ] && [ -f "$D/.setup-$REV" ]; then
  git fetch -q origin funsearch/style && git merge-base --is-ancestor HEAD b59e19e && git checkout -q -f b59e19e &&
    grep -q tune-v18 runs/style_launch.sh || { log "h-v18: checkout b59e19e failed"; return 1; }
  for pid in $(pgrep -a -x python3 | grep -E "league --name style8-h |funsearch.run --run style8-h-" | cut -d' ' -f1); do
    kill -TERM "$pid" && log "h-v18: SIGTERM style8-h pid $pid"; done
  sleep 15
  wc -l < runs/style8-h.log > runs/ec2-h-v18-mark; touch runs/ec2-h-v18
  log "h-v18: at b59e19e; style8-h stopped, relaunching below"
fi
for x in h b a c; do
  b=$(grep "^$x " runs/style_budgets | cut -d' ' -f2); [ -n "$b" ] || continue
  running "league --name style8-$x " && continue
  ls runs/style8-$x-g*/STOP > /dev/null 2>&1 && continue
  if [ -f runs/style8-$x.ec2-launched ] && tail -n 1 runs/style8-$x.log 2>/dev/null | grep -q 'budget spent'; then
    [ -f runs/style8-$x.ec2-reported ] || { log "style8-$x exited: $(tail -n 1 runs/style8-$x.log)"; touch runs/style8-$x.ec2-reported; }
    continue
  fi
  [ -f runs/style8-$x.ec2-launched ] && log "style8-$x not running: relaunching (resumes from its programs.jsonl)"
  setsid nohup sh runs/style_launch.sh $x $b >> runs/style8-$x.out 2>&1 < /dev/null &
  touch runs/style8-$x.ec2-launched
  log "launched style8-$x (budget \$$b)"
done
if [ -f runs/ec2-h-v18 ] && [ ! -f runs/ec2-h-v18-checked ]; then
  first=$(tail -n +"$(( $(cat runs/ec2-h-v18-mark) + 1 ))" runs/style8-h.log | grep -m1 'style8-h-g')
  [ -n "$first" ] && { touch runs/ec2-h-v18-checked; log "h-v18 check: $(echo "$first" | grep -q tune-v18 && echo 'tune-v18 in league' || echo 'tune-v18 MISSING'); $(echo "$first" | grep -oE '\$[0-9.]+ left')"; }
fi
# snapshot: complete JSON lines only (like runs/style_push_state.sh), never scripts or budgets
rm -rf /root/bc/style-snap && mkdir -p /root/bc/style-snap/runs
for d in runs/style8-*-g*/; do
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
cp runs/style8-*.json runs/style8-?.log runs/style8-*-g*.log runs/style8-?.out /root/bc/style-snap/runs/ 2>/dev/null
push_state funsearch/style-state runs /root/bc/style-snap/runs
push_state remote/style remote/style/runs /root/bc/style-snap/runs
