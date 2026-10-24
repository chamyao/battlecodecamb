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
if ! running "league --name hyb4"; then
  if [ -f runs/ec2-launched ] && ls runs/hyb4-g*/STOP > /dev/null 2>&1; then
    log "league not running and a STOP file is present: leaving it paused"
  else
    [ -f runs/ec2-launched ] && log "league not running: relaunching (resume from runs/)"
    setsid nohup python3 -m funsearch.league --name hyb4 --threads 5 --budget 9.82 \
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
