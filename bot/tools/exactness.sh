#!/bin/bash
# Exactness check: the deploy bot against a reference build of itself (BOT_REFERENCE: no
# memo, the simulator's algorithms on fresh host searches), both with unlimited fuel against
# OPPONENT on every pool map. Games are deterministic, so every map must give the same
# result line (gems, kills, deaths, gold). Usage: bot/tools/exactness.sh [POLICY] [OPPONENT] [JOBS]
set -e
repo=$(cd "$(dirname "$0")/../.." && pwd)
pol=${1:-$repo/policies/v2.policy}; opp=${2:-starter-cpp}; jobs=${3:-4}
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
for v in opt ref; do
	d=/tmp/exact_bot_$v
	rm -rf $d && mkdir -p $d && cp -r "$repo/bot/src" $d/ && rm -rf $d/src/.cambc
	bash "$repo/bot/sync.sh" "$pol" $d > /dev/null
	[ $v = ref ] && sed -i '1i #define BOT_REFERENCE' $d/src/bot_api.cpp
	ln -sfn $d ~/ws/bots/exact_$v
	(cd ~/ws && cambc build exact_$v --release > /dev/null)
done
export opp
run() {
	m=$1
	for v in opt ref; do
		o=/tmp/exact/$v/$m; rm -rf $o; mkdir -p $o
		(cd ~/ws && cambc run exact_$v $opp --release --map maps/$m.map26a --fuel 1000000000 -o $o > $o/log.txt 2>&1) || echo "FAILED $v $m"
	done
	a=$(grep -E "^\s+A\s" /tmp/exact/opt/$m/log.txt | awk '{print $3,$4,$5,$6,$7}')
	b=$(grep -E "^\s+A\s" /tmp/exact/ref/$m/log.txt | awk '{print $3,$4,$5,$6,$7}')
	[ "$a" = "$b" ] && echo "same $m $a" || echo "DIFF $m opt=[$a] ref=[$b]"
}
export -f run
ls ~/ws/maps/*.map26a | xargs -n1 basename | sed 's/.map26a//' | xargs -P $jobs -I{} bash -c 'run {}' | sort
