#!/bin/bash
# pipeline.sh SPEC CENTRE TAG REF: sim screen of SPEC around CENTRE vs tb.BASE (bot seeds), keep wins >= 38 whose
# sim games differ from the centre's, then real-cambc screen of the survivors vs the built bot REF.
set -eu
cd /home/user/battlecodecamb
spec=$1; centre=$2; tag=$3; ref=$4
python3 genome/tuneb/screen.py $spec genome/tuneb/runs/${tag}_sim.jsonl 0 0 --bot-seeds --text-base $centre
keep=$(python3 - genome/tuneb/runs/${tag}_sim.jsonl <<'PY'
import json, sys
R = [json.loads(l) for l in open(sys.argv[1])]
c = [r for r in R if r['tag'] == 'centre'][0]
k = ['centre'] + [r['tag'] for r in sorted(R, key=lambda r: -r['wins']) if r['tag'] != 'centre' and r['wins'] >= 38 and r['results'] != c['results']]
print(','.join(k))
PY
)
echo "real: $(echo $keep | tr ',' '\n' | wc -l) variants"
python3 genome/tuneb/real_screen.py $spec genome/tuneb/runs/${tag}_real.jsonl $ref --text-base $centre --only "$keep"
echo DONE
