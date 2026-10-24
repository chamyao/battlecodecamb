# pure line: resume pure4 (jobs/pure/JOBS.md "EC2 resume", c8cb1f0). g3 finishes on 81ab84b (old prompt)
# with --max-generations 3 --no-commit; after its promotion, g4+ runs from the tip of funsearch/pure.
# State in: remote/pure remote/pure/runs/ (04:15 UTC snapshot; Cham confirmed no newer state).
# runs/ is TRACKED on funsearch/pure: every checkout here saves and restores runs/ around it.
D=/root/bc/pure
SESSION=https://claude.ai/code/session_01Rbeaeb1EjHHutSParz5EPd
# g4 runs from this vetted funsearch/pure commit, not the moving tip (set by the pure line session only).
# 2b65f8d: coord/blocks 7db639b + deploy/v0 7ef15b2 merged (rebuild); prompt = funsearch/runs aa032ba catalog; fixed rall2-ca4-lean-g (live v19), v5d, v4, locker, fs-2, opp-hunter3; budget 15.15.
G4_REV=2b65f8d
[ -f "$D/HALT" ] && { log "halted: $(cat "$D/HALT")"; return 0; }
p1() {   # P1 contents (JOBS.md section 2)
  printf 'policies/tune-5.policy\npolicies/v5d.policy\npolicies/v4.policy\npolicies/locker.policy\npolicies/fs-2.policy\n' > runs/pure_fixed.txt
  echo policies/tune-5.policy > runs/pure_send.txt
}
halt() {
  for pid in $(pgrep -a -x python3 | grep -F 'league --name pure4' | cut -d' ' -f1); do kill -TERM "$pid"; done
  echo "$*" > "$D/HALT"; log "HALT: $*"
}
if [ ! -f "$D/.setup-done" ]; then
  clone_nopush 81ab84b "$D" || { log "clone failed"; return 1; }
  cd "$D" && build "$D" || { log "build failed: $(tail -n 3 interp/build/build.log)"; return 1; }
  python3 -m pytest -q tests > /root/bc/pure-pytest.txt 2>&1 || { log "pytest failed: $(tail -n 2 /root/bc/pure-pytest.txt)"; return 1; }
  chk=$(python3 -c "from pathlib import Path; from funsearch.league import cambc_check; print(cambc_check(Path('policies/fs-p2.policy').read_text(), 'policies/tune-3.policy', 16))")
  [ "$chk" = "0.3625" ] || { halt "bit-identity check printed $chk, expected 0.3625"; return 1; }
  git fetch -q origin remote/pure && git archive origin/remote/pure remote/pure/runs | tar -x --strip-components=2 -C . ||
    { log "state overlay failed"; return 1; }
  for d in pure4-g1 pure4-g2 pure4-g3 pure4-g2-b pure4-g3-oldbuild; do [ -d runs/$d ] || { halt "runs/$d missing after overlay"; return 1; }; done
  p1
  python3 - <<'EOF' || { halt "runs/pure4.json is not the expected g3 state: $(cat runs/pure4.json)"; return 1; }
import json; s = json.load(open("runs/pure4.json"))
assert s["gen"] == 3 and s["members"] == ["policies/fs-p2.policy"] and s["target"] >= 151, s
EOF
  N=$(wc -l < runs/pure4-g3/programs.jsonl)
  S=$(python3 -c "from funsearch.league import spent; print(round(spent('pure4'), 2))")
  wc -l < runs/pure4.log > runs/ec2-resume-mark
  echo g3 > runs/ec2-phase
  touch "$D/.setup-done"
  log "setup ok at 81ab84b: $(tail -n 1 /root/bc/pure-pytest.txt); cambc 0.3625 ok; g3 programs.jsonl $N lines; spent \$$S (left \$$(python3 -c "print(round(9.71-$S,2))"))"
