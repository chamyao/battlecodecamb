# hybrid line: resume hyb4 (jobs/hybrid/JOBS.md "EC2 resume", 28e6aa3). Never a fresh start.
# State in: remote/hybrid remote/hybrid/runs/ (04:54 UTC snapshot; Cham confirmed no newer state).
# State out: runs/ -> remote/hybrid remote/hybrid/runs/, promoted policies -> remote/hybrid policies/.
D=/root/bc/hybrid
[ -f "$D/HALT" ] && { log "halted: $(cat "$D/HALT")"; return 0; }
if [ ! -f "$D/.setup-done" ]; then
  clone_nopush funsearch/runs "$D" || { log "clone failed"; return 1; }
  cd "$D" && git fetch -q origin remote/hybrid && mkdir -p runs &&
    git archive origin/remote/hybrid remote/hybrid/runs | tar -x --strip-components=2 -C . || { log "state overlay failed"; return 1; }
  build "$D" || { log "build failed: $(tail -n 3 interp/build/build.log)"; return 1; }
  python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1 || { log "pytest failed: $(tail -n 2 runs/ec2-pytest.txt)"; return 1; }
  for p in policies/candidates/hyb-t5m.policy policies/candidates/hyb-t5m-rich15d6f.policy; do
    grep -qx "$p" runs/hyb4.challengers || echo "$p" >> runs/hyb4.challengers; done
  wc -l < runs/hyb4.log > runs/ec2-resume-mark      # log lines before the EC2 resume, for the resume check
  touch "$D/.setup-done"
  log "setup ok at $(git rev-parse --short HEAD): $(tail -n 1 runs/ec2-pytest.txt); challengers: $(tr '\n' ' ' < runs/hyb4.challengers)"
