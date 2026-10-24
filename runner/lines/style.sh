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
# Job S5 (style line, 09:34 UTC): same procedure as S4 on funsearch/style 88e3783 (merges deploy/v0: fuel recalibration,
# op codes; pair-farming priority in h's directive; fuel-gate rule in b's). h at g3 0 programs, b resumes mid-round.
if [ -f runs/ec2-s4-checked ] && [ ! -f runs/ec2-s5 ]; then
  lastleft() { grep -oE '\$[0-9.]+ left' "runs/style8-$1.log" 2>/dev/null | tail -n 1 | tr -dc '0-9.'; }
  echo "h $(lastleft h) b $(lastleft b)" > runs/ec2-s5-left
  for x in h b; do
    for pid in $(pgrep -a -x python3 | grep -E "league --name style8-$x |funsearch.run --run style8-$x-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S5: SIGTERM style8-$x pid $pid"; done
  done
  sleep 15
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 88e3783 HEAD && build "$D" &&
     python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
    for x in h b; do wc -l < runs/style8-$x.log > runs/ec2-s5-mark-$x; done
    touch runs/ec2-s5
    log "S5: at $(git rev-parse --short HEAD) (has 88e3783: deploy/v0 merge, pair-farming h, fuel-gate b), rebuilt, $(tail -n 1 /root/bc/style-pytest.txt); left before: $(cat runs/ec2-s5-left); relaunching h and b"
  else
    echo "S5 merge/build/tests failed; h and b stopped, a/c paused" > "$D/HALT"; log "HALT: S5 merge/build/tests failed"; return 1
  fi
fi
# Job S6 (style line, 11:32 UTC): new island h2 on funsearch/style 97e64e9 (script/policy only, no rebuild): fresh
# style8-h2, $2.2 from runs/style_budgets, H_* threads apply to h and h2. h and b keep running (not restarted);
# a stays paused (budget capped at its $0.04 spend). One-shot merge; the loop below starts h2.
if [ -f runs/ec2-s5-checked ] && [ ! -f runs/ec2-s6 ]; then
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 97e64e9 HEAD && grep -q '^h2 ' runs/style_budgets; then
    touch runs/ec2-s6; log "S6: at $(git rev-parse --short HEAD) (has 97e64e9), no rebuild; budgets: $(tr '\n' ' ' < runs/style_budgets)"
  else
    log "S6: merge to 97e64e9 failed; h2 not started"; return 1
  fi
fi
# S6b (style line, 11:35 UTC): h2 on ac873bb instead (tune-v20 replaces v18 in h/h2's fixed; script/policy only).
# Restart h2 only (it resumes its few programs); h and b keep running. One-shot.
if [ -f runs/ec2-s6 ] && [ ! -f runs/ec2-s6b ]; then
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor ac873bb HEAD; then
    for pid in $(pgrep -a -x python3 | grep -E "league --name style8-h2 |funsearch.run --run style8-h2-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S6b: SIGTERM style8-h2 pid $pid"; done
    sleep 10; wc -l < runs/style8-h2.log > runs/ec2-s6b-mark; touch runs/ec2-s6b
    log "S6b: at $(git rev-parse --short HEAD) (has ac873bb); h2 restarting below"
  else
    log "S6b: merge to ac873bb failed"; return 1
  fi
fi
# S7 (style line, 12:40 UTC): once h2's current boundary validation logs its verdict ("no promotion" or "PROMOTED"),
# restart h2 (then b) on funsearch/style 3f7dae9 (amended from ffac9e9/45b71ea: 8-byte shared memory, pair roles in byte 7 bits 2-7; tune-v21 replaces v19 in h2's fixed; directive uses shared-memory
# offsets 8+; script/policy/directive only, no rebuild). A promoted policy file stays in place. b keeps running.
if [ -f runs/ec2-s6b-checked ] && [ ! -f runs/ec2-s7 ]; then
  verdicts() { grep -cE 'no promotion|PROMOTED' runs/style8-h2.log 2>/dev/null; }
  [ -f runs/ec2-s7-mark ] || { verdicts > runs/ec2-s7-mark; log "S7: waiting for h2's boundary verdict (verdict lines so far: $(cat runs/ec2-s7-mark))"; }
  # 13:04 UTC (style line): h2's verdict landed at 12:39:50, before S7's baseline was taken, so run S7 now (no gate)
  if true; then
    v=$(grep -E 'no promotion|PROMOTED' runs/style8-h2.log | tail -n 1 | cut -c1-160)
    # final amendment (12:44 UTC): 3f7dae9 = 45b71ea + funsearch/runs a43aede (league/run code changed, no interp/sim),
    # so b restarts right after h2 to keep both on one code version (b resumes mid-round from programs.jsonl)
    for x in h2 b; do
      for pid in $(pgrep -a -x python3 | grep -E "league --name style8-$x |funsearch.run --run style8-$x-" | cut -d' ' -f1); do
        kill -TERM "$pid" && log "S7: SIGTERM style8-$x pid $pid"; done
    done
    sleep 10
    if git fetch -q origin funsearch/style &&
       { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
       git merge-base --is-ancestor 3f7dae9 HEAD && python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
      wc -l < runs/style8-h2.log > runs/ec2-s7-lmark; wc -l < runs/style8-b.log > runs/ec2-s7-bmark; touch runs/ec2-s7
      log "S7: h2 verdict: $v; at $(git rev-parse --short HEAD) (has 3f7dae9), $(tail -n 1 /root/bc/style-pytest.txt); h2 and b restarting below; promoted files kept: $(ls policies/style-h2*.policy 2>/dev/null | tr '\n' ' ')"
    else
      echo "S7 merge/3f7dae9/pytest failed; h2 and b stopped" > "$D/HALT"; log "HALT: S7 merge/3f7dae9/pytest failed"; return 1
    fi
  fi
fi
# S8 (jobs/style 49213a5, 14:17 UTC): rebuild on funsearch/style ed49293 (new block unit_tributing + capture-metric
# counters change the binary, so h2 and b restart together), then the resumable conversion gap run style8-gconv ($2).
if [ -f runs/ec2-s7-checked ] && [ ! -f runs/ec2-s8 ]; then
  for x in h2 b; do
    for pid in $(pgrep -a -x python3 | grep -E "league --name style8-$x |funsearch.run --run style8-$x-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S8: SIGTERM style8-$x pid $pid"; done
  done
  sleep 15
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor ed49293 HEAD && build "$D" && python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
    touch runs/ec2-s8
    log "S8: at $(git rev-parse --short HEAD) (has ed49293), rebuilt, $(tail -n 1 /root/bc/style-pytest.txt); h2 and b restarting, gap run style8-gconv starting"
  else
    echo "S8 merge/ed49293/build/tests failed; h2 and b stopped" > "$D/HALT"; log "HALT: S8 merge/build/tests failed"; return 1
  fi
fi
# 14:17 UTC (style line): HOLD the gconv gap run until a new commit + launch command arrive. Stop it if running;
# its spend carries over on relaunch (the launcher subtracts programs.jsonl cost). Set GCONV_HOLD=0 to release.
GCONV_HOLD=1
# S9 (jobs/style 8bd0586, 14:43 UTC): release gconv on funsearch/style 6e8cc17 (deploy/v0 d23c1cb: 15 calibrated gap
# sensors + sim recalibration -> rebuild; hill-climb + helpers; trimmed directive). Restart b first; a/c/h2 stay off.
if [ -f runs/ec2-s8 ] && [ ! -f runs/ec2-s9 ]; then
  for pid in $(pgrep -a -x python3 | grep -E "league --name style8-b |funsearch.run --run style8-b-|funsearch.run --run style8-gconv " | cut -d' ' -f1); do
    kill -TERM "$pid" && log "S9: SIGTERM pid $pid"; done
  sleep 15
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 6e8cc17 HEAD && build "$D" && python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
    wc -l < runs/style8-gconv.out > runs/ec2-s9-outmark 2>/dev/null || echo 0 > runs/ec2-s9-outmark
    touch runs/ec2-s9
    log "S9: at $(git rev-parse --short HEAD) (has 6e8cc17), rebuilt, $(tail -n 1 /root/bc/style-pytest.txt); restarting b, releasing gconv"
  else
    echo "S9 merge/6e8cc17/build/tests failed; b and gconv stopped" > "$D/HALT"; log "HALT: S9 merge/build/tests failed"; return 1
  fi
fi
[ -f runs/ec2-s9 ] && GCONV_HOLD=0
# S10 (style line, 14:58 UTC): restart gconv only on funsearch/style 34f261c (b48422d: hill-climb evaluations skip the
# 40 gap games; cheap climb settings in the launcher). Python/script only, no rebuild; b keeps running. One-shot.
if [ -f runs/ec2-s9-checked ] && [ ! -f runs/ec2-s10 ]; then
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 34f261c HEAD; then
    for pid in $(pgrep -a -x python3 | grep -F 'funsearch.run --run style8-gconv ' | cut -d' ' -f1); do
      kill -TERM "$pid" && log "S10: SIGTERM style8-gconv pid $pid"; done
    sleep 10; wc -l < runs/style8-gconv.out > runs/ec2-s10-outmark; touch runs/ec2-s10
    log "S10: at $(git rev-parse --short HEAD) (has 34f261c), no rebuild; gconv relaunching below"
  else
    log "S10: merge to 34f261c failed; gconv left as is"; touch runs/ec2-s10-failed
  fi
fi
# S11 (style line, 15:07 UTC): gconv AND b on funsearch/style 5b70f04 (34f261c + deploy/v0 e32dc0d: v22 group_threat
# dead-camp fix in sim/src/api.cpp, new cost tables) -> rebuild, pytest, relaunch both (spend carries over). One-shot.
if [ -f runs/ec2-s10 ] && [ ! -f runs/ec2-s11 ]; then
  for pid in $(pgrep -a -x python3 | grep -E "league --name style8-b |funsearch.run --run style8-b-|funsearch.run --run style8-gconv " | cut -d' ' -f1); do
    kill -TERM "$pid" && log "S11: SIGTERM pid $pid"; done
  sleep 15
  if git fetch -q origin funsearch/style &&
     { git merge -q --ff-only origin/funsearch/style 2>/dev/null || git merge -q --no-edit origin/funsearch/style; } &&
     git merge-base --is-ancestor 5b70f04 HEAD && build "$D" && python3 -m pytest -q tests > /root/bc/style-pytest.txt 2>&1; then
    wc -l < runs/style8-gconv.out > runs/ec2-s11-outmark; wc -l < runs/style8-b.log > runs/ec2-s11-bmark; touch runs/ec2-s11
    log "S11: at $(git rev-parse --short HEAD) (has 5b70f04: v22 dead-camp fix), rebuilt, $(tail -n 1 /root/bc/style-pytest.txt); relaunching b and gconv"
  else
    echo "S11 merge/5b70f04/build/tests failed; b and gconv stopped" > "$D/HALT"; log "HALT: S11 merge/build/tests failed"; return 1
  fi
fi
if [ -f runs/ec2-s11 ] && [ ! -f runs/ec2-s11-checked ]; then
  o=$(tail -n +"$(( $(cat runs/ec2-s11-outmark) + 1 ))" runs/style8-gconv.out 2>/dev/null)
  fb=$(tail -n +"$(( $(cat runs/ec2-s11-bmark) + 1 ))" runs/style8-b.log 2>/dev/null | grep -m1 'style8-b-g')
  echo "$o" | grep -q 'left of' && [ -n "$fb" ] && { touch runs/ec2-s11-checked; log "S11 check: gconv $(echo "$o" | grep -m1 -oE '\$[0-9.]+ left of \$[0-9.]+'); b $(echo "$fb" | grep -oE 'style8-b-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$fb" | grep -oE '\$[0-9.]+ left')"; }
fi
if [ -f runs/ec2-s10 ] && [ ! -f runs/ec2-s10-checked ]; then
  o=$(tail -n +"$(( $(cat runs/ec2-s10-outmark) + 1 ))" runs/style8-gconv.out 2>/dev/null)
  echo "$o" | grep -q 'left of' && { touch runs/ec2-s10-checked; log "S10 check: gconv relaunched: $(echo "$o" | grep -m1 -oE '\$[0-9.]+ left of \$[0-9.]+')"; }
fi
if [ "$GCONV_HOLD" = 1 ]; then
  for pid in $(pgrep -a -x python3 | grep -F 'funsearch.run --run style8-gconv ' | cut -d' ' -f1); do
    kill -TERM "$pid" && log "S8 HOLD: SIGTERM style8-gconv pid $pid"; done
  if [ ! -f runs/style8-gconv.ec2-held ]; then
    sleep 5; touch runs/style8-gconv.ec2-held
    log "S8 HOLD: gconv stopped; spend \$$(python3 -c "
import json, pathlib
p = pathlib.Path('runs/style8-gconv/programs.jsonl')
print(round(sum(json.loads(l)['metrics'].get('cost', 0.0) for l in open(p)), 3) if p.exists() else 0.0)") over $(cat runs/style8-gconv/programs.jsonl 2>/dev/null | wc -l) lines"
  fi
fi
if [ "$GCONV_HOLD" != 1 ] && [ -f runs/ec2-s8 ] && [ ! -f runs/style8-gconv.ec2-done ] && ! pgrep -a -x python3 | grep -q 'funsearch.run --run style8-gconv '; then
  if [ -f runs/style8-gconv.ec2-launched ] && tail -n 3 runs/style8-gconv.out 2>/dev/null | grep -qE '^done:|\$0\.00 left'; then
    touch runs/style8-gconv.ec2-done; log "S8: style8-gconv finished: $(tail -n 1 runs/style8-gconv.out | cut -c1-160)"
  else
    [ -f runs/style8-gconv.ec2-launched ] && log "S8: style8-gconv not running: relaunching (resumes)"
    GAP_OPPONENTS="builtin:starter@0.25,policies/tune-v21.policy@3,policies/opp-finisher.policy,policies/opp-hunter3.policy,policies/opp-hunter2b.policy,policies/pool/opp-metadraft.policy" \
      WORKERS=2 EVAL_THREADS=2 setsid nohup sh runs/style_gap_launch.sh style8-gconv 2.0 conversion:max:0.05 policies/tune-v21.policy funsearch/styles/g_conversion.txt >> runs/style8-gconv.out 2>&1 < /dev/null &
    touch runs/style8-gconv.ec2-launched; log "S8: launched style8-gconv (\$2.0 total)"
  fi
fi
if [ -f runs/ec2-s9 ] && [ ! -f runs/ec2-s9-checked ]; then
  o=$(tail -n +"$(( $(cat runs/ec2-s9-outmark) + 1 ))" runs/style8-gconv.out 2>/dev/null)
  if echo "$o" | grep -q 'mirror value'; then
    touch runs/ec2-s9-checked
    log "S9 check: $(echo "$o" | grep -m1 -oE '\$[0-9.]+ left of \$[0-9.]+'); $(echo "$o" | grep -m1 -oE 'reference [^;]*')"
  fi
fi
if [ -f runs/style8-gconv.ec2-launched ] && [ ! -f runs/style8-gconv.ec2-metric ]; then
  gm=$(grep -m1 'gap metric' runs/style8-gconv.out runs/style8-gconv.log 2>/dev/null | cut -d: -f2- | cut -c1-200)
  [ -n "$gm" ] && { touch runs/style8-gconv.ec2-metric; log "S8 gap line: $gm"; }
fi
for x in h h2 b a c; do
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
if [ -f runs/ec2-s5 ] && [ ! -f runs/ec2-s5-checked ]; then
  fh=$(tail -n +"$(( $(cat runs/ec2-s5-mark-h) + 1 ))" runs/style8-h.log | grep -m1 'style8-h-g')
  fb=$(tail -n +"$(( $(cat runs/ec2-s5-mark-b) + 1 ))" runs/style8-b.log | grep -m1 'style8-b-g')
  if [ -n "$fh" ] && [ -n "$fb" ]; then
    touch runs/ec2-s5-checked
    log "S5 check: h: $(echo "$fh" | grep -q 'style8-h-g3: .*best policies/style-h1.policy' && echo 'g3 best style-h1 ok' || echo 'UNEXPECTED') $(echo "$fh" | grep -q tune-v19 && echo 'tune-v19 in league' || echo 'tune-v19 MISSING') $(echo "$fh" | grep -oE '\$[0-9.]+ left'); b: $(echo "$fb" | grep -oE 'style8-b-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$fb" | grep -oE '\$[0-9.]+ left'); before: $(cat runs/ec2-s5-left)"
  fi
fi
if [ -f runs/ec2-s6 ] && [ ! -f runs/ec2-s6-checked ] && [ -f runs/style8-h2.log ]; then
  f2=$(grep -m1 'style8-h2-g' runs/style8-h2.log)
  if [ -n "$f2" ] && grep -q 'injected' runs/style8-h2-g1.log 2>/dev/null; then
    touch runs/ec2-s6-checked
    log "S6 check: h2: $(echo "$f2" | grep -q 'style8-h2-g1: .*best policies/opp-hunter3.policy' && echo 'g1 best opp-hunter3 ok' || echo 'UNEXPECTED') $(echo "$f2" | grep -q tune-v19 && echo 'tune-v19 in league' || echo 'tune-v19 MISSING') $(echo "$f2" | grep -oE '\$[0-9.]+ left'); $(grep -m1 -o 'injected [^ ]*' runs/style8-h2-g1.log)"
  fi
fi
if [ -f runs/ec2-s6b ] && [ ! -f runs/ec2-s6b-checked ]; then
  f2=$(tail -n +"$(( $(cat runs/ec2-s6b-mark) + 1 ))" runs/style8-h2.log | grep -m1 'style8-h2-g')
  [ -n "$f2" ] && { touch runs/ec2-s6b-checked; log "S6b check: h2: $(echo "$f2" | grep -q "league \['policies/tune-v20.policy'" && echo 'tune-v20 first in league' || echo 'tune-v20 NOT first') $(echo "$f2" | grep -oE 'best [^,]*') $(echo "$f2" | grep -oE '\$[0-9.]+ left')"; }
fi
if [ -f runs/ec2-s7 ] && [ ! -f runs/ec2-s7-checked ]; then
  f2=$(tail -n +"$(( $(cat runs/ec2-s7-lmark) + 1 ))" runs/style8-h2.log | grep -m1 'style8-h2-g')
  fb=$(tail -n +"$(( $(cat runs/ec2-s7-bmark) + 1 ))" runs/style8-b.log | grep -m1 'style8-b-g')
  [ -n "$f2" ] && [ -n "$fb" ] && { touch runs/ec2-s7-checked; log "S7 check: h2: $(echo "$f2" | grep -q "league \['policies/tune-v21.policy'" && echo 'tune-v21 first in league' || echo 'tune-v21 NOT first') $(echo "$f2" | grep -oE 'style8-h2-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$f2" | grep -oE 'best [^,]*') $(echo "$f2" | grep -oE '\$[0-9.]+ left'); b: $(echo "$fb" | grep -oE 'style8-b-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$fb" | grep -oE '\$[0-9.]+ left')"; }
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
cp runs/style8-*.json runs/style8-*.log runs/style8-*.out /root/bc/style-snap/runs/ 2>/dev/null
if [ -f runs/style8-gconv/programs.jsonl ]; then   # S8 gap run (plain funsearch.run, no league)
  mkdir -p /root/bc/style-snap/runs/style8-gconv
  python3 -c '
import sys, json
out = []
for line in open(sys.argv[1]):
    try: json.loads(line); out.append(line)
    except Exception: pass
open(sys.argv[2], "w").writelines(out)' runs/style8-gconv/programs.jsonl /root/bc/style-snap/runs/style8-gconv/programs.jsonl
fi
push_state funsearch/style-state runs /root/bc/style-snap/runs
push_state remote/style remote/style/runs /root/bc/style-snap/runs
