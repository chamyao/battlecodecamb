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
for n in C D D2; do
  [ -f "runs/tune/$n.rc" ] && [ ! -f "runs/tune/$n.reported" ] && { log "job $n exited rc=$(cat runs/tune/$n.rc)"; touch "runs/tune/$n.reported"; }
done
push_state remote/tune remote/tune/runs/tune runs/tune
