#!/bin/bash
# Run the host-backed Bitboard self-test (bot/tools/bbtest) on the given maps.
set -e
ln -sfn "$(cd "$(dirname "$0")" && pwd)/bbtest" ~/ws/bots/bbtest
cd ~/ws
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
for m in "$@"; do
	rm -rf /tmp/bbtest && cambc run bbtest starter-cpp --release --map maps/$m.map26a --rounds 2 --fuel 1000000000 -o /tmp/bbtest > /tmp/bbtest.log 2>&1 || { tail /tmp/bbtest.log; exit 1; }
	(cd /tmp/bbtest && unzip -q -o *.repl26a && tr -d '\000' < team-a.stdout | grep "^@@BB")
done
