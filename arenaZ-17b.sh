# rev: 7e40b6f9582dc78a054cc969f81077bf58ea5294
# arenaZ-17b (Arena A lead; Cham-approved, genome/arenaa arenaa/CULL.md): arenaZ-15 exactly (7e40b6f + batch-mutate, runtime
# 648bafd, every call on Opus, batches of 8, --max-births 475, --budget 20) + rng-salt.patch + cull-minmu.patch (inline; =
# genome/search patches/). This arm: --cull min-mu, --rng-salt 0 (same stream as arenaZ-15). Panel: panelZ-17b.
cp genome/examples/starter.genome $OUT/starter.genome
git fetch -q origin genome/rt-a-fast
git apply <<'PATCH' || exit 1
diff --git a/genome/search/arena.py b/genome/search/arena.py
index 747241d5..98aa7a50 100644
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -93,7 +93,12 @@ class Arena:
             (self.out / d).mkdir(parents=True, exist_ok=True)
         self.lock = threading.RLock()
         self.sc = Scorer([], threads=1)
-        self.claude = Claude(args.budget, opus_every=args.opus_every)
+        if args.batch_mutate:  # arenaZ-15: edit mutations go out in batches (batchclaude.py)
+            from .batchclaude import BatchClaude
+            self.claude = BatchClaude(args.budget, opus_every=args.opus_every, size=args.batch_mutate,
+                                      wait=args.batch_wait, log_path=self.out / "batches.jsonl")
+        else:
+            self.claude = Claude(args.budget, opus_every=args.opus_every)
         self.claude.spent = sum(r.get("cost", 0.0) for r in self._read("children"))
         self.maps = sorted(MAPS)
         self.specs = {}
@@ -555,6 +560,7 @@ class Arena:
                 # births: keep up to --births-in-flight proposals going once the newborn queue is drained
                 with self.lock:
                     want_birth = (births_open and len(births) < a.births_in_flight
+                                  and not (a.max_births and self.s["births"] + len(births) >= a.max_births)
                                   and len(self.s["newborn_queue"]) <= a.threads
                                   and (len(self.genomes()) < a.capacity or self.s["since_birth"] >= a.random_matches))
                 if want_birth:
@@ -593,6 +599,9 @@ class Arena:
                             self.log(f"birth error: {type(e).__name__}: {e}")
                             continue
                         m = self.accept(rec, source)
+                        if a.max_births and self.s["births"] >= a.max_births and births_open:
+                            births_open = False
+                            self.log(f"{self.s['births']} births (--max-births {a.max_births}): no more births")
                         if m:
                             self.log(f"birth {m['name']} ({rec['op']} {rec['model'] or ''}) of {rec['parents']} "
                                      f"species {m['species']}; {len(self.genomes())} genomes ${self.claude.spent:.2f}")
@@ -641,6 +650,10 @@ def main(argv=None):
     ap.add_argument("--regress", type=float, default=0.03)
     ap.add_argument("--threads", type=int, default=5)
     ap.add_argument("--births-in-flight", type=int, default=3)
+    ap.add_argument("--batch-mutate", type=int, default=0,
+                    help="send edit mutations as one call per batch of up to this many (0: one call each)")
+    ap.add_argument("--max-births", type=int, default=0, help="stop births at this total (0: budget only)")
+    ap.add_argument("--batch-wait", type=float, default=20.0, help="send a partial batch this long after its oldest request")
     ap.add_argument("--summary-every", type=int, default=10)
     ap.add_argument("--max-hours", type=float, default=48)
     ap.add_argument("--tail-matches", type=int, default=200, help="matches played after the budget runs out")
