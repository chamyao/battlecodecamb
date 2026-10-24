"""Evolvability report from one or more runs of genome/search/run.py.

    python3 -m genome.search.report runs/evo-policy runs/evo-genome [--md out.md]

Per run and operator: children, invalid rate, behavioural twins, share beating the parent by a confirmed
margin (paired, confirm seed), crossover children beating both parents, spend and cost per confirmed
improvement (behavioural vs fuel-only gains when fuel10.py has run); and the edit-size breakdown (lines changed, edges per child).
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def load(run):
    progs = [json.loads(l) for l in open(Path(run) / "programs.jsonl")]
    return [p for p in progs if p["metrics"].get("op") not in ("seed", None) and p["model"] != "reset"]


def _share(k, n):
    if not n:
        return "-"
    se = math.sqrt(max(k, 0.5) * (n - k) / n) / n
    return f"{k}/{n} = {100 * k / n:.1f}% (±{100 * se:.1f})"


def rows(progs, beat_margin, fuel10=None):
    groups = defaultdict(list)
    for p in progs:
        groups[p["metrics"]["op"]].append(p)
    groups["all"] = progs
    out = []
    for op, ps in groups.items():
        n = len(ps)
        bad = sum(1 for p in ps if p["error"])
        valid = [p for p in ps if not p["error"]]
        twins = sum(1 for p in valid if p["metrics"].get("twin"))
        up = sum(1 for p in valid if p["metrics"].get("delta_screen", -1) > 0)
        beat = sum(1 for p in valid if p["metrics"].get("delta_confirm", -1) > beat_margin)
        two = [p for p in valid if len(p["metrics"].get("parent_ids", [])) == 2]
        both = sum(1 for p in two if p["metrics"].get("delta_confirm", -1) > beat_margin)
        cost = sum(p["metrics"].get("cost", 0.0) for p in ps)
        f10 = {}
        if fuel10 is not None:
            gains = [str(p["id"]) for p in valid if p["metrics"].get("delta_confirm", -1) > beat_margin]
            beh = sum(1 for i in gains if fuel10.get(i, {}).get("behavioural"))
            f10 = {"behavioural_gains": _share(beh, n), "fuel_only_gains": _share(len(gains) - beh, n),
                   "cost_per_behavioural_gain": f"${cost / beh:.2f}" if beh else "-"}
        out.append({"op": op, "children": n, "invalid": _share(bad, n), "twins": _share(twins, len(valid)),
                    "screen_up": _share(up, len(valid)), "beats_parent": _share(beat, n),
                    "two_parent_beats_both": _share(both, len(two)) if two else "-",
                    "cost": f"${cost:.2f}", "cost_per_gain": f"${cost / beat:.2f}" if beat else "-", **f10})
    return out


def size_rows(progs, beat_margin):
    bins = [(1, 2), (3, 5), (6, 10), (11, 20), (21, 40), (41, 10 ** 9)]
    out = []
    for lo, hi in bins:
        ps = [p for p in progs if lo <= (p["metrics"].get("log", {}).get("lines_changed") or 0) <= hi
              and p["metrics"]["op"] in ("mutate", "llm")]
        if not ps:
            continue
        valid = [p for p in ps if not p["error"]]
        beat = sum(1 for p in valid if p["metrics"].get("delta_confirm", -1) > beat_margin)
        ds = sorted(p["metrics"]["delta_screen"] for p in valid if "delta_screen" in p["metrics"])
        out.append({"lines": f"{lo}-{hi}" if hi < 10 ** 9 else f"{lo}+", "children": len(ps),
                    "beats_parent": _share(beat, len(valid)),
                    "median_screen_delta": f"{ds[len(ds) // 2]:+.3f}" if ds else "-"})
    for k in (1, 2):
        ps = [p for p in progs if p["metrics"].get("log", {}).get("n_edges") == k]
        if ps:
            valid = [p for p in ps if not p["error"]]
            beat = sum(1 for p in valid if p["metrics"].get("delta_confirm", -1) > beat_margin)
            out.append({"lines": f"{k} edge(s)", "children": len(ps), "beats_parent": _share(beat, len(valid)),
                        "invalid": _share(len(ps) - len(valid), len(ps))})
    return out


def table(rs):
    if not rs:
        return ""
    keys = list(dict.fromkeys(k for r in rs for k in r))
    lines = ["| " + " | ".join(keys) + " |", "|" + " --- |" * len(keys)]
    lines += ["| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rs]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--beat-margin", type=float, default=0.03)
    ap.add_argument("--md", default="")
    args = ap.parse_args()
    parts = []
    for run in args.runs:
        progs = load(run)
        all_progs = [json.loads(l) for l in open(Path(run) / "programs.jsonl")]
        seed = next(p for p in all_progs if p["metrics"].get("op") == "seed")
        best = max((p for p in all_progs if not p["error"] and "confirm" in p["metrics"]),
                   key=lambda p: p["metrics"]["confirm"])
        f10 = Path(run) / "fuel10.json"
        fuel10 = json.loads(f10.read_text()) if f10.exists() else None
        parts.append(f"## {Path(run).name}\n\nseed confirm {seed['metrics']['confirm']:.3f}; best confirmed "
                     f"#{best['id']} {best['metrics']['confirm']:.3f}\n\n{table(rows(progs, args.beat_margin, fuel10))}\n\n"
                     f"Edit size (Claude children):\n\n{table(size_rows(progs, args.beat_margin))}\n")
    text = "\n".join(parts)
    print(text)
    if args.md:
        Path(args.md).write_text(text)


if __name__ == "__main__":
    main()
