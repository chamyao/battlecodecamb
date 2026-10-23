#!/bin/bash
# Profile the deploy bot's real fuel in cambc (see bot/profile_patch.py) on the given maps,
# running POLICY (default policies/v2.policy). bot/ is not modified: the bot is synced into a
# copy. The same game is also played by the unpatched bot (identical decisions, so an identical
# game), whose real per-turn fuel calibrates the profiler's distortion away. Output:
# /tmp/prof/<policy name>/<map>/prof.txt and plain/*.repl26a; then
#   python3 oracle/tools/fuel_calibrate.py /tmp/prof/*/*
# Usage: [POLICY=policies/x.policy] [ROUNDS=800] [EVERY=10] [JOBS=3] oracle/run_bot_profile.sh MAP...
# EVERY: log every N-th turn (1 for coverage runs; draft turns are always logged).
set -e
repo=$(cd "$(dirname "$0")/.." && pwd)
policy=$(realpath "${POLICY:-$repo/policies/v2.policy}")
tag=$(basename "$policy" .policy)
bot=/tmp/botprof_$tag
plain=/tmp/botplain_$tag
rm -rf "$bot" && mkdir -p "$bot" && cp -r "$repo/bot/src" "$bot/" && rm -f "$bot"/src/sprof.h
"$repo/bot/sync.sh" "$policy" "$bot" > /dev/null
rm -rf "$plain" && cp -r "$bot" "$plain"
ln -sfn "$plain" ~/ws/bots/plain_$tag
python3 "$repo/bot/profile_patch.py" "$bot" ${EVERY:-10}
ln -sfn "$bot" ~/ws/bots/prof_$tag
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
(cd ~/ws && cambc build prof_$tag --release > /dev/null && cambc build plain_$tag --release > /dev/null)
export tag
run() {
	m=$1; out=/tmp/prof/$tag/$m; rm -rf $out; mkdir -p $out
	(cd ~/ws && cambc run prof_$tag starter-cpp --release --map maps/$m.map26a --rounds ${ROUNDS:-800} --fuel 100000000 \
		--log-limit 2000000000 -o $out > $out/log.txt 2>&1)
	(cd $out && unzip -q -o *.repl26a && tr -d '\000' < team-a.stdout | grep "^@@" > prof.txt)
	mkdir -p $out/plain
	(cd ~/ws && cambc run plain_$tag starter-cpp --release --map maps/$m.map26a --rounds ${ROUNDS:-800} --fuel 100000000 \
		-o $out/plain > $out/plain/log.txt 2>&1)
	echo "$tag $m $(wc -l < $out/prof.txt) lines"
}
export -f run
printf "%s\n" "$@" | xargs -P ${JOBS:-3} -I{} bash -c 'run {}'
