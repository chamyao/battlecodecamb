#!/bin/bash
# real.sh GENOME NAME: cambc 4.0.0 bot from GENOME (genome/bot/sync.sh, dd28e2f3 runtime), 70 maps x 2 sides vs live v39
# (~/ws4/bots/v39); prints "NAME sha256 wins/140 crashes N"
set -e
G=$(realpath $1); N=$2; R=/home/user/battlecodecamb; O=/tmp/claude-0/real/$N
export SSL_CERT_FILE=/root/.ccr/ca-bundle.crt
cd $R && bash genome/bot/sync.sh $G ~/ws4/bots/$N > /dev/null
bash genome/bot/gate4.sh $N v39 $O
w=0; n=0; cr=0
for f in $O/*-A.log $O/*-B.log; do
  s=${f%.log}; s=${s##*-}; n=$((n+1))
  if [ $s = A ]; then grep -q "Team A ($N) wins" $f && w=$((w+1)); else grep -q "Team B ($N) wins" $f && w=$((w+1)); fi
  c=$(awk -v b=$N '$2==b && NF>=7 {print $7}' $f | head -1); cr=$((cr+${c:-0}))
done
echo "$N $(sha256sum $G | cut -c1-16) $w/$n crashes $cr"