fi
cd "$D" || return 1
phase=$(cat runs/ec2-phase)
mark=$(cat runs/ec2-resume-mark)
newlog() { tail -n +"$((mark + 1))" runs/pure4.log; }
# One-shot g3 -> g4 WITHOUT a promotion (pure line, 2026-10-24): g3's 151-program round did not promote (best h2h
# 0.529 < 0.55) and the league extended g3 on the old prompt and opponents. Stop it, move the state to gen 4 with
# fs-p2 still the best, and run g4 from G4_REV. Runs once (runs/ec2-advanced).
ADVANCE_G3=1
if [ "$ADVANCE_G3" = 1 ] && [ "$phase" = g3 ] && [ ! -f runs/ec2-advanced ]; then
  if running "league --name pure4"; then
    [ -f runs/pure4-g3/STOP ] || { touch runs/pure4-g3/STOP; log "g3 advance: STOP requested, waiting for the league to exit"; }
    push_state remote/pure remote/pure/runs runs; return 0
  fi
  python3 - <<'EOF2' || { halt "g3 advance: runs/pure4.json is not at gen 3: $(cat runs/pure4.json)"; return 1; }
import json
s = json.load(open("runs/pure4.json"))
assert s["gen"] == 3, s
json.dump({"gen": 4, "members": s["members"]}, open("runs/pure4.json", "w"))
EOF2
  rm -f runs/pure4-g3/STOP
  rm -rf /root/bc/pure-runs-save && cp -a runs /root/bc/pure-runs-save &&
    git fetch -q origin funsearch/pure && git checkout -q -f "$G4_REV" &&
    rm -rf runs && cp -a /root/bc/pure-runs-save runs &&
    git checkout -q "$G4_REV" -- runs/pure_launch.sh runs/pure_fixed.txt runs/pure_send.txt ||
    { halt "g3 advance: g4 checkout failed"; return 1; }
  build "$D" || { log "g4 build failed"; return 1; }
  echo g4 > runs/ec2-phase; wc -l < runs/pure4.log > runs/ec2-resume-mark; rm -f runs/ec2-resume-checked
  touch runs/ec2-advanced
  phase=g4; mark=$(cat runs/ec2-resume-mark)
  log "g3 ended without promotion (best stays fs-p2); moved to funsearch/pure $(git rev-parse --short HEAD) for g4"
fi
# One-shot (pure line, 11:40 UTC): live v20 tune-fight-2s for g5. g4's fixed opponents are frozen in pure4.json,
# so updating pure_fixed.txt now only affects g5; pure_send.txt adds a logged cambc-exact vs v20 at g4's check.
V20_REV=13f4e52
if [ "$phase" = g4 ] && [ ! -f runs/ec2-v20 ]; then
  git fetch -q origin funsearch/pure &&
    git checkout -q "$V20_REV" -- policies/tune-fight-2s.policy runs/pure_fixed.txt runs/pure_send.txt &&
    touch runs/ec2-v20 && log "pure: v20 opponent files from $V20_REV (fixed from g5): $(tr '\n' ' ' < runs/pure_fixed.txt)" ||
    log "pure: v20 opponent file sync failed"
fi
# One-shot (pure line, 12:50 UTC): live v21 tune-v20-L1c from g6 (g5 started 12:36 with v20 frozen in pure4.json).
V21_REV=0fcb030
if [ "$phase" = g4 ] && [ -f runs/ec2-v20 ] && [ ! -f runs/ec2-v21 ]; then
  git fetch -q origin funsearch/pure &&
    git checkout -q "$V21_REV" -- policies/tune-v20-L1c.policy policies/fs-p3.policy runs/pure_fixed.txt runs/pure_send.txt &&
    touch runs/ec2-v21 && log "pure: v21 opponent files from $V21_REV (fixed from g6): $(tr '\n' ' ' < runs/pure_fixed.txt)" ||
    log "pure: v21 opponent file sync failed"
