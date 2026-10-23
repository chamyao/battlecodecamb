#!/bin/bash
# Play the deploy bot against an opponent on every pool map (in parallel) and summarise
# result and per-turn fuel per map. Usage: bot/tools/pool.sh [OPPONENT] [OUT] [JOBS] [extra cambc args]
# Builds once (cambc build) before the parallel runs.
set -e
repo=$(cd "$(dirname "$0")/../.." && pwd)
opp=${1:-starter-cpp}; out=${2:-/tmp/pool}; jobs=${3:-3}
shift $(( $# < 3 ? $# : 3 ))
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
ln -sfn "$repo/bot" ~/ws/bots/deploy
(cd ~/ws && cambc build deploy --release > /dev/null)
rm -rf "$out" && mkdir -p "$out"
export out opp
export EXTRA="$*"
run() {
	m=$1; d=$out/$m; mkdir -p $d
	(cd ~/ws && cambc run deploy $opp --release --map maps/$m.map26a -o $d $EXTRA > $d/log.txt 2>&1) || echo "FAILED $m"
}
export -f run
ls ~/ws/maps/*.map26a | xargs -n1 basename | sed 's/.map26a//' | xargs -P $jobs -I{} bash -c 'run {}'
python3 "$repo/bot/tools/pool_summary.py" "$out"
