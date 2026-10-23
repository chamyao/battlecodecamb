#!/bin/bash
# Profile the deploy bot's real fuel in cambc (see bot/profile_patch.py) on the given maps.
# Usage: oracle/run_bot_profile.sh MAP... ; output in /tmp/prof/MAP/prof.txt, then
#        python3 oracle/tools/fuel_calibrate.py MAP...
set -e
repo=$(cd "$(dirname "$0")/.." && pwd)
"$repo/bot/sync.sh" > /dev/null
rm -rf /tmp/botprof && cp -r "$repo/bot" /tmp/botprof && rm -rf /tmp/botprof/.cambc
python3 "$repo/bot/profile_patch.py" /tmp/botprof
ln -sfn /tmp/botprof ~/ws/bots/deployprof
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
(cd ~/ws && cambc build deployprof --release > /dev/null)
run() {
	m=$1; out=/tmp/prof/$m; rm -rf $out; mkdir -p $out
	(cd ~/ws && cambc run deployprof starter-cpp --release --map maps/$m.map26a --rounds ${ROUNDS:-800} --fuel 100000000 \
		--log-limit 2000000000 -o $out > $out/log.txt 2>&1)
	(cd $out && unzip -q -o *.repl26a && tr -d '\000' < team-a.stdout | grep "^@@" > prof.txt)
	echo "$m $(wc -l < $out/prof.txt) lines"
}
export -f run
printf "%s\n" "$@" | xargs -P ${JOBS:-3} -I{} bash -c 'run {}'
