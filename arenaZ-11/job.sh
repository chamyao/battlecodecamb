# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-11 (Arena A lead; Cham-approved; genome/arenaa dff5f0cd arenaa/SPLIT.md): arenaZ-1 + in-place gene splitting. After every
# 10th birth, one random live member whose longest gene has > 30 code lines gets that gene split by Claude (Haiku) into caller +
# helpers; accepted only if it type-checks, has more genes and is a behavioural twin on the fingerprint games (one retry); applied
# in place (same name, rating, species, games; not a birth); logged to splits.jsonl. The member draw uses its own generator and
# splits use Haiku outside the births budget and the Opus cadence, so the births stream and spend match arenaZ-1's ($3, ~475 births).
# 7e40b6f, runtime 648bafd, starter seed and only anchor, champions every 50, mix 70/15/15. Panel: arena service.
cp genome/examples/starter.genome $OUT/starter.genome
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -47,8 +47,8 @@
 
 from .. import build as gbuild
 from .. import lang
-from . import edit, operators
-from .claude import BudgetExceeded, Claude
+from . import edit, operators, prompts
+from .claude import HAIKU, BudgetExceeded, Claude
 from .score import Scorer
 
 FRESH_SEEDS = (5_000_011, 6_000_011)
@@ -393,6 +393,82 @@
         rec["fingerprint"] = fp
         return rec, child.source
 
+    # ---- arenaZ-11: in-place gene splitting (arenaa/SPLIT.md)
+    SPLIT_TASK = """# Your task: split one gene
+Split gene {name} [{gid}] into a caller plus one or more new helper genes so that the program computes exactly the
+same thing in every situation. Do not change any behaviour, constant, order of tests, or primitive call results.
+New genes get @gene("new", "<one line>", parents=["{gid}"]); {name} keeps its id ({gid}).
+
+Reply with one ```python code block holding the new version of {name} (keep @gene("{gid}", ...)) and each new
+helper gene. Do not repeat the other genes. Then write nothing else."""
+
+    def split_candidates(self):
+        out = []
+        for m in self.genomes():
+            _, _, genes = edit.segments((self.out / m["path"]).read_text())
+            gid, text = max(genes.items(), key=lambda kv: edit.gene_count_lines(kv[1]))
+            if edit.gene_count_lines(text) > self.a.split_lines:
+                out.append((m["name"], gid))
+        return out
+
+    def split(self, births):
+        """Split the longest gene of one random eligible live member; apply in place if it is a behavioural twin."""
+        with self.lock:
+            cands = self.split_candidates()
+            if not cands:
+                self._write("splits", {"births": births, "skipped": "no member with a gene over "
+                                                                    f"{self.a.split_lines} lines"})
+                return
+            name, gid = random.Random(1_000_003 + births).choice(cands)  # own stream: the arena's rng is untouched
+            m = self.s["members"][name]
+            ptext = (self.out / m["path"]).read_text()
+            fp = m["fingerprint"]
+        genome = lang.parse(ptext)
+        gname = next(g.name for g in genome.genes.values() if g.id == gid)
+        _, _, genes = edit.segments(ptext)
+        user = f"## The genome\n```python\n{ptext.strip()}\n```\n\nSplit {gname}."
+        system = [prompts.SYSTEM_BASE, self.SPLIT_TASK.format(name=gname, gid=gid)]
+        rec = {"births": births, "member": name, "gene": gid, "gene_name": gname,
+               "lines_before": edit.gene_count_lines(genes[gid]), "genes_before": len(genes), "cost": 0.0, "tries": []}
+        for attempt in range(2):
+            text, model, cost, info = self.claude.ask(system, user, model=HAIKU)
+            with self.claude.lock:  # splits are outside the births budget
+                self.claude.spent -= cost
+            rec["cost"] += cost
+            why, child = None, None
+            try:
+                if text is None:
+                    raise edit.EditError("refusal")
+                child, st = operators.apply_mutation(ptext, text, {gid}, f"X{births}")
+                n_genes = len(edit.segments(child)[2])
+                if n_genes <= len(genes):
+                    why = f"the split must add at least one gene ({n_genes} genes, was {len(genes)})"
+                elif self.fingerprint(child) != fp:
+                    why = "not a behavioural twin: per-game outcomes on the fingerprint games differ from the parent's"
+            except (edit.EditError, lang.GenomeError, RuntimeError) as e:
+                why = f"{type(e).__name__}: {e}"
+            rec["tries"].append(why or "ok")
+            if why is None:
+                break
+            user = f"{user}\n\n# Your previous reply\n{(text or '').strip()}\n\nIt was rejected: {why}. Reply again."
+        rec["accepted"] = why is None
+        if why is None:
+            _, _, cg = edit.segments(child)
+            rec.update(genes_after=len(cg), lines_after=edit.gene_count_lines(cg[gid]),
+                       new_genes=[i for i in cg if i not in genes])
+            with self.lock:
+                if self.s["members"].get(name, {}).get("alive", True) and name in self.s["members"]:
+                    (self.out / m["path"]).write_text(child)
+                    self.specs.pop(name, None)
+                    self.s["split_cost"] = self.s.get("split_cost", 0.0) + rec["cost"]
+                else:
+                    rec["accepted"], rec["note"] = False, "member died meanwhile"
+        else:
+            with self.lock:
+                self.s["split_cost"] = self.s.get("split_cost", 0.0) + rec["cost"]
+        self._write("splits", rec)
+        self.log(f"split {name}.{gname}: {'applied' if rec['accepted'] else 'discarded'} ({rec['tries']}) ${rec['cost']:.4f}")
+
     def accept(self, rec, source):
         with self.lock:
             twin = next((m["name"] for m in self.genomes() if m["fingerprint"] == rec.get("fingerprint")), None)
