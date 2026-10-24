#!/bin/bash
# Deploy-faithful gate row for a genome: --bot-seeds /80 vs a base genome and the anchors (both sides, all maps).
# Usage: genome/intel/tools/gate80.sh GENOME BASE.genome
G=$1; B=$2
cd "$(dirname "$0")/../../.."
row="$(basename $G .genome)"
for opp in "$B" policies/candidates/tune-v20-L1c.policy policies/candidates/style-gconv1.policy policies/v7.policy policies/candidates/tune-v20-L1.policy policies/candidates/rall2-ca4-lean-g.policy policies/opp-tune5-metadraft.policy; do
	if [ "$G" = "$B" ] && [ "$opp" = "$B" ]; then row="$row | —"; continue; fi
	w=$(python3 -m genome.intel.sim_metrics "$G" "$opp" --bot-seeds | sed -E 's/.*\(([0-9.]+)\/80\).*susp ([0-9.]+).*/\1 \2/')
	row="$row | ${w% *}"; susp=${w#* }
done
echo "$row | susp $susp"
