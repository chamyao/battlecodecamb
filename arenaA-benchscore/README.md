# Bench scoring (Arena A lead; genome/search benchscore.py)

Runtime: arena engine genome/simspeed 4b60b58 (NOT bit-identical to db3f945 for genome-vs-policy games; compare
within this file only). Every parent (kind=parent), valid child (kind=child) of promptbench-2/-r1b/-r1c and 40 null
children (kind=null: constant tuning sigma 0.02, 8 per promptbench-2 parent; genomes in null/) vs style-gconv1,
tune-v20-L1, rall2-ca4-lean-g, v7, opp-tune5-metadraft, tune-v20-L1c (and null children vs their parent):
the 80 distinct games each (40 maps x 2 sides, bot seeds). Note: promptbench-2's own child-vs-parent column
(vs_parent) was played at db3f945. Updated as scoring proceeds.
