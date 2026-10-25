# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-2 (Arena A lead; Cham: Arena Z is the training-setup testbed): a REPLICATE of arenaZ-1 to measure run-to-run
# variance. Identical job (7e40b6f, runtime 648bafd, starter seed and only fixed anchor, champions every 50, $3) except the
# arena's random stream: inline patch adding --rng-salt (seed of self.rng + 1000003 x salt; parent picks, operator draws,
# pairings), run with --rng-salt 1. (Claude's sampling differs between runs anyway.) Panel: on the arena service.
cp genome/examples/starter.genome $OUT/starter.genome
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -120,7 +120,8 @@
             for m in self.anchors():
                 m["sigma"] = args.anchor_sigma
             self.log("fixed anchors: " + ", ".join(f"{m['name']} {m['mu']:.2f}" for m in self.anchors()))
-        self.rng = random.Random(self.s["births"] * 7919 + self.s["matches"] + 1)
+        # arenaZ-2: --rng-salt shifts the arena's own random stream (parent picks, operator draws, match pairing)
+        self.rng = random.Random(self.s["births"] * 7919 + self.s["matches"] + 1 + 1_000_003 * args.rng_salt)
         self.gaps, self.gaps_t = [], 0.0
 
     # ---- logging
@@ -644,6 +645,7 @@
     ap.add_argument("--summary-every", type=int, default=10)
     ap.add_argument("--max-hours", type=float, default=48)
     ap.add_argument("--tail-matches", type=int, default=200, help="matches played after the budget runs out")
+    ap.add_argument("--rng-salt", type=int, default=0, help="shifts the arena's random stream (0 = as before)")
     ap.add_argument("--fixed-anchors", action="store_true", default=FIXED_DEFAULT,
                     help="anchors keep fixed ratings (frozen at their current mu on resume)")
     ap.add_argument("--anchor-sigma", type=float, default=1.0)
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 3 --threads $THREADS --fixed-anchors --gate-every 100000000 --rng-salt 1
