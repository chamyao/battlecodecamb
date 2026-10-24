# tune line (jobs/tune/JOBS.md "EC2 resume", 2026-10-24 06:05 UTC): job C (t5_mapfix) then job D (draft_meta m1),
# both at nice 15 with the scripts' default 4 threads; job B is obsolete. Logs and cand-*.policy go to remote/tune.
D=/root/bc/tune
if [ ! -d "$D/.git" ]; then
  git clone -q --branch tune/runs "$REPO" "$D" || { log "clone failed"; return 1; }
  log "cloned tune/runs at $(git -C "$D" rev-parse --short HEAD)"
fi
build "$D" fuel_turns || { log "build failed: $(tail -n 3 "$D/interp/build/build.log")"; return 1; }
cd "$D" && mkdir -p runs/tune
# 06:45 UTC: follow tune/runs (job D2 needs 28b47e7+: draft_meta base argument, policies/tune5-reset.policy)
git pull -q --ff-only origin tune/runs 2>/dev/null || log "pull failed"

# job <name> <match> <command...>: start once; <name>.rc is written when it exits
job() {
  local n=$1 m=$2; shift 2
  [ -f "runs/tune/$n.rc" ] && return 0
  running "$m" && return 0
  [ -f "runs/tune/$n.started" ] && log "job $n died without an exit code; restarting"
  date -u +%FT%TZ > "runs/tune/$n.started"
  setsid nohup sh -c "nice -n 15 $* ; echo \$? > runs/tune/$n.rc" < /dev/null > /dev/null 2>&1 &
  log "started job $n: $*"
}
job C funsearch/t5_mapfix.py "python3 funsearch/t5_mapfix.py > runs/tune/t5mapfix.out 2>&1"
# D alongside C while the box is otherwise idle (JOBS.md: "after C or alongside it if threads allow")
job D "funsearch/draft_meta.py m1" "python3 funsearch/draft_meta.py m1 9411 > runs/tune/draftmeta.out 2>&1"
# D2 (06:45 UTC): job D's draft screen rebased on tune5-reset (the likely next live bot); D on tune-5 is superseded
[ -f runs/tune/D.rc ] || [ -f runs/tune/D.killed ] || { pkill -f "funsearch/draft_meta.py m1 " ; echo superseded > runs/tune/D.rc; touch runs/tune/D.killed; log "stopped job D (superseded by D2)"; }
job D2 "funsearch/draft_meta.py r1" "python3 funsearch/draft_meta.py r1 9431 policies/tune5-reset.policy > runs/tune/draftmeta-r1.out 2>&1"
# E, F (06:55 UTC): exploration on tune5-campreset (funsearch/explore.py, tune/runs 1e+ with explore.py)
job E "funsearch/explore.py drafts" "python3 funsearch/explore.py drafts 9471 400 > runs/tune/explore-drafts.out 2>&1"
job F "funsearch/explore.py switches" "python3 funsearch/explore.py switches > runs/tune/explore-switches.out 2>&1"
for n in C D D2 E F; do
  [ -f "runs/tune/$n.rc" ] && [ ! -f "runs/tune/$n.reported" ] && { log "job $n exited rc=$(cat runs/tune/$n.rc)"; touch "runs/tune/$n.reported"; }
done
push_state remote/tune remote/tune/runs/tune runs/tune

# G (08:30 UTC, FunSearch lead approved $5): fight-block FunSearch seeded from tune-v18g, branch tune/fs
# (funsearch/style 3d34e37 + directive funsearch/styles/t_fight.txt + runs/tune_fs_launch.sh). Own clone, own build.
G=/root/bc/tune-fs
GREV=6cba5f0  # 08:35 UTC: seed tune-v18g (retreat-dash fuel gate), fuel rule in the directive
if [ ! -f "$G/.setup-$GREV" ]; then
  # a run started on an older rev is stopped and restarted from scratch on the new one
  for pid in $(pgrep -a -x python3 | grep -E "league --name tune-fight |funsearch.run --run tune-fight-" | cut -d' ' -f1); do
    kill -TERM "$pid" && log "G: stopped old tune-fight pid $pid (rev change)"; done
  clone_nopush "$GREV" "$G" || { log "G: clone failed"; return 1; }
  build "$G" || { log "G: build failed: $(tail -n 3 "$G/interp/build/build.log")"; return 1; }
  touch "$G/.setup-$GREV"; log "G: tune/fs set up at $GREV"
fi
(
  cd "$G" || exit 0
  [ -f runs/tune-fight.done ] && exit 0
  running "league --name tune-fight " && exit 0
  if [ -f runs/tune-fight.launched ] && tail -n 1 runs/tune-fight.log 2>/dev/null | grep -q 'budget spent'; then
    touch runs/tune-fight.done; log "G: tune-fight exited: $(tail -n 1 runs/tune-fight.log)"; exit 0
  fi
  [ -f runs/tune-fight.launched ] && log "G: tune-fight not running: relaunching (resumes)"
  WORKERS=2 EVAL_THREADS=2 VAL_THREADS=3 setsid nohup sh runs/tune_fs_launch.sh 5 >> runs/tune-fight.out 2>&1 < /dev/null &
  touch runs/tune-fight.launched; log "G: launched tune-fight (\$5)"
)
# state: the league log/json, each generation's programs/proposals and any promoted policies
rm -rf /root/bc/tune-fs-snap && mkdir -p /root/bc/tune-fs-snap
cp -a "$G"/runs/tune-fight* /root/bc/tune-fs-snap/ 2>/dev/null
cp -a "$G"/policies/tune-fight-*.policy /root/bc/tune-fs-snap/ 2>/dev/null
push_state remote/tune remote/tune/fs /root/bc/tune-fs-snap