diff --git a/genome/search/batchclaude.py b/genome/search/batchclaude.py
new file mode 100644
index 00000000..a8cc88a9
--- /dev/null
+++ b/genome/search/batchclaude.py
@@ -0,0 +1,107 @@
+"""Batched edit mutations (arenaZ-15): mutate() calls are held and sent as ONE call per batch.
+
+A batch goes out when `size` mutation requests are pending, or `wait` seconds after the oldest pending one arrived. The
+call carries the shared system blocks (SYSTEM_BASE + MUTATE_TASK) once and every request's user prompt (as mutate_user
+renders it) as a numbered section; the reply has one "## Request <n>" section per request, each holding that request's
+```python block. Each caller gets its own section back as its reply and parses it exactly as a single reply, so a missing
+or malformed section fails only that child. Every other call (crossover by meaning, splits, ...) goes straight through.
+
+Per child the info dict adds batch id, batch size and position (cost = batch cost / size); per batch, a row in
+`log_path`: size, latency, tokens, cost, sections found.
+"""
+import json
+import re
+import threading
+import time
+
+from . import prompts
+from .claude import Claude
+
+BATCH_HEAD = """The genomes below are {k} INDEPENDENT mutation requests, each for a different genome. Handle each one on its own,
+exactly as if it were the only request: its own editable genes, link and fixed genes; nothing carries over between requests.
+
+Answer every request, in order. For request n write a line "## Request n" and then exactly one ```python block with that
+request's edited genes, in the format the task asks for. Nothing else is needed between sections."""
+
+SECTION = re.compile(r"^#{1,3}\s*Request\s+(\d+)\b.*$", re.M)
+
+
+def split_reply(text, k):
+    """{n: section text} for n in 1..k (missing sections are absent)."""
+    marks = list(SECTION.finditer(text or ""))
+    out = {}
+    for i, m in enumerate(marks):
+        n = int(m.group(1))
+        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
+        if 1 <= n <= k and n not in out:
+            out[n] = text[m.end():end]
+    return out
+
+
+class _Item:
+    def __init__(self, user):
+        self.user, self.t = user, time.time()
+        self.done = threading.Event()
+        self.result = self.error = None
+
+
+class BatchClaude(Claude):
+    def __init__(self, budget_usd, opus_every=10, size=8, wait=20.0, log_path=None, max_tokens=64000):
+        super().__init__(budget_usd, opus_every=opus_every, max_tokens=max_tokens)  # a cap only: room for k replies
+        self.size, self.wait, self.log_path = size, wait, log_path
+        self.pending, self.batches = [], 0
+        self.cv = threading.Condition()
+        threading.Thread(target=self._loop, daemon=True).start()
+
+    def ask(self, system, user, model=None):
+        if list(system) != [prompts.SYSTEM_BASE, prompts.MUTATE_TASK] or model is not None:
+            return super().ask(system, user, model)
+        it = _Item(user)
+        with self.cv:
+            self.pending.append(it)
+            self.cv.notify_all()
+        it.done.wait()
+        if it.error is not None:
+            raise it.error
+        return it.result
+
+    def _loop(self):
+        while True:
+            with self.cv:
+                while not (len(self.pending) >= self.size
+                           or (self.pending and time.time() - self.pending[0].t >= self.wait)):
+                    self.cv.wait(timeout=1.0)
+                batch, self.pending = self.pending[:self.size], self.pending[self.size:]
+                self.batches += 1
+                bid = self.batches
+            threading.Thread(target=self._send, args=(bid, batch), daemon=True).start()
+
+    def _send(self, bid, batch):
+        k = len(batch)
+        user = BATCH_HEAD.format(k=k) + "".join(f"\n\n======== Request {n} ========\n\n{it.user}"
+                                                 for n, it in enumerate(batch, 1))
+        row = {"batch": bid, "size": k, "t": round(time.time(), 1),
+               "waited": [round(time.time() - it.t, 1) for it in batch]}
+        try:
+            text, model, cost, info = super().ask([prompts.SYSTEM_BASE, prompts.MUTATE_TASK], user)
+        except Exception as e:  # BudgetExceeded or an API error: every child in the batch gets it
+            row["error"] = f"{type(e).__name__}: {str(e)[:200]}"
+            self._log(row)
+            for it in batch:
+                it.error = e
+                it.done.set()
+            return
+        parts = split_reply(text, k) if text is not None else {}
+        row.update({"model": model, "cost": round(cost, 5), "sections": len(parts), **info})
+        self._log(row)
+        for n, it in enumerate(batch, 1):
+            child_info = {**info, "batch": bid, "batch_size": k, "batch_pos": n, "batch_cost": round(cost, 5)}
+            reply = None if text is None else parts.get(n, "")
+            it.result = (reply, model, cost / k, child_info)
+            it.done.set()
+
+    def _log(self, row):
+        if self.log_path:
+            with self.cv:
+                with open(self.log_path, "a") as f:
+                    f.write(json.dumps(row) + "\n")
PATCH
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
git apply <<'PATCH' || exit 1
--- a/genome/search/arena.py
+++ b/genome/search/arena.py
@@ -315,7 +315,10 @@
             gs = self.genomes()
             ok = [m for m in gs if m["games"] >= self.a.min_games and not self.protected(m["species"])]
             strict = [m for m in ok if len(self.species_members(m["species"])) > self.a.min_species]
-            pool = strict or [m for m in ok if len(self.species_members(m["species"])) > 1] or ok
+            if self.a.cull == "legacy":
+                pool = strict or [m for m in ok if len(self.species_members(m["species"])) > 1] or ok
+            else:  # min-mu: if no species is above --min-species, the lowest-rated eligible genome dies
+                pool = strict or ok
             if not pool:
                 return  # everyone is new or protected: stay over capacity for now
             v = min(pool, key=lambda m: m["mu"])
@@ -626,6 +629,10 @@
     ap.add_argument("--min-games", type=int, default=40)
     ap.add_argument("--min-species", type=int, default=2)
     ap.add_argument("--protect-games", type=int, default=60)
+    ap.add_argument("--cull", choices=["legacy", "min-mu"], default="legacy",
+                    help="legacy: if no species is above --min-species, a genome of a species with more than one "
+                         "member dies (in practice the parent of a newborn of its own species); min-mu: the "
+                         "lowest-rated eligible genome dies")
     ap.add_argument("--species-delta", type=float, default=0.15)
     ap.add_argument("--tournament", type=int, default=3)
     ap.add_argument("--champion-every", type=int, default=50)
PATCH
git checkout -q 648bafd -- sim interp policygen genome/runtime genome/lang.py genome/build.py genome/tools genome/CMakeLists.txt || exit 1
cmake --build genome/build -j$THREADS --target genome_eval > $OUT/rebuild.log 2>&1 || exit 1
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --tag Z --seed genome/examples/starter.genome --anchors $OUT/starter.genome \
    --budget 20 --opus-every 1 --threads $THREADS --fixed-anchors --gate-every 100000000 \
    --batch-mutate 8 --batch-wait 20 --births-in-flight 8 --max-births 475 \
    --cull min-mu --rng-salt 0
