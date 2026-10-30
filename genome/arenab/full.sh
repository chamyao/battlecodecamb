#!/bin/bash
# full.sh BOT : gate vs v40 + split + deaths + solo
S=/tmp/claude-0/-home-user-battlecodecamb/ffe54acc-bdb7-57df-a68a-1cdbcfbc6770/scratchpad; v=$1
cd /home/user/battlecodecamb && bash genome/arenab/gate4.sh $v x6-83 >/dev/null 2>&1
python3 /tmp/claude-0/split.py $S/cambc4/runs/$v-vs-x6-83/batch.log $v $S/cambc4/oldmaps.txt | tail -1
(cd /tmp/claude-0/deaths && python3 deaths.py $S/cambc4/runs/$v-vs-x6-83 $v)
bash /tmp/claude-0/deaths/solo.sh $v
