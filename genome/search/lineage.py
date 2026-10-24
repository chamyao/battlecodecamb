"""Between-run analysis for an arena lineage, CPU only: panel scores of ancestors and of single-gene ablations.

    python3 -m genome.search.lineage --out lineage.jsonl --state arenaA-3/arena --ancestors A1,A3,... \
        --ablate A659,A711 --opponents p1,p2,... --threads 5

For each listed ancestor, and for each ablation (a genome with one gene, whose body differs from the seed's
version of the same gene ID, reverted to the seed's version), the 80 distinct games (40 maps x 2 sides, bot
seeds) vs each opponent. Ablations that do not type-check are logged (kind=ablation, error) and not played.
"""
import argparse
import json
import time
from pathlib import Path

from funsearch.evaluate import ROOT

from .. import lang
from . import edit
from .gate import rate, spec_of


def ablations(text, seed_text):
    """[(gene id, genome text with that gene reverted to the seed's, error or None)]."""
    _, _, seed_genes = edit.segments(seed_text)
    header, keeps, genes = edit.segments(text)
    out = []
    for gid, body in genes.items():
        if gid not in seed_genes or edit.body_canon(body) == edit.body_canon(seed_genes[gid]):
            continue
        variant = dict(genes)
        variant[gid] = seed_genes[gid]
        src = edit.assemble(header, keeps, variant)
        try:
            lang.parse(src)
            out.append((gid, src, None))
        except lang.GenomeError as e:
            out.append((gid, None, f"GenomeError: {e}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True, help="arena output dir holding the genomes (genomes/<name>.genome)")
    ap.add_argument("--ancestors", default="")
    ap.add_argument("--ablate", default="")
    ap.add_argument("--seed-genome", default=str(ROOT / "genome/seeds/v23.genome"))
    ap.add_argument("--opponents", action="append", required=True, help="comma list; repeatable")
    ap.add_argument("--threads", type=int, default=5)
    a = ap.parse_args()
    d = Path(a.state)
    opps = [o for part in a.opponents for o in part.split(",") if o]
    seed = Path(a.seed_genome).read_text()
    done = set()
    if Path(a.out).exists():
        done = {(r["genome"], r.get("opponent")) for r in map(json.loads, open(a.out))}
    specs = {o: spec_of(o if o.endswith(".genome") else str(ROOT / o)) for o in opps}

    def write(rec):
        with open(a.out, "a") as f:
            f.write(json.dumps({"t": round(time.time()), **rec}) + "\n")

    def play(name, text, meta):
        spec = spec_of(text, "genome")
        for o in opps:
            if (name, Path(o).stem) in done:
                continue
            w, n = rate(spec, specs[o], a.threads)
            write({"genome": name, "opponent": Path(o).stem, "wins": w, "games": n, **meta})
            print(name, Path(o).stem, w, n, flush=True)

    play("seed", seed, {"kind": "seed"})
    for name in filter(None, a.ancestors.split(",")):
        p = d / "genomes" / f"{name}.genome"
        if not p.exists():
            write({"genome": name, "kind": "ancestor", "error": "genome file missing"})
            continue
        play(name, p.read_text(), {"kind": "ancestor"})
    for name in filter(None, a.ablate.split(",")):
        text = (d / "genomes" / f"{name}.genome").read_text()
        play(name, text, {"kind": "ablation-base"})
        for gid, src, err in ablations(text, seed):
            tag = f"{name}-{gid}"
            if err:
                if (tag, None) not in done:
                    write({"genome": tag, "kind": "ablation", "base": name, "reverted": gid, "error": err})
                continue
            play(tag, src, {"kind": "ablation", "base": name, "reverted": gid})
    print("done", flush=True)


if __name__ == "__main__":
    main()
