# rev: 681e2e3a90741660b8a8b51e2c0609461f6fddff
# Arena B with FIXED anchor ratings (Cham): resumes arenaB-1 once it has exited (rc), anchors frozen at their current
# mu; same rev (runtime genome/v0 46f8c7a) and settings otherwise; --budget is the arena's total cap ($8; spend so
# far restored from the copied children.jsonl). The fixed-anchor patch (same change as genome/search b7ab83f) is applied
# inline below, so nothing else differs from the running code.
while [ ! -f "$OUT/../arenaB-1/rc" ]; do sleep 60; done
echo "arenaB-1 exited rc=$(cat "$OUT/../arenaB-1/rc"); resuming with fixed anchors"
python3 - <<'PYEOF'
# Patch genome/search/arena.py: anchors with fixed ratings (only the genome learns from a game vs an anchor).
p = "genome/search/arena.py"
s = open(p).read()
def sub(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
sub('''            for r in st.get("results", []):
                if r > 0.5:
                    rate_game(a, b)
                elif r < 0.5:
                    rate_game(b, a)
''', '''            for r in st.get("results", []):
                if r == 0.5:
                    continue
                w_, l_ = (a, b) if r > 0.5 else (b, a)
                keep = [(m["mu"], m["sigma"]) for m in (w_, l_)]
                rate_game(w_, l_)
                if self.a.fixed_anchors:  # anchors keep fixed ratings: only the genome learns from the game
                    for m, (mu, sg) in zip((w_, l_), keep):
                        if m["kind"] == "anchor":
                            m["mu"], m["sigma"] = mu, sg
''')
sub('''        if rating:
            m["mu"], m["sigma"] = rating
''', '''        if rating:
            m["mu"], m["sigma"] = rating
        if self.a.fixed_anchors:
            m["sigma"] = self.a.anchor_sigma
''')
sub('''        self.rng = random.Random(''', '''        if args.fixed_anchors:  # freeze every anchor at its current mu (keeps the scale, fixed from here on)
            for m in self.anchors():
                m["sigma"] = args.anchor_sigma
            self.log("fixed anchors: " + ", ".join(f"{m['name']} {m['mu']:.2f}" for m in self.anchors()))
        self.rng = random.Random(''')
sub('''    ap.add_argument("--intel-branch", default="")''', '''    ap.add_argument("--fixed-anchors", action="store_true", default=FIXED_DEFAULT,
                    help="anchors keep fixed ratings (frozen at their current mu on resume)")
    ap.add_argument("--anchor-sigma", type=float, default=1.0)
    ap.add_argument("--intel-branch", default="")''')
sub('''MU0, SIGMA0 = 25.0, 25.0 / 3''', '''MU0, SIGMA0 = 25.0, 25.0 / 3
FIXED_DEFAULT = False''')
open(p, "w").write(s)
PYEOF
python3 -c "import anthropic" 2>/dev/null || pip install -q anthropic
python3 -m genome.search.arena --out $OUT/arena --resume-from "$OUT/../arenaB-1/arena" --tag B --seed genome/seeds/v23.genome --budget 8 --threads $THREADS --fixed-anchors --intel-branch genome/intel
