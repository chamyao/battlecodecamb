# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaA-5 (Arena A lead; Cham away, lead continuing): resume arenaA-3's final state with ONE change, deterministic-aware
# evaluation: (a) distinct-games matchmaking (a pair plays only (map, side) games it has not played; exhausted pairs are not
# matched again; genome-genome pairs start with the maps they already played in matches.jsonl), (b) every arena match with
# --bot-seeds (policy anchors seeded as deployed). Inline backport of only those two features from genome/search fe57288
# onto 7e40b6f's arena.py (patch below); prompt, operators, culling, champions, twin check, frozen anchors unchanged.
# Runtime genome/rt-a-fast 648bafd (= db3f945, arenaA-3's runtime; 65-cell check); --refingerprint kept as in arenaA-3.
# --budget 7.77 = arenaA-3's $4.27 (children.jsonl, arenaA-1 included) + $3.50: lineage total <= $8 with arenaA-2's $0.17.
# Panel: job panelA-5.
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -120,6 +120,8 @@
             for m in self.anchors():
                 m["sigma"] = args.anchor_sigma
             self.log("fixed anchors: " + ", ".join(f"{m['name']} {m['mu']:.2f}" for m in self.anchors()))
+        if "pair_maps" not in self.s:
+            self.seed_pair_maps()
         self.rng = random.Random(self.s["births"] * 7919 + self.s["matches"] + 1)
         self.gaps, self.gaps_t = [], 0.0
 
@@ -232,33 +234,62 @@
         return json.dumps(outs)
 
     # ---- matches
-    def next_maps(self):
+    # Backport (arenaA-5) of genome/search fe57288's distinct-games matchmaking: every game is fixed by its map and
+    # side (genomes ignore the seed; policies are seeded as deployed with --bot-seeds), so a pair has 80 distinct
+    # games. A match plays maps the pair has not played yet, both sides; an exhausted pair is not matched again.
+    def pair_key(self, an, bn):
+        return "|".join(sorted((an, bn)))
+
+    def seed_pair_maps(self):
+        """On the first resume with distinct games: the maps each pair of genomes (champions included) already played,
+        from matches.jsonl. Pairs with a policy anchor start empty: under bot seeds those are new games."""
+        pm = self.s["pair_maps"] = {}
+        mem = self.s["members"]
+        for r in self._read("matches"):
+            a, b = mem.get(r.get("a")), mem.get(r.get("b"))
+            if not a or not b or not a["path"].endswith(".genome") or not b["path"].endswith(".genome"):
+                continue
+            got = pm.setdefault(self.pair_key(r["a"], r["b"]), [])
+            got += [m for m in r.get("maps", []) if m not in got]
+        self.log(f"distinct games: {len(pm)} genome pairs seeded with their played maps from matches.jsonl")
+
+    def next_maps(self, an, bn):
         k = self.a.match_games // 2
+        played = set(self.s.setdefault("pair_maps", {}).get(self.pair_key(an, bn), []))
         ptr = self.s["map_ptr"]
         self.s["map_ptr"] = (ptr + k) % len(self.maps)
-        return [self.maps[(ptr + i) % len(self.maps)] for i in range(k)]
+        order = [self.maps[(ptr + i) % len(self.maps)] for i in range(len(self.maps))]
+        fresh = [m for m in order if Path(m).stem not in played][:k]
+        self.s["pair_maps"].setdefault(self.pair_key(an, bn), []).extend(Path(m).stem for m in fresh)
+        return fresh
+
+    def exhausted(self, an, bn):
+        return len(self.s.setdefault("pair_maps", {}).get(self.pair_key(an, bn), [])) >= len(self.maps)
 
     def pick_pair(self):
         """Newborn matches first; else a random pairing weighted toward uncertain genomes."""
         alive = {m["name"] for m in self.players()}
         while self.s["newborn_queue"]:
             a, b = self.s["newborn_queue"].pop(0)
-            if a in alive and b in alive:
+            if a in alive and b in alive and not self.exhausted(a, b):
                 return a, b
         gs = self.genomes()
         if len(gs) < 1:
             return None
-        a = self.rng.choices(gs, [m["sigma"] for m in gs])[0]
-        others = [m for m in self.players() if m["name"] != a["name"]]
-        return a["name"], self.rng.choice(others)["name"]
+        for _ in range(50):
+            a = self.rng.choices(gs, [m["sigma"] for m in gs])[0]
+            others = [m for m in self.players() if m["name"] != a["name"] and not self.exhausted(a["name"], m["name"])]
+            if others:
+                return a["name"], self.rng.choice(others)["name"]
+        return None
 
     def play_match(self, an, bn, seed, maps):
         with self.lock:
             a, b = self.s["members"][an], self.s["members"][bn]
             sa, sb = self.spec(a), self.spec(b)
-        out = subprocess.run([str(self.sc_eval()), "--a", sa, "--b", sb, "--games", str(self.a.match_games),
-                              "--threads", "1", "--seed", str(seed), *maps], capture_output=True, text=True,
-                             timeout=1800)
+        out = subprocess.run([str(self.sc_eval()), "--a", sa, "--b", sb, "--games", str(2 * len(maps)),
+                              "--threads", "1", "--seed", str(seed), "--bot-seeds", *maps], capture_output=True,
+                             text=True, timeout=1800)
         if out.returncode != 0:
             return {"error": f"exit {out.returncode}: {out.stderr[-200:]}"}
         return json.loads(out.stdout)
@@ -569,7 +600,7 @@
                         pair = self.pick_pair()
                         if pair is None:
                             break
-                        mseed, maps = 9_000_000 + self.s["matches"] + len(matches), self.next_maps()
+                        mseed, maps = 9_000_000 + self.s["matches"] + len(matches), self.next_maps(*pair)
                     matches[mpool.submit(self.play_match, *pair, mseed, maps)] = (*pair, mseed, maps)
                 if not matches and not births:
                     break
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaA-3/arena" --tag A --seed genome/seeds/v23.genome \
    --budget 7.77 --threads $THREADS --fixed-anchors --refingerprint --gate-every 100000000
