"""One-at-a-time constant grid on a base policy (exact snippet replacement), screened vs the base."""
import json, sys
sys.path.insert(0, '.')
from funsearch.race import *
base_file, tag, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
base = open(base_file).read()
bpol = compile_text(base)
G = {
    "treasure": ("let treasure_n = floor( shards_bought / 2 )", ["let treasure_n = 0", "let treasure_n = floor( shards_bought / 4 )",
                 "let treasure_n = floor( shards_bought / 3 )", "let treasure_n = floor( 2 * shards_bought / 3 )", "let treasure_n = shards_bought"]),
    "jungle": ("let jungle_n = floor( rest_after_treasure / 3 )", ["let jungle_n = 0", "let jungle_n = floor( rest_after_treasure / 6 )",
               "let jungle_n = floor( rest_after_treasure / 2 )", "let jungle_n = rest_after_treasure"]),
    "strength": ("let strength_shards = floor( rest_after_jungle / 2 )", ["let strength_shards = 0", "let strength_shards = floor( rest_after_jungle / 3 )",
                 "let strength_shards = floor( 2 * rest_after_jungle / 3 )", "let strength_shards = rest_after_jungle"]),
    "retreat": ("health() < 0.3 * max_health():", [f"health() < {v} * max_health():" for v in (0.15, 0.2, 0.25, 0.35, 0.4, 0.5)]),
    "gemret": ("gems() > 0 and health() < 0.5 * max_health() and not in_danger()", [f"gems() > 0 and health() < {v} * max_health() and not in_danger()" for v in (0.3, 0.4, 0.6, 0.7)]),
    "bag": ("gems() >= 10 or", [f"gems() >= {v} or" for v in (1, 5, 7, 14, 20, 25, 30, 40, 60)]),
    "baground": ("round_number() > 1500", [f"round_number() > {v}" for v in (1000, 1250, 1750, 1900)]),
    "baghp": ("or health() < 0.5 * max_health()\n", [f"or health() < {v} * max_health()\n" for v in (0.3, 0.4, 0.6, 0.7)]),
    "dash": ("distance(position(), goal) > 4", [f"distance(position(), goal) > {v}" for v in (2, 3, 6, 8, 12, 1000)]),
    "monolith": ("ring(monolith_tiles(), 5)", [f"ring(monolith_tiles(), {v})" for v in (3, 4, 6, 7)]),
}
cands = {}
for k, (old, news) in G.items():
    assert base.count(old) == 1, (k, base.count(old))
    for n in news:
        cands[f"{k}={n.strip()}"] = base.replace(old, n)
print(len(cands), "candidates", flush=True)
log = open(f"runs/tune/screen-{tag}.log", "a")
def L(s):
    log.write(s + "\n"); log.flush()
res = screen(cands, bpol, games=200, seed=seed, log=L)
json.dump(res, open(f"runs/tune/screen-{tag}.json", "w"))
