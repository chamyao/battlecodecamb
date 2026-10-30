#!/bin/bash
# build4.sh GENOME NAME : genome -> bot source (genome/v0 runtime) -> cambc 4.0.0 release build in ws4/bots/NAME
S=/tmp/claude-0/-home-user-battlecodecamb/ffe54acc-bdb7-57df-a68a-1cdbcfbc6770/scratchpad; W4=$S/cambc4/ws4
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
rm -rf $W4/bots/$2 && (cd /tmp/claude-0/wt-v0 && bash genome/bot/sync.sh $1 $W4/bots/$2 >/dev/null) && rm -rf $W4/bots/$2/.cambc && (cd $W4 && $S/cambc4/venv/bin/cambc build --release $2 2>&1 | tail -1)
