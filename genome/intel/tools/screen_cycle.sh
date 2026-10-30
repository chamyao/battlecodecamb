#!/bin/bash
# One ladder-screen cycle (SCREEN.md): submit a built bot, wait until it is live,
# queue screen_v1, wait for all 30 games, fetch + extract (engine 2.0.0), report,
# and pair against the baseline games.
# Usage: genome/intel/tools/screen_cycle.sh BATCH BOTNAME "NOTE" [BASE_GAMES_JSON]
#   RESUME_V=N skips the submit and continues with already-submitted version N.
#   BATCH    e.g. s1 (writes genome/intel/batches/BATCH_plan.json, BATCH_games.json, BATCH_report.md)
#   BOTNAME  a bot dir under $WS4/bots, already built and checked
# Env: WS4 (cambc 4.0.0 workspace), CAMBC4 (cambc 4.0.0 binary), AN (analysis dir with extract.js).
set -eo pipefail
B=$1; BOT=$2; NOTE=$3; BASE=${4:-genome/intel/batches/b18base_games.json}
REPO=$(git rev-parse --show-toplevel); cd "$REPO"
D=genome/intel/batches; SCR=${SCR:?set SCR to a scratch dir}
[ ${#NOTE} -le 80 ] || { echo "note too long"; exit 1; }
# the public API returns 429/503 under load: retry every platform call
retry() { local i out; for i in 1 2 3 4 5 6 7 8 9 10; do out=$("$@" 2>&1) && { echo "$out"; return 0; }; sleep $((i * 5)); done; echo "$out" >&2; return 1; }
if [ -n "$RESUME_V" ]; then V=$RESUME_V; echo "resume v$V (already submitted)"
else
  (cd "$WS4" && "$CAMBC4" submit "$BOT" --note "$NOTE" | tail -1); echo "submitted $(date -u +%FT%TZ)"
  V=$(retry "$CAMBC4" submissions list | awk 'NR>3 && /^v[0-9]+/{print substr($1,2); exit}')
fi
for i in $(seq 1 60); do
  SL=$(retry "$CAMBC4" submissions list)
  echo "$SL" | sed -n 2p | grep -q "Live: $V " && break
  echo "$SL" | grep -E "^v$V +(failed|error)" && exit 1
  sleep 20
done
echo "live v$V $(date -u +%FT%TZ)"
cp $D/screen_v1_plan.json $D/${B}_plan.json
python3 -I genome/intel/run_batch.py queue $D/${B}_plan.json | tail -1 > /dev/null; echo "queued $(date -u +%FT%TZ)"
G=$(python3 -c "import json;print(' '.join(p['group']['groupId'] for p in json.load(open('$D/${B}_plan.json'))))")
for i in $(seq 1 120); do
  n=0; for g in $G; do k=$(retry cambc match-groups show $g --json | python3 -c "import json,sys;print(sum(m['status']=='finished' for m in json.load(sys.stdin)['matches']))"); n=$((n+k)); done
  [ $n -ge 30 ] && break; sleep 30
done
echo "finished $n/30 $(date -u +%FT%TZ)"
(cd "$AN" && python3 fetch_groups.py $SCR/$B $G | tail -1)
python3 -I "$AN"/ladder_prep.py $SCR/$B $SCR/${B}x > $SCR/$B/prep.txt
grep -v '^skip' $SCR/$B/prep.txt | while read r o w; do [ -f $o ] || CAMBC_WASM=$w node "$AN"/extract.js $r $o > /dev/null 2>&1 || echo FAIL $r; done
python3 -I genome/intel/batch_report.py "$AN" $SCR/$B $SCR/${B}x --json $D/${B}_games.json > $D/${B}_report.md
head -1 $D/${B}_report.md
python3 -I genome/intel/paired.py $BASE $D/${B}_games.json