@@ -550,7 +626,7 @@
         births_open = True
         seq = len(self._read("children"))
         with ThreadPoolExecutor(a.threads) as mpool, ThreadPoolExecutor(a.births_in_flight) as bpool:
-            matches, births = {}, {}
+            matches, births, splits = {}, {}, {}
             while time.time() < t_end:
                 # births: keep up to --births-in-flight proposals going once the newborn queue is drained
                 with self.lock:
@@ -571,10 +647,17 @@
                             break
                         mseed, maps = 9_000_000 + self.s["matches"] + len(matches), self.next_maps()
                     matches[mpool.submit(self.play_match, *pair, mseed, maps)] = (*pair, mseed, maps)
-                if not matches and not births:
+                if not matches and not births and not splits:
                     break
-                done, _ = wait(list(matches) + list(births), timeout=30, return_when=FIRST_COMPLETED)
+                done, _ = wait(list(matches) + list(births) + list(splits), timeout=30, return_when=FIRST_COMPLETED)
                 for f in done:
+                    if f in splits:
+                        splits.pop(f)
+                        try:
+                            f.result()
+                        except Exception as e:
+                            self.log(f"split error: {type(e).__name__}: {e}")
+                        continue
                     if f in matches:
                         an, bn, mseed, maps = matches.pop(f)
                         try:
@@ -593,6 +676,8 @@
                             self.log(f"birth error: {type(e).__name__}: {e}")
                             continue
                         m = self.accept(rec, source)
+                        if m and a.split_every and self.s["births"] % a.split_every == 0:
+                            splits[bpool.submit(self.split, self.s["births"])] = self.s["births"]
                         if m:
                             self.log(f"birth {m['name']} ({rec['op']} {rec['model'] or ''}) of {rec['parents']} "
                                      f"species {m['species']}; {len(self.genomes())} genomes ${self.claude.spent:.2f}")
@@ -644,6 +729,8 @@
     ap.add_argument("--summary-every", type=int, default=10)
     ap.add_argument("--max-hours", type=float, default=48)
     ap.add_argument("--tail-matches", type=int, default=200, help="matches played after the budget runs out")
+    ap.add_argument("--split-every", type=int, default=0, help="arenaZ-11: births between in-place gene splits (0: off)")
+    ap.add_argument("--split-lines", type=int, default=30, help="split only a longest gene over this many code lines")
     ap.add_argument("--fixed-anchors", action="store_true", default=FIXED_DEFAULT,
                     help="anchors keep fixed ratings (frozen at their current mu on resume)")
     ap.add_argument("--anchor-sigma", type=float, default=1.0)
PATCH
git diff --stat
git fetch -q origin genome/rt-a-fast; git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 3 --threads $THREADS --fixed-anchors --gate-every 100000000 --split-every 10 --split-lines 30
