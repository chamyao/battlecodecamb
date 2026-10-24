# genome line (Cham, Oct 24 2026: the box is free for the genome team; docs/GENOME.md on genome/v0).
# A job queue: every job is a script `<name>.sh` on branch jobs/genome. Its first line names the commit
# to run on: `# rev: <sha or branch>`. The runner checks that out into /root/bc/genome/w/<name>, builds
# genome_eval there, runs the script once (cwd = that checkout, $OUT = its output dir, $THREADS =
# threads it may use, FUNSEARCH_API_KEY in the environment) and pushes $OUT to remote/genome under
# <name>/ when it exits (and every tick while it runs). At most $MAXJOBS jobs at once.
G=/root/bc/genome
MAXJOBS=4; export THREADS=5  # 4 slots: a job waiting on another (e.g. a resume) only sleeps
mkdir -p "$G/out" "$G/w"
# (19:27 UTC pause removed 19:31: Cham confirmed the pause did not include the genome line.)
if [ ! -d "$G/jobs/.git" ]; then
  git clone -q --single-branch --branch jobs/genome "$REPO" "$G/jobs" || { log "clone jobs/genome failed"; return 1; }
fi
git -C "$G/jobs" fetch -q origin jobs/genome && git -C "$G/jobs" reset -q --hard origin/jobs/genome
# Stop: a file `<name>.stop` on jobs/genome stops that running job (SIGTERM to its process group, SIGKILL
# after 10 s) and writes rc=stopped. Its out/ dir is kept (a new job can resume from it).
for sf in "$G"/jobs/*.stop; do
  [ -e "$sf" ] || continue
  n=$(basename "$sf" .stop); o="$G/out/$n"
  [ -f "$o/pid" ] && [ ! -f "$o/rc" ] || continue
  p=$(cat "$o/pid")
  if kill -0 "$p" 2>/dev/null; then
    kill -TERM -- "-$p" 2>/dev/null || kill -TERM "$p"; sleep 10
    kill -0 "$p" 2>/dev/null && kill -KILL -- "-$p" 2>/dev/null
  fi
  echo stopped > "$o/rc"; log "stopped job $n (by $n.stop)"
done
active=$(ls "$G"/out/*/started 2>/dev/null | wc -l); done_n=$(ls "$G"/out/*/rc 2>/dev/null | wc -l)
active=$((active - done_n))
for f in "$G"/jobs/*.sh; do
  [ -e "$f" ] || continue
  n=$(basename "$f" .sh); o="$G/out/$n"
  [ -f "$o/rc" ] && continue
  if [ -f "$o/started" ]; then
    # still running? (the job's shell writes its pid)
    if [ -f "$o/pid" ] && kill -0 "$(cat "$o/pid")" 2>/dev/null; then continue; fi
    log "job $n died without an exit code"; echo died > "$o/rc"; continue
  fi
  [ "$active" -ge "$MAXJOBS" ] && continue
  rev=$(head -n 1 "$f" | sed -n 's/^# rev: *//p')
  [ -n "$rev" ] || { mkdir -p "$o"; echo "no '# rev:' line" > "$o/error"; echo bad > "$o/rc"; log "job $n: no rev line"; continue; }
  w="$G/w/$n"
  clone_nopush "$rev" "$w" || { mkdir -p "$o"; echo "checkout $rev failed" > "$o/error"; echo bad > "$o/rc"; log "job $n: checkout $rev failed"; continue; }
  mkdir -p "$o" && cp "$f" "$o/job.sh"
  ( cmake -S "$w/genome" -B "$w/genome/build" -DCMAKE_BUILD_TYPE=Release > "$o/build.log" 2>&1 &&
    cmake --build "$w/genome/build" -j16 --target genome_eval >> "$o/build.log" 2>&1 ) ||
    { echo "build failed" > "$o/error"; echo bad > "$o/rc"; log "job $n: build failed"; continue; }
  date -u +%FT%TZ > "$o/started"
  ( cd "$w" && OUT="$o" setsid nohup sh -c "echo \$\$ > '$o/pid'; nice -n 10 bash '$o/job.sh' > '$o/log.txt' 2>&1; echo \$? > '$o/rc'" < /dev/null > /dev/null 2>&1 & )
  active=$((active + 1)); log "started job $n at $rev"
done
for o in "$G"/out/*/; do
  [ -d "$o" ] || continue; n=$(basename "$o")
  [ -f "$o/rc" ] && [ ! -f "$o/reported" ] && { log "job $n exited rc=$(cat "$o/rc")"; touch "$o/reported"; }
done
# A git checkout left inside a finished job's out/ (e.g. a worktree; its .git points at a deleted worktree)
# makes push_state's `git add` abort on every tick: remove it there and in push_state's clone.
for o in "$G"/out/*/; do
  [ -f "$o/rc" ] || continue
  find "$o" -mindepth 2 -name .git -printf '%h\n' 2>/dev/null | while read -r d; do
    log "removing git checkout ${d#$G/out/} from finished job output"; rm -rf "$d"
  done
done
find /root/bc/state/remote_genome -mindepth 2 -name .git -printf '%h\n' 2>/dev/null | while read -r d; do rm -rf "$d"; done
push_state remote/genome . "$G/out" "remote/genome: $(date -u +%H:%M) UTC"