fi
# One-shot build switch, now applied to the running g5 (pure line, 12:55 / 13:05 UTC): G6_REV merges deploy/v0 dc15600 (tune lockfix b9452ee:
# locked_altars() = enemy locks only; v21 depends on it). When pure4.json reaches gen 6 the league has already started
# g6 on the old build: stop it, move that partial g6 dir aside (still counted by spent()), drop "target" (keep the
# frozen "fixed"), check out G6_REV keeping runs/, rebuild, relaunch g6 from scratch.
G6_REV=0af36c4
if [ "$phase" = g4 ] && [ ! -f runs/ec2-g6build ]; then
  gen=$(python3 -c "import json; print(json.load(open('runs/pure4.json'))['gen'])")
  if [ "$gen" -ge 5 ]; then   # moved up to g5 (13:05 UTC): every pool policy uses locked_altars
    if running "league --name pure4"; then
      [ -f "runs/pure4-g$gen/STOP" ] || { mkdir -p "runs/pure4-g$gen"; touch "runs/pure4-g$gen/STOP"; log "g6 build switch: STOP requested (gen $gen)"; }
      push_state remote/pure remote/pure/runs runs; return 0
    fi
    rm -f "runs/pure4-g$gen/STOP"
    [ -d "runs/pure4-g$gen" ] && mv "runs/pure4-g$gen" "runs/pure4-g$gen-oldbuild"
    [ -f "runs/pure4-g$gen.log" ] && mv "runs/pure4-g$gen.log" "runs/pure4-g$gen-oldbuild.log"
    python3 - <<'EOF2' || { halt "g6 build switch: pure4.json edit failed"; return 1; }
import json
s = json.load(open("runs/pure4.json"))
s.pop("target", None)
s.pop("fixed", None)   # re-read runs/pure_fixed.txt (v21 list) for the restarted generation
json.dump(s, open("runs/pure4.json", "w"))
EOF2
    rm -rf /root/bc/pure-runs-save && cp -a runs /root/bc/pure-runs-save &&
      git fetch -q origin funsearch/pure && git checkout -q -f "$G6_REV" &&
      rm -rf runs && cp -a /root/bc/pure-runs-save runs &&
      git checkout -q "$G6_REV" -- runs/pure_launch.sh ||
      { halt "g6 build switch: checkout failed"; return 1; }
    build "$D" || { log "g6 build failed"; return 1; }
    wc -l < runs/pure4.log > runs/ec2-resume-mark; rm -f runs/ec2-resume-checked
    touch runs/ec2-g6build; mark=$(cat runs/ec2-resume-mark)
    log "g6 build switch: moved to funsearch/pure $(git rev-parse --short HEAD) (lockfix); g6 restarts on the new build"
  fi
fi
# One-shot (pure line, 14:30 UTC, asked by Cham): restart the league on TUNE_REV (gap blocks batch 1, per-child hill-climb, helpers-pure,
# league tuning stage). The current generation RESUMES from runs/ (no state edits); only in-flight programs are lost.
TUNE_REV=b0c0651
if [ "$phase" = g4 ] && [ -f runs/ec2-g6build ] && [ ! -f runs/ec2-tune ]; then
  gen=$(python3 -c "import json; print(json.load(open('runs/pure4.json'))['gen'])")
  if running "league --name pure4"; then
    [ -f "runs/pure4-g$gen/STOP" ] || { touch "runs/pure4-g$gen/STOP"; log "tune restart: STOP requested (gen $gen)"; }
    push_state remote/pure remote/pure/runs runs; return 0
  fi
  rm -f "runs/pure4-g$gen/STOP"
  rm -rf /root/bc/pure-runs-save && cp -a runs /root/bc/pure-runs-save &&
    git fetch -q origin funsearch/pure && git checkout -q -f "$TUNE_REV" &&
    rm -rf runs && cp -a /root/bc/pure-runs-save runs &&
    git checkout -q "$TUNE_REV" -- runs/pure_launch.sh ||
    { halt "tune restart: checkout failed"; return 1; }
  build "$D" || { log "tune restart build failed"; return 1; }
  wc -l < runs/pure4.log > runs/ec2-resume-mark; rm -f runs/ec2-resume-checked
  touch runs/ec2-tune; mark=$(cat runs/ec2-resume-mark)
  log "tune restart: moved to funsearch/pure $(git rev-parse --short HEAD); gen $gen resumes"
fi
if ! running "league --name pure4"; then
  if [ "$phase" = g3 ] && [ -f runs/ec2-launched ] && newlog | grep -q 'PROMOTED fs-p3' &&
     python3 -c "import json,sys; sys.exit(json.load(open('runs/pure4.json'))['gen'] != 4)"; then
    # g3 -> g4 (JOBS.md section 5): push fs-p3 to funsearch/pure, move to the tip keeping runs/, relaunch.
    prom=$(newlog | grep -m1 'PROMOTED fs-p3')
    mkdir -p /root/bc/pure-pol && cp policies/fs-p3.policy /root/bc/pure-pol/ &&
      push_state funsearch/pure policies /root/bc/pure-pol "policies/fs-p3: pure4 g3 promotion (EC2 runner)

