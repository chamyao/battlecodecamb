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
# Job S3 (jobs/style 618411f, 07:31 UTC): pause islands a and c (STOP + SIGTERM; budgets kept for later), restart
# island h on funsearch/style 3d34e37 (v18 in h's fixed, --round 40, extra directions; script/policy/directive only,
# no rebuild) with H_WORKERS=2 H_EVAL_THREADS=2. Island b keeps running untouched. One-shot; the loop relaunches h.
export H_WORKERS=2 H_EVAL_THREADS=2
if [ ! -f runs/ec2-s3 ] && [ -f "$D/.setup-$REV" ]; then
  git fetch -q origin funsearch/style && git merge-base --is-ancestor HEAD 3d34e37 && git checkout -q -f 3d34e37 &&
    grep -q tune-v18 runs/style_launch.sh || { log "S3: checkout 3d34e37 failed"; return 1; }
  for x in a c; do
    for g in runs/style8-$x-g*/; do [ -d "$g" ] && touch "${g}STOP"; done
    for pid in $(pgrep -a -x python3 | grep -E "league --name style8-$x |funsearch.run --run style8-$x-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S3: paused style8-$x (SIGTERM pid $pid)"; done
  done
  for pid in $(pgrep -a -x python3 | grep -E "league --name style8-h |funsearch.run --run style8-h-" | cut -d' ' -f1); do
    kill -TERM "$pid" && log "S3: SIGTERM style8-h pid $pid"; done
  sleep 15
  wc -l < runs/style8-h.log > runs/ec2-s3-mark; touch runs/ec2-s3
  log "S3: at 3d34e37; a and c paused (STOP files), h stopped and relaunching below, b untouched"
fi
# Job S4 (style line, 08:25 UTC, amended 08:27 to 05bb372 = 5ad7da6 + tune-v19 in h's fixed): rebuild on 05bb372 (5ad7da6
# coord/blocks ace7eb9: op codes change, so h AND b restart together; fuel-gate rule in the h/b directives).
# a/c stay paused. One-shot; on success the loop below relaunches h and b, which resume from programs.jsonl.
if [ -f runs/ec2-s3 ] && [ ! -f runs/ec2-s4 ]; then
  lastleft() { grep -oE '\$[0-9.]+ left' "runs/style8-$1.log" 2>/dev/null | tail -n 1 | tr -dc '0-9.'; }
  echo "h $(lastleft h) b $(lastleft b)" > runs/ec2-s4-left
  for x in h b; do
    for pid in $(pgrep -a -x python3 | grep -E "league --name style8-$x |funsearch.run --run style8-$x-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S4: SIGTERM style8-$x pid $pid"; done
  done
  sleep 15
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 05bb372 HEAD && build "$D" &&
     python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
    for x in h b; do wc -l < runs/style8-$x.log > runs/ec2-s4-mark-$x; done
    touch runs/ec2-s4
    log "S4: at $(git rev-parse --short HEAD) (has 05bb372: tune-v19 in h fixed), rebuilt, $(tail -n 1 /root/bc/style-pytest.txt); left before: $(cat runs/ec2-s4-left); relaunching h and b"
  else
    echo "S4 merge/build/tests failed; h and b stopped, a/c paused" > "$D/HALT"; log "HALT: S4 merge/build/tests failed"; return 1
  fi
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
if [ -f runs/ec2-s3 ] && [ ! -f runs/ec2-s3-checked ]; then
  first=$(tail -n +"$(( $(cat runs/ec2-s3-mark) + 1 ))" runs/style8-h.log | grep -m1 'style8-h-g')
  [ -n "$first" ] && { touch runs/ec2-s3-checked; log "S3 h check: $(echo "$first" | grep -q tune-v18 && echo 'tune-v18 in league' || echo 'tune-v18 MISSING'); $(echo "$first" | grep -oE '\$[0-9.]+ left')"; }
fi
if [ -f runs/ec2-s4 ] && [ ! -f runs/ec2-s4-checked ]; then
  fh=$(tail -n +"$(( $(cat runs/ec2-s4-mark-h) + 1 ))" runs/style8-h.log | grep -m1 'style8-h-g')
  fb=$(tail -n +"$(( $(cat runs/ec2-s4-mark-b) + 1 ))" runs/style8-b.log | grep -m1 'style8-b-g')
  if [ -n "$fh" ] && [ -n "$fb" ]; then
    touch runs/ec2-s4-checked
    log "S4 check: h: $(echo "$fh" | grep -q 'style8-h-g2: .*best policies/style-h1.policy' && echo 'g2 best style-h1 ok' || echo 'UNEXPECTED') $(echo "$fh" | grep -q tune-v19 && echo 'tune-v19 in league' || echo 'tune-v19 MISSING') $(echo "$fh" | grep -oE '\$[0-9.]+ left'); b: $(echo "$fb" | grep -oE 'style8-b-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$fb" | grep -oE '\$[0-9.]+ left'); before: $(cat runs/ec2-s4-left)"
  fi
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
