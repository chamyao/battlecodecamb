# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-9 (Arena A lead): arenaZ-1 with ONE change: operator mix 55% edit mutation / 30% crossover / 15% tune (was 70/15/15);
# the crossover branch (same species with prob. 0.8, else another species; by ID or by meaning) unchanged. Same random stream as
# arenaZ-1 (the same draw u, only the thresholds move). 7e40b6f, runtime 648bafd, starter seed and only anchor, champions every 50.
# --budget 6 so it does not stop early (Arena A reserve). Panel: arena service.
cp genome/examples/starter.genome $OUT/starter.genome
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -346,7 +346,7 @@
             gs = self.genomes()
             parent = self.tournament(gs)
             u = r.random()
-            op = "mutate" if u < 0.70 else "cross" if u < 0.85 else "tune"
+            op = "mutate" if u < 0.55 else "cross" if u < 0.85 else "tune"  # arenaZ-9: 55/30/15 (was 70/15/15)
             partner = None
             if op == "cross":
                 same = [m for m in gs if m["species"] == parent["species"] and m["name"] != parent["name"]]
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 6 --threads $THREADS --fixed-anchors --gate-every 100000000