$prom" || { log "fs-p3 push failed"; return 1; }
    rm -rf /root/bc/pure-runs-save && cp -a runs /root/bc/pure-runs-save &&
      git fetch -q origin funsearch/pure && git checkout -q -f "$G4_REV" &&
      rm -rf runs && cp -a /root/bc/pure-runs-save runs && cp /root/bc/pure-pol/fs-p3.policy policies/ &&
      git checkout -q "$G4_REV" -- runs/pure_launch.sh runs/pure_fixed.txt runs/pure_send.txt ||
      { halt "g4 checkout failed"; return 1; }
    # g4 opponents come from G4_REV (fixed tune5-campreset instead of tune-5); do not rewrite them with p1 here.
    build "$D" || { log "g4 build failed"; return 1; }
    echo g4 > runs/ec2-phase; wc -l < runs/pure4.log > runs/ec2-resume-mark; rm -f runs/ec2-resume-checked
    phase=g4; mark=$(cat runs/ec2-resume-mark)
    log "g3 promoted ($prom); moved to funsearch/pure $(git rev-parse --short HEAD) for g4"
  elif [ -f runs/ec2-launched ] && newlog | tail -n 1 | grep -q 'budget spent'; then
    [ -f runs/ec2-budget-reported ] || { log "league exited: $(newlog | tail -n 1)"; touch runs/ec2-budget-reported; }
    push_state remote/pure remote/pure/runs runs; return 0
  elif [ -f runs/ec2-launched ] && ls runs/pure4-g*/STOP > /dev/null 2>&1; then
    log "league not running and a STOP file is present: leaving it paused"; push_state remote/pure remote/pure/runs runs; return 0
  elif [ "$phase" = g3 ] && [ -f runs/ec2-launched ] && newlog | grep -q 'PROMOTED fs-p3'; then
    log "g3 promoted but the league is gone before gen 4 was written; waiting"; return 0
  fi
  [ -f runs/ec2-launched ] && log "league not running: relaunching ($phase, resume from runs/)"
  if [ "$phase" = g3 ]; then
    setsid nohup python3 -m funsearch.league --name pure4 --budget 9.71 \
      --members policies/fs-1.policy --keep 0 --fixed @runs/pure_fixed.txt --cambc-also @runs/pure_send.txt \
      --policy-prefix fs-p --line pure --session "$SESSION" \
      --workers 3 --eval-threads 2 --threads 5 --max-generations 3 --no-commit >> runs/pure.out 2>&1 < /dev/null &
  else
    setsid nohup sh runs/pure_launch.sh >> runs/pure.out 2>&1 < /dev/null &
  fi
  touch runs/ec2-launched
  log "launched pure4 league ($phase)"
fi
# Resume check: the first new pure4.log line must be pure4-g3 (to 151) and not +150/+151 (g3), or pure4-g4 (g4).
if [ ! -f runs/ec2-resume-checked ]; then
  first=$(newlog | grep -m1 -E 'pure4-g[0-9]+: ')
  if [ -n "$first" ]; then
    if [ "$phase" = g3 ] && { ! echo "$first" | grep -q 'pure4-g3: ' || echo "$first" | grep -qE '\+15[01] programs'; }; then
      halt "restart detected instead of a resume: $first"
    elif [ "$phase" = g4 ] && { ! echo "$first" | grep -qE 'pure4-g[4-9][0-9]*: ' || ! echo "$first" | grep -qF "$(head -n 1 runs/pure_fixed.txt)"; }; then
      halt "g4 did not start as expected: $first"
    else
      touch runs/ec2-resume-checked; log "resume check ok: $(echo "$first" | cut -c1-160)"
    fi
  fi
fi
push_state remote/pure remote/pure/runs runs
if ls policies/fs-p*.policy > /dev/null 2>&1; then   # promoted policies (none until a promotion)
  mkdir -p /root/bc/pure-pol && cp -a policies/fs-p*.policy /root/bc/pure-pol/ && push_state remote/pure policies /root/bc/pure-pol
fi
