# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-4 (Arena A lead; Cham: first in the queue): arenaZ-1 exactly (7e40b6f, runtime 648bafd, starter seed and only fixed
# anchor, champions every 50, $3, same RNG seed as arenaZ-1) with ONE change: every edge mutation uses promptexp-1's A1 operator
# (genome/search a1op.py + promptexp.py at 1bcb3d44487b200c9b123b053f2373e470ec079d: minimal system + typed explicit Task, T1-T5 equal, the type's check with one
# retry, then rejected; links skip trivial callees, else the score gene's links). Crossover, tuning, the 70/15/15 mix, Opus
# every 10th, twin check, culling unchanged. Inline patch: arena --a1-mutate (keeps the arena's random draws as before).
cp genome/examples/starter.genome $OUT/starter.genome
git fetch -q origin genome/search || exit 1
git show 1bcb3d44487b200c9b123b053f2373e470ec079d:genome/search/promptexp.py > genome/search/promptexp.py || exit 1
git show 1bcb3d44487b200c9b123b053f2373e470ec079d:genome/search/a1op.py > genome/search/a1op.py || exit 1
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -373,8 +373,12 @@
                 op = "mutate"
         if op == "mutate":
             two = 1.0 if r.random() < 0.25 else 0.0
-            child = operators.mutate(ptext, self.claude, r, prefix, self._stats_line(parent), two,
-                                     notes_fn=self.intel_notes)
+            if self.a.a1_mutate:  # arenaZ-4: promptexp-1's A1 link operator (genome/search a1op.py) for every mutation
+                from . import a1op
+                child = a1op.mutate(ptext, self.claude, r, prefix)
+            else:
+                child = operators.mutate(ptext, self.claude, r, prefix, self._stats_line(parent), two,
+                                         notes_fn=self.intel_notes)
         return self.check(child, parents, seq)
 
     def _stats_line(self, m):
@@ -644,6 +648,7 @@
     ap.add_argument("--summary-every", type=int, default=10)
     ap.add_argument("--max-hours", type=float, default=48)
     ap.add_argument("--tail-matches", type=int, default=200, help="matches played after the budget runs out")
+    ap.add_argument("--a1-mutate", action="store_true", help="mutations use the A1 link operator (a1op.py)")
     ap.add_argument("--fixed-anchors", action="store_true", default=FIXED_DEFAULT,
                     help="anchors keep fixed ratings (frozen at their current mu on resume)")
     ap.add_argument("--anchor-sigma", type=float, default=1.0)
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -c "from genome.search import a1op, arena; print('a1op ok')" || exit 1
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 3 --threads $THREADS --fixed-anchors --gate-every 100000000 --a1-mutate
