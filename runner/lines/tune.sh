# tune line (jobs/tune/JOBS.md "EC2 resume", 2026-10-24 06:05 UTC): job C (t5_mapfix) then job D (draft_meta m1),
# both at nice 15 with the scripts' default 4 threads; job B is obsolete. Logs and cand-*.policy go to remote/tune.
D=/root/bc/tune
if [ ! -d "$D/.git" ]; then
  git clone -q --branch tune/runs "$REPO" "$D" || { log "clone failed"; return 1; }
  log "cloned tune/runs at $(git -C "$D" rev-parse --short HEAD)"
fi
build "$D" fuel_turns || { log "build failed: $(tail -n 3 "$D/interp/build/build.log")"; return 1; }
cd "$D" && mkdir -p runs/tune

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
for n in C D; do
  [ -f "runs/tune/$n.rc" ] && [ ! -f "runs/tune/$n.reported" ] && { log "job $n exited rc=$(cat runs/tune/$n.rc)"; touch "runs/tune/$n.reported"; }
done
push_state remote/tune remote/tune/runs/tune runs/tune
