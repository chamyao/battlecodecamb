"""Held-out panel for a running arena, CPU only: every --every births, the current top --top genomes vs fixed opponents
(never in the arena), 80 distinct games each (40 maps x 2 sides, bot seeds).

    python3 -m genome.search.panelwatch --out panel.jsonl --state <arena out dir> --opponents p1,p2,... \
        [--every 100] [--top 3] [--threads 5] [--until <file>]

Milestone 0 is the seed (or, with --after-births B for a resumed arena, the first milestone is the first multiple
of --every above B). A milestone's genomes are snapshotted (name, mu, sigma, games, text) when the arena reaches
it and played afterwards, so a slow panel never mixes generations. Stops when --until exists and every reached
milestone is played.
"""
import argparse
import json
import time
from pathlib import Path

from funsearch.evaluate import ROOT

from .gate import rate, spec_of


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--opponents", action="append", required=True, help="comma list; repeatable")
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--until", default="", help="stop once this file exists (e.g. the arena job's rc)")
    ap.add_argument("--poll", type=float, default=60)
    ap.add_argument("--after-births", type=int, default=-1,
                    help="a resumed arena: only milestones after this many births (no milestone 0)")
    a = ap.parse_args()
    d, out = Path(a.state), Path(a.out)
    snap_dir = out.parent / "panel-genomes"
    snap_dir.mkdir(parents=True, exist_ok=True)
    opps = [o for part in a.opponents for o in part.split(",") if o]
    specs = {Path(o).stem: spec_of(o if o.endswith(".genome") else str(ROOT / o)) for o in opps}
    done, snaps = set(), {}
    if out.exists():
        for r in map(json.loads, open(out)):
            if r.get("kind") == "snapshot":
                snaps[r["milestone"]] = r["genomes"]
            else:
                done.add((r["milestone"], r["genome"], r["opponent"]))

    def write(rec):
        with open(out, "a") as f:
            f.write(json.dumps({"t": round(time.time()), **rec}) + "\n")

    while True:
        finished = bool(a.until) and Path(a.until).exists()
        sp = d / "state.json"
        if sp.exists():
            s = json.loads(sp.read_text())
            k = s["births"] // a.every
            for m in range(k + 1):
                if m in snaps or m * a.every <= a.after_births:
                    continue
                if m < k and m > 0:
                    continue  # passed while we were not watching: only the latest reached milestone is snapshotted
                gen = [x for x in s["members"].values() if x["kind"] == "genome"]
                live = [x for x in gen if x.get("alive", True)]
                if m == 0:  # the seed, alive or not
                    top = [x for x in gen if x.get("parents") == []][:1] or sorted(gen, key=lambda x: x["born"])[:1]
                else:
                    top = sorted(live, key=lambda x: -x["mu"])[:a.top]
                gs = []
                for x in top:
                    p = snap_dir / f"m{m}-{x['name']}.genome"
                    p.write_text((d / x["path"]).read_text())
                    gs.append({"name": x["name"], "mu": round(x["mu"], 2), "sigma": round(x["sigma"], 2),
                               "games": x["games"], "file": p.name})
                snaps[m] = gs
                write({"kind": "snapshot", "milestone": m, "births": s["births"], "genomes": gs})
                print(f"milestone {m} (births {s['births']}): {[g['name'] for g in gs]}", flush=True)
        todo = [(m, g, o) for m in sorted(snaps) for g in snaps[m] for o in specs
                if (m, g["name"], o) not in done]
        for m, g, o in todo:
            gspec = spec_of((snap_dir / g["file"]).read_text(), "genome")
            w, n = rate(gspec, specs[o], a.threads)
            done.add((m, g["name"], o))
            write({"kind": "panel", "milestone": m, "genome": g["name"], "mu": g["mu"], "opponent": o,
                   "wins": w, "games": n})
            print(m, g["name"], o, w, n, flush=True)
            if not finished:
                break  # re-read the state between matches so a milestone is snapshotted when it is reached
        if finished and not todo:
            break
        if not todo:
            time.sleep(a.poll)
    print("done", flush=True)


if __name__ == "__main__":
    main()
