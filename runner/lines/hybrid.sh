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
  # H6 + H7 (hybrid line, 12:15 / 12:40 / 12:47 UTC), one relaunch at the same hyb5 boundary: merge funsearch/runs c4341a3+ (deploy/v0 lockfix d9d2897 + recalibrated fuel: interp changes, build() rebuilds;
  # (includes 48a1404: lock-flag bits in shared memory; and policies/pool/v21.policy; no interp change), queue v21 as a
  # challenger, relaunch with v21 seeds on islands 0/1/3 and --cambc-ref v21.
  V21SEEDS=policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/lean-g65.policy,policies/pool/v21.policy
  [ -f runs/ec2-h6 ] && { SEEDS=$V21SEEDS; CREF=policies/pool/v21.policy; }
  if [ -f runs/ec2-h5 ] && [ ! -f runs/ec2-h6 ]; then
    if [ ! -f runs/ec2-h6-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h6-holdmark; touch runs/hyb5.hold runs/ec2-h6-hold
      log "H6: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h6-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H6: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor c4341a3 HEAD && [ -f policies/pool/v21.policy ] && build "$D" &&
         python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        grep -qx policies/pool/v21.policy runs/hyb5.challengers 2>/dev/null || echo policies/pool/v21.policy >> runs/hyb5.challengers
        for f in runs/hyb5-g*.log; do echo "$f $(wc -l < "$f")"; done > runs/ec2-h6-marks
        rm -f runs/hyb5.hold; touch runs/ec2-h6; SEEDS=$V21SEEDS; CREF=policies/pool/v21.policy
        log "H6+H7: funsearch/runs $(git rev-parse --short HEAD) (has c4341a3: deploy/v0 lockfix + fuel recalibration; rebuilt), $(tail -n 1 runs/ec2-pytest.txt); v21 challenger queued; relaunching on v21"
      else
        echo "H6+H7 merge/c4341a3/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H6 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # H7b (12:50 UTC): H6+H7 had already relaunched on a43aede (no lockfix) when the c4341a3 requirement arrived, so
  # v21 / lock policies were being mis-evaluated. Restart now (no boundary wait): SIGTERM, merge c4341a3+, rebuild,
  # pytest, relaunch with the same (v21) flags; hyb5 resumes mid-round from programs.jsonl.
  if [ -f runs/ec2-h6 ] && [ ! -f runs/ec2-h7b ]; then
    for pid in $(pgrep -a -x python3 | grep -E "league --name hyb5|funsearch.run --run hyb5-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "H7b: SIGTERM hyb5 pid $pid"; done
    sleep 15
    if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
       git merge-base --is-ancestor c4341a3 HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
      wc -l < runs/hyb5.log > runs/ec2-h7b-mark; touch runs/ec2-h7b
      log "H7b: funsearch/runs $(git rev-parse --short HEAD) (has c4341a3: lockfix + fuel recalibration), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 (same v21 flags)"
    else
      echo "H7b merge/c4341a3/build/tests failed; hyb5 stopped" > "$D/HALT"; log "HALT: H7b upgrade failed"; pushall; return 1
    fi
  fi
  # H7c (12:58 UTC, hybrid line): the g2 boundary validation that ran on the stale a43aede build (12:43:24-12:48:58)
  # appended 21 entries to runs/validation_cache.jsonl (lines 807-827 of remote/hybrid c6840e8). Stop hyb5, drop those
  # keys, relaunch so the boundary is re-validated on the lockfix build only. Entries after H7b are kept.
  if [ -f runs/ec2-h7b ] && [ ! -f runs/ec2-h7c ]; then
    for pid in $(pgrep -a -x python3 | grep -E "league --name hyb5|funsearch.run --run hyb5-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "H7c: SIGTERM hyb5 pid $pid"; done
    sleep 15
    cp runs/validation_cache.jsonl runs/validation_cache.jsonl.pre-h7c
    STALE="b7081cf2f78b3dae118903b5e0c4885bc2ee9928d2d986a119fb22d19daff992 771205884b94b9ef633e363651444cfe84678ea6df63a4a3575ddd8966a02081 f8e3e9dadf9894695acee461d092ca384fb782c8cb733f13dc960a2226d8eb7c 83a35d5392a2a2865ca601e5f6626edb2463b72607b05d96137254563065861d 5dd8a7bdb39abe13c6c26a749247ac52c4054fd5cc9b07948a920795bb79fe19 d33075bd666f5105b822eb391cde401cd744ae788894b235f3a452cc85a0de18 0531858814c68be9fab74a798070715a5961191cbd35948c3408a804932a6781 8d4b6ead169a6e93f04309d788de61155b30bdcfcdf537f7256085e9866f3fe6 4781fa0fac6c9adc079e9cafd3d899cfbed07c770623c1cd132ea45cc2992cf8 e87e58f489a2d742d9436874413af9a950e4a97db0ac62b4b4c965351d4deb7b 41c9a25e1bd6b82d02ecc5dd2d4f58dd5498753ec132f933e55536132f2bc748 82d95d3e69051dac4009e69920967e8f5903a6dba7bff8e024dbba043b2e1382 527836d9dd1d1ebd524db7b0b564d32a66b65ea1a4795bea716f0a7f65292e44 ad5a03fed51066d5307090947d050b6e7ee71728269e7d6d48d021ec18adba70 81a6f8309bb4344111d3d7ed3d6b7610c6bd4a78cda05b46cddab8656e020e73 2062287d710fe4c28b6619019993cfbdad89e37bc44488bf1aa073acc1ebc571 256b258fe63dfd1487eaed80d99fe218e7aff1c070770959b8bea99f2298332c 3fef3e1602010edbf56165226c9aa2b38882a6922ec955d843b7763d6c77f1be d44df922a0bc0f3c6e9440d27ccf70f9e8e73f12db939c33cbe73df19e5ab09b 4fb5a0ebe8612f9d302720169766575c6ce8533e56e0b6abf837456e7a5ca5dc 26e49efcec7ab0f06900266d4d377a42639cbd258901834a570aa2c6dc228926" python3 - <<'PY'
import json, os
stale = set(os.environ["STALE"].split())
lines = open("runs/validation_cache.jsonl").read().splitlines(keepends=True)
keep = [l for l in lines if not l.strip() or json.loads(l).get("key") not in stale]
open("runs/validation_cache.jsonl", "w").writelines(keep)
print(len(lines) - len(keep))
PY
    n=$(( $(wc -l < runs/validation_cache.jsonl.pre-h7c) - $(wc -l < runs/validation_cache.jsonl) ))
    wc -l < runs/hyb5.log > runs/ec2-h7c-mark; touch runs/ec2-h7c
    log "H7c: removed $n stale-build validation cache entries (expected 21; backup validation_cache.jsonl.pre-h7c); relaunching hyb5"
  fi
  # H8 (jobs/hybrid, 13:36 UTC): at the next hyb5 boundary merge funsearch/runs f31c3a4+ (sim/ diagnostics-only line:
  # rebuild), pytest, relaunch with H7's command plus the disengage axis and seeds v21,v21,v20,v19-L1c.
  H8SEEDS=policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/v20.policy,policies/pool/v19-L1c.policy
  H8AXES="--axes items,vision,teleport,team,roles,pairs,macro,abilities,combat,disengage"
  # H8 addendum, revised (13:51 UTC): require fb401ce (child constant climb on by default in funsearch.run: steps 6,
  # games 16, slack 0.15, margin 0.03; comment-only children skipped) and NO --tune-* flags.
  H8TUNE=; TUNE=
  [ -f runs/ec2-h8 ] && { SEEDS=$H8SEEDS; AXES=$H8AXES; TUNE=$H8TUNE; }
  if [ -f runs/ec2-h7c ] && [ ! -f runs/ec2-h8 ]; then
    if [ ! -f runs/ec2-h8-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h8-holdmark; touch runs/hyb5.hold runs/ec2-h8-hold
      log "H8: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h8-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H8: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor f31c3a4 HEAD && git merge-base --is-ancestor fb401ce HEAD &&
         [ -f policies/pool/v19-L1c.policy ] && build "$D" &&
         python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        for f in runs/hyb5-g*.log; do echo "$f $(wc -l < "$f")"; done > runs/ec2-h8-marks
        rm -f runs/hyb5.hold; touch runs/ec2-h8; SEEDS=$H8SEEDS; AXES=$H8AXES; TUNE=$H8TUNE
        log "H8: funsearch/runs $(git rev-parse --short HEAD) (has f31c3a4, fb401ce), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 (disengage axis; seeds v21,v21,v20,v19-L1c; default child climb)"
      else
        echo "H8 merge/f31c3a4/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H8 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # H8b (13:55 UTC): H8 fired at 13:49-13:51 with the pre-revision flags (--tune-children --tune-steps 6 --tune-games 12)
  # on fb401ce. Restart once so hyb5 runs the revised command (no --tune-* flags: default climb, games 16).
  if [ -f runs/ec2-h8 ] && [ ! -f runs/ec2-h8b ] && pgrep -a -x python3 | grep -F 'league --name hyb5' | grep -q -- '--tune-children'; then
    for pid in $(pgrep -a -x python3 | grep -E "league --name hyb5|funsearch.run --run hyb5-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "H8b: SIGTERM hyb5 pid $pid (drop --tune-* flags)"; done
    sleep 15; touch runs/ec2-h8b
  fi
  # H9 (jobs/hybrid, 14:04 UTC): restart NOW mid-round: fb401ce's default climb replays ~4.7k games per child, breaking
  # the programs/hour cap. Merge c6eb17a+ (python only; cheaper defaults: games 8, steps 4, stop after 2 rejects) and
  # relaunch with the H8 command plus a reduced climb opponent set.
  H9TUNE="--tune-opponents builtin:starter@0.25,policies/pool/v21.policy@3,policies/pool/opp-hunter3.policy,policies/pool/opp-hunter2b.policy,policies/pool/opp-metadraft.policy"
  [ -f runs/ec2-h9 ] && TUNE=$H9TUNE
  if [ -f runs/ec2-h8 ] && [ ! -f runs/ec2-h9 ]; then
    for pid in $(pgrep -a -x python3 | grep -E "league --name hyb5|funsearch.run --run hyb5-" | cut -d' ' -f1); do
      kill -TERM "$pid" && log "H9: SIGTERM hyb5 pid $pid"; done
    sleep 15
    if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
       git merge-base --is-ancestor c6eb17a HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
      wc -l < runs/hyb5.log > runs/ec2-h9-mark; date +%s > runs/ec2-h9-time
      cat runs/hyb5-g*/programs.jsonl 2>/dev/null | wc -l > runs/ec2-h9-progs
      touch runs/ec2-h9; TUNE=$H9TUNE
      log "H9: funsearch/runs $(git rev-parse --short HEAD) (has c6eb17a), $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 with --tune-opponents (5)"
    else
      echo "H9 merge/c6eb17a/tests failed; hyb5 stopped" > "$D/HALT"; log "HALT: H9 upgrade failed"; pushall; return 1
    fi
  fi
  # H11-H14 (jobs/hybrid ... 965de08, 14:25-14:40 UTC) folded into H10: require d915b03 (contains 14df19b, e71632d,
  # bank_detour sensor); (contains fe36f47,
  # 1d748cf exec_blocks refresh, deploy/v0 f6a56b7 calibrated fuel) (gap-sensor batches 1+2, vocab
  # variant on by default, exec_blocks vs builtin:starter); same command line.
  # H10 (jobs/hybrid, 14:20 UTC): next hyb5 boundary after H9: merge funsearch/runs 4174c28+ (coord/capture-metric:
  # sim/ + policygen/blocks.py changed, new block unit_tributing: rebuild), pytest, relaunch with H9's command and the
  # weighted axis menu (conversion:3, disengage:2, the rest 1).
  H10AXES="--axes conversion:5,disengage:2,items:1,vision:1,teleport:1,team:1,roles:1,pairs:1,macro:1,abilities:1,combat:1"
  # H10 addendum (14:30 UTC): require 7a6038d (contains 4174c28) and add the shared helper library built from all three
  # FunSearch lines' runs/ on this box; the league rebuilds runs/hyb5.helpers.json + HELPERS.md at every boundary.
  H10HELP="--helpers-runs /root/bc/hybrid/runs,/root/bc/pure/runs,/root/bc/style/runs,/root/bc/tune-fs/runs"; HELP=
  [ -f runs/ec2-h10 ] && { AXES=$H10AXES; HELP=$H10HELP; }
  if [ -f runs/ec2-h9 ] && [ ! -f runs/ec2-h10 ]; then
    if [ ! -f runs/ec2-h10-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h10-holdmark; touch runs/hyb5.hold runs/ec2-h10-hold
      log "H10: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h10-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H10: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor 7a6038d HEAD && git merge-base --is-ancestor 6646329 HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        cat runs/hyb5-g*/programs.jsonl 2>/dev/null | wc -l > runs/ec2-h10-progs
        rm -f runs/hyb5.hold; touch runs/ec2-h10; AXES=$H10AXES; HELP=$H10HELP
        log "H10: funsearch/runs $(git rev-parse --short HEAD) (has 7a6038d, 6646329: H10-H15: gap sensors, vocab variant, exec_blocks refresh, calibrated fuel), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 with the weighted axis menu and --helpers-runs"
      else
        echo "H10 merge/4174c28/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H10 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # H16 (jobs/hybrid c20e5e6, 15:07 UTC): next hyb5 boundary after H10: merge funsearch/runs 8b38ce6+ (dead-camp fix,
  # the v22 build: sim/ + interp/ changed -> rebuild; validation cache invalidated by the rebuild), pytest, same flags.
  if [ -f runs/ec2-h10 ] && [ ! -f runs/ec2-h16 ]; then
    if [ ! -f runs/ec2-h16-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h16-holdmark; touch runs/hyb5.hold runs/ec2-h16-hold
      log "H16: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h16-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H16: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor 8b38ce6 HEAD && build "$D" && python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        rm -f runs/hyb5.hold; touch runs/ec2-h16
        log "H16: funsearch/runs $(git rev-parse --short HEAD) (has 8b38ce6: dead-camp fix / v22 build), rebuilt, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5, same flags"
      else
        echo "H16 merge/8b38ce6/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H16 upgrade failed"; pushall; return 1
      fi
    fi
  fi
  # H17 (jobs/hybrid 138bd65, 15:40 UTC, lead-approved): #82 fuel island at the next hyb5 boundary after H16: merge
  # funsearch/runs 27dd4a2+, build interp_eval + fuel_turns, pytest; island 3 seeded with #82, protected, fuel-scored,
  # with its own axis menu (the league passes these run args through).
  H17SEEDS=policies/pool/v21.policy,policies/pool/v21.policy,policies/pool/v20.policy,policies/candidates/hyb5-g3-82.policy
  # H18 (jobs/hybrid 8af15ba, lead-approved) folded in: capture-yield fitness on all islands, --yield-weight 0.25, fc797d0+
  H17EXTRA="--protect-islands 3 --fuel-islands 3 --island-axes 3=fuel:5,conversion:2,pairs:1,disengage:1 --yield-weight 0.25"; EXTRA=
  [ -f runs/ec2-h17 ] && { SEEDS=$H17SEEDS; EXTRA=$H17EXTRA; }
  if [ -f runs/ec2-h16 ] && [ ! -f runs/ec2-h17 ]; then
    if [ ! -f runs/ec2-h17-hold ]; then
      grep -c 'hold file present' runs/hyb5.log > runs/ec2-h17-holdmark; touch runs/hyb5.hold runs/ec2-h17-hold
      log "H17: hold set for the next hyb5 boundary"
    fi
    if [ "$(grep -c 'hold file present' runs/hyb5.log)" -gt "$(cat runs/ec2-h17-holdmark)" ]; then
      for pid in $(pgrep -a -x python3 | grep -F 'league --name hyb5' | cut -d' ' -f1); do kill -TERM "$pid" && log "H17: SIGTERM hyb5 pid $pid"; done
      sleep 10
      if git fetch -q origin funsearch/runs && git merge -q --no-edit origin/funsearch/runs &&
         git merge-base --is-ancestor 27dd4a2 HEAD && git merge-base --is-ancestor fc797d0 HEAD && [ -f policies/candidates/hyb5-g3-82.policy ] &&
         rm -f "$D/interp/build/.built-$(git rev-parse HEAD)" && build "$D" fuel_turns &&
         python3 -m pytest -q tests > runs/ec2-pytest.txt 2>&1; then
        for f in runs/hyb5-g*.log; do echo "$f $(wc -l < "$f")"; done > runs/ec2-h17-marks
        cat runs/hyb5-g*/programs.jsonl 2>/dev/null | wc -l > runs/ec2-h17-progs
        rm -f runs/hyb5.hold; touch runs/ec2-h17; SEEDS=$H17SEEDS; EXTRA=$H17EXTRA
        log "H17: funsearch/runs $(git rev-parse --short HEAD) (has 27dd4a2, fc797d0), built interp_eval+fuel_turns, $(tail -n 1 runs/ec2-pytest.txt); relaunching hyb5 with the #82 fuel island and --yield-weight 0.25"
      else
        echo "H17 merge/27dd4a2/build/tests failed; hyb5 stopped on hold" > "$D/HALT"; log "HALT: H17 upgrade failed"; pushall; return 1
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
        --island-seeds "$SEEDS" $AXES $TUNE $HELP $EXTRA \
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
  if [ -f runs/ec2-h6 ] && [ ! -f runs/ec2-h6-checked ]; then
    r=""; for f in runs/hyb5-g*.log; do
      m=$(awk -v f="$f" '$1==f{print $2}' runs/ec2-h6-marks); m=${m:-0}
      r="$r$(tail -n +"$((m + 1))" "$f" | grep -oE 're-seeded island [0-9] with [a-z0-9-]+' | tr '\n' ';')"
    done
    if [ -n "$r" ]; then touch runs/ec2-h6-checked; log "H7 check: $r (expected islands 0,1,3 with v21; island 2 kept)"
    elif grep -q 'PROMOTED challenger policies/pool/v21.policy' runs/hyb5.log; then
      touch runs/ec2-h6-checked; log "H7 check: no re-seed lines; v21 promoted at the boundary"; fi
  fi
  if [ -f runs/ec2-h7b ] && [ ! -f runs/ec2-h7b-checked ]; then
    f=$(tail -n +"$(( $(cat runs/ec2-h7b-mark) + 1 ))" runs/hyb5.log | grep -m1 'hyb5-g[0-9]*: ')
    [ -n "$f" ] && { touch runs/ec2-h7b-checked; log "H7b check: $(echo "$f" | grep -oE 'hyb5-g[0-9]+: \+[0-9]+ programs[^,]*') $(echo "$f" | grep -oE 'best [^,]*') $(echo "$f" | grep -oE '\$[0-9.]+ left')"; }
  fi
  if [ -f runs/ec2-h8 ] && [ ! -f runs/ec2-h8-checked ]; then
    r=""; for f in runs/hyb5-g*.log; do
      m=$(awk -v f="$f" '$1==f{print $2}' runs/ec2-h8-marks); m=${m:-0}
      r="$r$(tail -n +"$((m + 1))" "$f" | grep -oE 're-seeded island [0-9] with [a-z0-9-]+' | sed "s|^|$(basename "$f" .log): |" | tr '\n' ';')"
    done
    newl=$(grep -c 'hyb5-g[0-9]*: ' runs/hyb5.log)
    if [ -n "$r" ]; then touch runs/ec2-h8-checked; log "H8 check: $r (expected island 2 with v20, island 3 with v19-L1c; 0/1 keep v21)"
    elif [ -f runs/ec2-h8-wait ] && [ $(( $(date +%s) - $(cat runs/ec2-h8-wait) )) -gt 1800 ]; then
      touch runs/ec2-h8-checked; log "H8 check: no re-seed lines 30 min after relaunch; last: $(grep 'hyb5-g[0-9]*: ' runs/hyb5.log | tail -n 1 | cut -c1-120)"
    fi
    [ -f runs/ec2-h8-wait ] || date +%s > runs/ec2-h8-wait
  fi
  if [ -f runs/ec2-h9 ] && [ ! -f runs/ec2-h9-rate ]; then
    # first round boundary after H9: programs/hour over the round, and mean metrics.tuned.games of children since H9
    b=$(tail -n +"$(( $(cat runs/ec2-h9-mark) + 1 ))" runs/hyb5.log | grep -E 'hold file present|no promotion|PROMOTED' | head -n 1)
    if [ -n "$b" ]; then
      touch runs/ec2-h9-rate
      st=$(python3 - "$(cat runs/ec2-h9-time)" "$(cat runs/ec2-h9-progs)" <<'PY'
import json, glob, sys, time
t0, n0 = float(sys.argv[1]), int(sys.argv[2])
rows = []
for f in sorted(glob.glob("runs/hyb5-g*/programs.jsonl")):
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass
new = rows[n0:]
tg = [r.get("metrics", {}).get("tuned", {}).get("games") for r in new]
tg = [g for g in tg if isinstance(g, (int, float))]
hrs = (time.time() - t0) / 3600
print(f"{len(new)} programs in {hrs*60:.0f} min = {len(new)/hrs:.0f}/h; tuned children {len(tg)}, mean tuned.games {sum(tg)/len(tg) if tg else 0:.0f}")
PY
)
      log "H9 rate: $st (round ended: $(echo "$b" | cut -c1-60)); before: g2 58/h, g3 49/h"
    fi
  fi
  if [ -f runs/ec2-h10 ] && [ ! -f runs/ec2-h10-checked ]; then
    st=$(python3 - "$(cat runs/ec2-h10-progs)" <<'PY'
import json, glob, sys, collections
n0 = int(sys.argv[1]); rows = []
for f in sorted(glob.glob("runs/hyb5-g*/programs.jsonl")):
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass
new = rows[n0:]
if len(new) >= 28:
    c = collections.Counter()
    for r in new:
        v = ((r.get("metrics") or {}).get("variant") or {})
        ax = v.get("axis")
        if ax in ("conversion", "disengage"): c[ax] += 1
        if v.get("vocab"): c["vocab"] += 1
    print(f"{len(new)} new programs: conversion {c['conversion']} ({c['conversion']/len(new):.2f}, expect 0.31), disengage {c['disengage']} ({c['disengage']/len(new):.2f}, expect 0.12), vocab {c['vocab']} ({c['vocab']/len(new):.2f}, expect ~0.2)")
PY
)
    [ -n "$st" ] && { touch runs/ec2-h10-checked; log "H10 check: $st"; }
  fi
  if [ -f runs/ec2-h10 ] && [ ! -f runs/ec2-h10-exec ]; then
    eb=$(grep -ho 'exec_blocks vs starter for [0-9]* programs[^)]*)' runs/hyb5*.log runs/hyb5.out 2>/dev/null | tail -n 1)
    [ -n "$eb" ] && { touch runs/ec2-h10-exec; log "H10 startup check: '$eb'"; }
  fi
  # H15 (jobs/hybrid 8e627ee, lead-approved): conversion weight 5 (folded into H10). Watch explore.txt for "FLAG yield".
  if [ -f runs/ec2-h10 ]; then
    fy=$(grep -h 'FLAG yield' runs/hyb5*.explore.txt 2>/dev/null | wc -l)
    if [ "$fy" -gt "$(cat runs/ec2-flagyield 2>/dev/null || echo 0)" ]; then
      echo "$fy" > runs/ec2-flagyield
      log "H15 ALERT: 'FLAG yield' in explore.txt: $(grep -h 'FLAG yield' runs/hyb5*.explore.txt | tail -n 1 | cut -c1-200)"
    fi
  fi
  if [ -f runs/ec2-h10 ] && [ ! -f runs/ec2-h10-helpers ]; then
    hk=$(tail -n +"$(( $(cat runs/ec2-h10-progs 2>/dev/null || echo 0) * 0 + 1 ))" runs/hyb5.log | grep -o 'helpers: [0-9]* helpers kept' | tail -n 1)
    lh=$(cat runs/hyb5-g*/programs.jsonl 2>/dev/null | tail -n +"$(( $(cat runs/ec2-h10-progs) + 1 ))" | grep -c 'lib_helpers')
    [ -n "$hk" ] && [ "$lh" -gt 0 ] && { touch runs/ec2-h10-helpers; log "H10 helpers check: '$hk'; $lh new children carry metrics.lib_helpers; HELPERS.md $( [ -f runs/hyb5.HELPERS.md ] && echo present || echo MISSING)"; }
  fi
  if [ -f runs/ec2-h17 ] && [ ! -f runs/ec2-h18-checked ]; then
    yt=$(grep -ho 'yield term: [0-9]* logged programs rescaled' runs/hyb5*.log runs/hyb5.out 2>/dev/null | tail -n 1)
    ny=$(cat runs/hyb5-g*/programs.jsonl 2>/dev/null | tail -n +"$(( $(cat runs/ec2-h17-progs) + 1 ))" | grep -c '"yield"')
    [ -n "$yt" ] && [ "$ny" -gt 0 ] && { touch runs/ec2-h18-checked; log "H18 check: '$yt'; $ny new children carry metrics.yield"; }
  fi
  if [ -f runs/ec2-h17 ] && [ ! -f runs/ec2-h17-checked ]; then
    r=""; for f in runs/hyb5-g*.log; do
      m=$(awk -v f="$f" '$1==f{print $2}' runs/ec2-h17-marks); m=${m:-0}
      r="$r$(tail -n +"$((m + 1))" "$f" | grep -E 're-seeded island 3' | cut -c1-120 | tr '\n' ';')"
    done
    st=$(python3 - "$(cat runs/ec2-h17-progs)" <<'PY'
import json, glob, sys
n0 = int(sys.argv[1]); rows = []
for f in sorted(glob.glob("runs/hyb5-g*/programs.jsonl")):
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass
i3 = [r for r in rows[n0:] if r.get("island") == 3]   # top-level "island" field (no metrics.island)
if len(i3) >= 8:
    fuel = sum(1 for r in i3 if (r.get("metrics") or {}).get("fuel") is not None)
    fax = sum(1 for r in i3 if ((r.get("metrics") or {}).get("variant") or {}).get("axis") == "fuel")
    print(f"island-3 children {len(i3)}: metrics.fuel {fuel}, fuel axis {fax} ({fax/len(i3):.2f}, expect ~0.5)")
PY
)
    [ -n "$r" ] && [ -n "$st" ] && { touch runs/ec2-h17-checked; log "H17 check: $r $st"; }
  fi
  if [ -f runs/ec2-h8 ] && [ ! -f runs/ec2-h8-tuned ]; then
    t=$(cat runs/hyb5-g*/programs.jsonl 2>/dev/null | grep -c '"tuned"')
    [ "$t" -gt 0 ] && { touch runs/ec2-h8-tuned; log "H8 tune check: $t programs carry metrics.tuned"; }
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
