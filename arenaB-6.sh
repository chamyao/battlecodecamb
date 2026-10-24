# rev: 5a961dfc82c499b9416979b896d253562a9502f2
# Arena B (genome lead + Arena B lead): resume arenaB-5 (stopped) on genome/v0 d0c0704 (77da39c + box_field: fuel
# 82b5dcb runtime, lang checks); twin-check outcomes recomputed on it; fixed anchors (tune-v20-L1c keeps calibrating
# if under 200 games); matches use only maps a pair has not played (80 distinct games per pair) with policies seeded
# as deployed; intel on; total cap $8. In-arena gate rounds off (gatekeeper-8 gates vs B318).
while [ ! -f "$OUT/../arenaB-5/rc" ]; do sleep 60; done
echo "arenaB-5 exited rc=$(cat "$OUT/../arenaB-5/rc"); resuming"
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaB-5/arena" --tag B --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000 --intel-branch genome/intel --gate-ref genome/candidates/B318.genome