fi
cd "$D" || return 1
pushall() {
  push_state remote/hybrid remote/hybrid/runs runs
  if ls policies/fs-h*.policy > /dev/null 2>&1; then
    mkdir -p /root/bc/hybrid-pol && cp -a policies/fs-h*.policy /root/bc/hybrid-pol/ && push_state remote/hybrid policies /root/bc/hybrid-pol
  fi
}
# ---- Job H3 (jobs/hybrid dc9280f, 09:00 UTC, lead-approved): hyb4 ends at its g4 verdict; hyb5 on v19 with exploration
if [ -f runs/ec2-hyb5 ]; then
  # Job H4 (jobs/hybrid, 10:55 UTC, lead-approved): retune hyb5 at its next round boundary (90 so far or later):
  # hold -> SIGTERM -> merge funsearch/runs 8c5b4e4+ -> rebuild -> pytest -> relaunch with 3 changed flags.
  ARCH=0.3; SEEDS=policies/pool/v19.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/opp-hunter3.policy; AXES=
  if [ -f runs/ec2-h4 ]; then
    ARCH=0.1; SEEDS=policies/pool/v19.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v19.policy
    AXES="--axes items,vision,teleport,team,roles,pairs,macro,abilities,combat"
  else
    [ -f runs/ec2-h4-hold ] || { touch runs/hyb5.hold runs/ec2-h4-hold; log "H4: hold set for the next hyb5 boundary"; }
    if tail -n 3 runs/hyb5.log | grep -q 'hold file present'; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H4: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor 8c5b4e4 HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        for f in runs/hyb5-g*.log; do echo "$f $(wc -l < "$f")"; done > runs/ec2-h4-marks
        rm -f runs/hyb5.hold; touch runs/ec2-h4
        ARCH=0.1; SEEDS=policies/pool/v19.policy,policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v19.policy
        AXES="--axes items,vision,teleport,team,roles,pairs,macro,abilities,combat"
        log "H4: funsearch/runs $(git rev-parse --short HEAD) (has 8c5b4e4), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 retuned"
      else
        echo "H4 merge/8c5b4e4/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H4 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # Job H5 (jobs/hybrid, 11:35 UTC): rebase hyb5 on live v20 at the next boundary (150 so far or later), H4 mechanics:
  # hold -> SIGTERM -> merge funsearch/runs d0cbd58+ (no interp change) -> pytest -> v20 challenger -> relaunch.
  CREF=policies/pool/v19.policy
  if [ -f runs/ec2-h5 ]; then
    SEEDS=policies/pool/v20.policy,policies/pool/v20.policy,policies/pool/lean-g65.policy,policies/pool/v20.policy; CREF=policies/pool/v20.policy
  elif [ -f runs/ec2-h4-checked ]; then
    if [ ! -f runs/ec2-h5-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h5-holdmark; touch runs/hyb5.hold runs/ec2-h5-hold
      log "H5: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h5-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H5: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor d0cbd58 HEAD && [ -f policies/pool/v20.policy ] && build "$D" &&
         python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        grep -qx policies/pool/v20.policy runs/hyb5.challengers 2>/dev/null || echo policies/pool/v20.policy >> runs/hyb5.challengers
        for f in runs/hyb5-g*.log; do echo "$f $(wc -l < "$f")"; done > runs/ec2-h5-marks
        rm -f runs/hyb5.hold; touch runs/ec2-h5
        SEEDS=policies/pool/v20.policy,policies/pool/v20.policy,policies/pool/lean-g65.policy,policies/pool/v20.policy; CREF=policies/pool/v20.policy
        log "H5: funsearch/runs $(git rev-parse --short HEAD) (has d0cbd58), $(tail -n 1 runs/ec2-pytest.txt); v20 challenger queued; relaunching on v20"
      else
        echo "H5 merge/d0cbd58/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H5 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # H6 (hybrid line, 12:15 UTC): at the next hyb5 boundary merge funsearch/runs 48a1404+ (prompt-only shared-memory
  # change: byte 7 bits 0-1 reserved for tune's lock flags; no interp change) and relaunch with the same flags.
  if [ -f runs/ec2-h5 ] && [ ! -f runs/ec2-h6 ]; then
    if [ ! -f runs/ec2-h6-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h6-holdmark; touch runs/hyb5.hold runs/ec2-h6-hold
      log "H6: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h6-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H6: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor 48a1404 HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        rm -f runs/hyb5.hold; touch runs/ec2-h6
        log "H6: funsearch/runs $(git rev-parse --short HEAD) (has 48a1404), $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5, same flags"
      else
        echo "H6 merge/48a1404/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H6 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  if ! running "league --name hyb5"; then
    if [ -f runs/hyb5.ec2-launched ] && ls runs/hyb5-g*/STOP > /dev/null 2>&1; then
      log "hyb5 not running and a STOP file is present: leaving it paused"
    elif [ -f runs/hyb5.ec2-launched ] && tail -n 1 runs/hyb5.log 2>/dev/null | grep -q 'budget spent'; then
      [ -f runs/hyb5.ec2-reported ] || { log "hyb5 exited: $(tail -n 1 runs/hyb5.log)"; touch runs/hyb5.ec2-reported; }
    else
      [ -f runs/hyb5.ec2-launched ] && log "hyb5 not running: relaunching (resume from runs/)"
      setsid nohup python3 -m funsearch.league --name hyb5 --threads 5 --budget 25.0 \
        --members policies/pool/v19.policy,policies/pool/lean-g65.policy,policies/pool/v18.policy \
        --fixed policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-hunter2a.policy,policies/pool/opp-metadraft.policy,policies/pool/opp-icecream.policy \
        --prefix fs-h --line hybrid --round 30 --cambc-ref "$CREF" --workers 3 --eval-threads 2 \
        --explore --change-weights 0.6,0.4,0 --novelty-lambda 0.3 --archive-share "$ARCH" \
        --island-seeds "$SEEDS" $AXES \
        >> runs/hyb5.out 2>&1 < /dev/null &
      touch runs/hyb5.ec2-launched; log "launched hyb5 league"
    fi
  fi
  if [ ! -f runs/hyb5.ec2-checked ] && [ -f runs/hyb5.log ] && grep -q 'seed' runs/hyb5-g1.log 2>/dev/null; then
    first=$(grep -m1 'hyb5-g' runs/hyb5.log)
    if echo "$first" | grep -q 'hyb5-g1: +30 programs to the next boundary (0 so far), best policies/pool/v19.policy'; then
      sleep 0; touch runs/hyb5.ec2-checked
      log "hyb5 check ok: $(echo "$first" | cut -c1-110); seeds: $(grep -oE 'seed [a-z0-9-]+' runs/hyb5-g1.log | sort | uniq -c | tr -s ' ' | tr '\n' ';')"
    else
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid"; done
      echo "hyb5 first line unexpected: $first" > "$D/HALT"; log "HALT: hyb5 first line unexpected: $first"
    fi
  fi
  if [ -f runs/ec2-h4 ] && [ ! -f runs/ec2-h4-checked ]; then
    n=0; for f in runs/hyb5-g*.log; do
      m=$(awk -v f="$f" '$1==f{print $2}' runs/ec2-h4-marks); m=${m:-0}
      n=$(( n + $(tail -n +"$((m + 1))" "$f" | grep -c 're-seeded island 3 with v19') ))
      other=$(( ${other:-0} + $(tail -n +"$((m + 1))" "$f" | grep -c 're-seeded island [012]') ))
    done
    if [ "$n" -ge 1 ]; then
      touch runs/ec2-h4-checked
      log "H4 check: 're-seeded island 3 with v19' x$n (expected 1), other islands re-seeded: ${other:-0}"
    fi
  fi
  if [ -f runs/ec2-h5 ] && [ ! -f runs/ec2-h5-checked ]; then
    r=""; for f in runs/hyb5-g*.log; do
      m=$(awk -v f="$f" '$1==f{print $2}' runs/ec2-h5-marks); m=${m:-0}
      r="$r$(tail -n +"$((m + 1))" "$f" | grep -oE 're-seeded island [0-9] with [a-z0-9-]+' | tr '\n' ';')"
    done
    g=$(awk -v f=runs/hyb5.log '$1==f{print $2}' runs/ec2-h5-marks 2>/dev/null)
    newgen=$(grep -E 'PROMOTED|hyb5-g[0-9]+: \+30 programs to the next boundary \(0 so far\)' runs/hyb5.log | tail -n 2 | cut -c1-150 | tr '\n' '|')
    if [ -n "$r" ]; then
      touch runs/ec2-h5-checked; log "H5 check: $r (expected islands 0,1,3 with v20; island 2 kept)"
    elif grep -q 'PROMOTED challenger policies/pool/v20.policy' runs/hyb5.log; then
      touch runs/ec2-h5-checked; log "H5 check: no re-seed lines; v20 promoted at the boundary, new generation: $newgen"
    fi
  fi
  pushall; return 0
fi
if grep -q 'hyb4-g5: ' runs/hyb4.log; then
  if [ ! -f runs/hyb4-g5/STOP ]; then
    mkdir -p runs/hyb4-g5 && touch runs/hyb4-g5/STOP && date +%s > runs/ec2-h3-stop
    log "H3: g4 verdict logged; STOP placed in runs/hyb4-g5, waiting for hyb4 to exit"
  fi
  pids=$(pgrep -a -x python3 | grep -E "league --name hyb4|funsearch.run --run hyb4-" | cut -d' ' -f1)
  if [ -n "$pids" ]; then
    if [ $(( $(date +%s) - $(cat runs/ec2-h3-stop) )) -gt 900 ]; then
      for pid in $pids; do kill -TERM "$pid" && log "H3: SIGTERM hung hyb4 pid $pid"; done
    fi
    pushall; return 0
  fi
  pushall
  log "H3: hyb4 stopped. g4 verdict: $(sed -n '/hyb4-g4: +0 programs/,/hyb4-g5: /p' runs/hyb4.log | grep -E 'PROMOTED|no promotion|h2h' | cut -c1-160 | tr '\n' '|')"
  if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
     git merge-base --is-ancestor 557ce2c HEAD && build "$D" &&
     python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
    cat >> runs/SPEND.md <<'X'
| 2026-10-24 | exploration test xc1/xp1/xp2 (hybrid session container) | 114 | 3.21 | |
| 2026-10-24 | hyb5 started on v19 (explore), --budget 25.0 | | | |
X
    touch runs/ec2-hyb5
    log "H3: funsearch/runs $(git rev-parse --short HEAD) (has 557ce2c), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); SPEND lines appended; hyb5 launches next tick"
  else
    echo "H3 merge/557ce2c/build/tests failed; hyb4 stopped, hyb5 not started" > "$D/HALT"; log "HALT: H3 upgrade failed"
  fi
  pushall; return 0
fi
BUDGET=$(cat runs/ec2-budget 2>/dev/null || echo 9.82)   # launched at 9.82; 29.47 from the g4 boundary (JOBS.md)
# EC2 update U1 step 2 (jobs/hybrid da1a09c): tune5-campreset as a challenger now, no restart; never tune5-reset
if [ ! -f runs/ec2-u1 ]; then
  git fetch -q origin funsearch/runs && git show origin/funsearch/runs:policies/tune5-campreset.policy > policies/tune5-campreset.policy &&
    { grep -qx policies/tune5-campreset.policy runs/hyb4.challengers || echo policies/tune5-campreset.policy >> runs/hyb4.challengers; } &&
    cat >> runs/SPEND.md <<'X' && touch runs/ec2-u1 && log "U1: challenger tune5-campreset added; SPEND.md lines appended"
| 2026-10-24 | hyb4-g3 (best tune-4) on remote-server after snapshot bca8693: lost with Cham's machine (g3 verdict and later programs), not in programs.jsonl | ? | ~0.35 | |
| 2026-10-24 | hybrid line cap raised $10 -> $30 (project cap $90 -> $200). League --budget 29.47 = 30 - 0.18 (hyb, hyb2, hyb3) - 0.35 (lost above) | | | |
X
fi
# U1 step 3 + budget: hold at the g4 boundary, then merge funsearch/runs (must contain aa032ba), rebuild, test,
# relaunch with --budget 29.47. The league waits at the boundary while runs/hyb4.hold exists.
if [ ! -f runs/ec2-g4-upgraded ]; then
  grep -q 'hyb4-g4: ' runs/hyb4.log && [ ! -f runs/ec2-hold-set ] && { touch runs/hyb4.hold runs/ec2-hold-set; log "g4 started: hold set for the g4 boundary upgrade"; }
  if [ -f runs/hyb4.hold ] && tail -n 3 runs/hyb4.log | grep -q 'hold file present'; then
    for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb4' | cut -d' ' -f1); do kill -TERM "$pid"; done; sleep 10
    rm -f policies/tune5-campreset.policy   # tracked upstream; avoid the untracked-file conflict
    if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
       git merge-base --is-ancestor aa032ba HEAD && build "$D" &&
       python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
      echo 29.47 > runs/ec2-budget; BUDGET=29.47; rm -f runs/hyb4.hold; touch runs/ec2-g4-upgraded
      log "g4 boundary upgrade: funsearch/runs $(git rev-parse --short HEAD), $(tail -n 1 runs/ec2-pytest.txt); relaunching with --budget 29.47"
    else
      echo "g4 boundary upgrade failed (merge/aa032ba/build/tests); league left on hold" > "$D/HALT"; log "HALT: g4 upgrade failed"; return 1
    fi
  fi
fi
if ! running "league --name hyb4"; then
  if [ -f runs/ec2-launched ] && ls runs/hyb4-g*/STOP > /dev/null 2>&1; then
    log "league not running and a STOP file is present: leaving it paused"
  else
    [ -f runs/ec2-launched ] && log "league not running: relaunching (resume from runs/)"
    setsid nohup python3 -m funsearch.league --name hyb4 --threads 5 --budget "$BUDGET" \
      --members policies/v7-zerogem.policy,policies/v7.policy,policies/v5d-fs2.policy \
      --fixed policies/locker.policy --prefix fs-h --line hybrid --round 30 \
      --cambc-ref policies/tune-5.policy --workers 3 --eval-threads 2 >> runs/hyb4.out 2>&1 < /dev/null &
    touch runs/ec2-launched
    log "launched hyb4 league"
  fi
fi
# Resume check 1: the first new hyb4.log line must continue g3 (30 so far) or g4; g1 (0 so far) = fresh start -> stop.
if [ ! -f runs/ec2-resume-checked ]; then
  first=$(tail -n +"$(( $(cat runs/ec2-resume-mark) + 1 ))" runs/hyb4.log | grep -m1 -E 'hyb4-g[0-9]+: ')
  if [ -n "$first" ]; then
    if echo "$first" | grep -qE 'hyb4-g1: .*\(0 so far\)'; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb4' | cut -d' ' -f1); do kill -TERM "$pid"; done
      echo "fresh start detected: $first" > "$D/HALT"; log "FRESH START DETECTED, stopped: $first"
    else
      touch runs/ec2-resume-checked; log "resume check ok: $(echo "$first" | cut -c1-160)"
    fi
  fi
fi
push_state remote/hybrid remote/hybrid/runs runs
if ls policies/fs-h*.policy > /dev/null 2>&1; then   # promoted policies (none until a promotion)
  mkdir -p /root/bc/hybrid-pol && cp -a policies/fs-h*.policy /root/bc/hybrid-pol/ && push_state remote/hybrid policies /root/bc/hybrid-pol
fi
