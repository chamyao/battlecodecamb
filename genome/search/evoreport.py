"""Evolvability report for a strength run (genome/search/strength.py), rewritten at every round boundary.

Per operator arm (edge mutation with 1 / 2 edges, crossover by ID, crossover by meaning, constant
tuning) and per model: confirmed-improvement rate, cost per improvement, invalid rate, behavioural vs
fuel-only gains (fuel x10 re-score); success by edit size; which genes and edges improvements came
from; improvements per dollar per island and generation (to spot stalls).

    python3 -m genome.search.evoreport runs/strength1      # print the current report
"""
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path


def _share(k, n):
    if not n:
        return "-"
    se = math.sqrt(max(k, 0.5) * max(n - k, 0.5) / n) / n
    return f"{k}/{n} = {100 * k / n:.1f}% (±{100 * se:.1f})"


def load(out):
    progs = []
    for path in sorted(Path(out).glob("g*/programs.jsonl")):
        gen = int(path.parent.name[1:])
        seen = set()
        for line in open(path):
            p = json.loads(line)
            if p["id"] in seen or p["metrics"].get("op") in ("seed", None) or p["model"] == "reset":
                continue
            seen.add(p["id"])
            p["key"] = f"g{gen}#{p['id']}"
            progs.append(p)
    return progs


def group_rows(progs, keyf, fuel10, margin):
    groups = defaultdict(list)
    for p in progs:
        groups[keyf(p)].append(p)
    rows = []
    for k in sorted(groups):
        ps = groups[k]
        n = len(ps)
        valid = [p for p in ps if not p["error"]]
        gains = [p for p in valid if p["metrics"].get("delta_confirm", -1) > margin]
        beh = sum(1 for p in gains if fuel10.get(p["key"], {}).get("behavioural"))
        unchecked = sum(1 for p in gains if p["key"] not in fuel10)
        cost = sum(p["metrics"].get("cost", 0.0) for p in ps)
        rows.append({"group": k, "children": n, "invalid": _share(n - len(valid), n),
                     "twins": _share(sum(1 for p in valid if p["metrics"].get("twin")), len(valid)),
                     "improvements": _share(len(gains), n),
                     "behavioural": beh, "fuel_only": len(gains) - beh - unchecked,
                     "cost": f"${cost:.2f}", "cost/improvement": f"${cost / len(gains):.3f}" if gains else "-"})
    return rows


def table(rows):
    if not rows:
        return "(none)\n"
    keys = list(dict.fromkeys(k for r in rows for k in r))
    out = ["| " + " | ".join(keys) + " |", "|" + " --- |" * len(keys)]
    out += ["| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rows]
    return "\n".join(out) + "\n"


def size_bin(p):
    n = p["metrics"].get("log", {}).get("lines_changed") or 0
    for lo, hi in ((1, 2), (3, 5), (6, 10), (11, 20), (21, 40)):
        if lo <= n <= hi:
            return f"lines {lo:02d}-{hi}"
    return "lines 41+" if n > 40 else "lines 0 (invalid)"


def arm_op(p):
    m = p["metrics"]
    return m["op"] if m["arm"] == "cross" else m["arm"]


def render(out, state=None, bandit=None, margin=0.03):
    out = Path(out)
    state = state or json.loads((out / "state.json").read_text())
    progs = load(out)
    fuel10 = state.get("fuel10", {})
    spent = sum(p["metrics"].get("cost", 0.0) for p in progs)
    gains = [p for p in progs if not p["error"] and p["metrics"].get("delta_confirm", -1) > margin]
    s = [f"# Strength run {out.name}: {time.strftime('%Y-%m-%d %H:%M')}\n",
         f"{len(progs)} children, {len(gains)} confirmed improvements (> {margin} paired, confirm seed), "
         f"spent ${spent:.2f}. Generation {state['gen']}, best `{Path(state['best']).name}`, "
         f"promotions: {len(state['promoted'])}.\n"]
    if bandit is not None:
        s.append(f"Operator mix now (Thompson + floor): {bandit.shares()}; children {bandit.n}; gains {bandit.g}\n")
    for b in state.get("boundaries", [])[-5:]:
        if b.get("promoted"):
            s.append(f"- boundary g{b['gen']} at {b['programs']} programs: promoted {b['promoted']} "
                     f"(h2h {b['h2h']:.3f}, pool deltas {b['drops']})")
    s.append("\n## Per operator\n" + table(group_rows(progs, arm_op, fuel10, margin)))
    s.append("## Per operator and model\n" + table(group_rows(
        [p for p in progs if p["metrics"].get("model")], lambda p: f"{arm_op(p)} / {p['metrics']['model']}",
        fuel10, margin)))
    llm = [p for p in progs if p["metrics"]["arm"] in ("mutate1", "mutate2")]
    s.append("## Edge mutation by size\n" + table(group_rows(llm, size_bin, fuel10, margin)))
    s.append("## Edge mutation by genes changed / new genes\n" + table(group_rows(
        llm, lambda p: f"changed {len(p['metrics']['log'].get('genes_changed', []))}, "
                       f"new {min(2, len(p['metrics']['log'].get('genes_added', [])))}{'+' if len(p['metrics']['log'].get('genes_added', [])) >= 2 else ''}",
        fuel10, margin)))
    genes, edges = Counter(), Counter()
    for p in gains:
        lg = p["metrics"].get("log", {})
        genes.update(lg.get("genes_changed", []))
        genes.update(["(new genes)"] * len(lg.get("genes_added", [])))
        for e in lg.get("edges", []):
            edges[f"{e[0]} -> {e[1]} ({e[2]})"] += 1
        for c in lg.get("changes", []):
            genes[f"constant line {c[0]}"] += 1
    s.append("## Where improvements came from\nGenes (IDs): " + (", ".join(f"{g} x{n}" for g, n in genes.most_common(15)) or "-")
             + "\n\nEdges: " + (", ".join(f"{e} x{n}" for e, n in edges.most_common(15)) or "-") + "\n")
    rows = []
    per = defaultdict(list)
    for p in progs:
        per[(p["metrics"]["gen"], p["metrics"]["island"])].append(p)
    for (g, i), ps in sorted(per.items()):
        k = sum(1 for p in ps if not p["error"] and p["metrics"].get("delta_confirm", -1) > margin)
        c = sum(p["metrics"].get("cost", 0.0) for p in ps)
        half = ps[len(ps) // 2:]
        k2 = sum(1 for p in half if not p["error"] and p["metrics"].get("delta_confirm", -1) > margin)
        c2 = sum(p["metrics"].get("cost", 0.0) for p in half)
        rows.append({"gen": g, "island": i, "children": len(ps), "improvements": k, "cost": f"${c:.2f}",
                     "per 100 children": f"{100 * k / len(ps):.1f}",
                     "per 100 (recent half)": f"{100 * k2 / max(1, len(half)):.1f}",
                     "per $": f"{k / c:.1f}" if c else "-", "per $ (recent half)": f"{k2 / c2:.1f}" if c2 else "-"})
    s.append("## Improvements per dollar, per generation and island\n" + table(rows))
    return "\n".join(s)


def write(out, state, bandit, margin):
    text = render(out, state, bandit, margin)
    (Path(out) / "report.md").write_text(text)
    rep = Path(out) / "reports"
    rep.mkdir(exist_ok=True)
    (rep / f"b{len(state.get('boundaries', [])):03d}.md").write_text(text)


if __name__ == "__main__":
    print(render(sys.argv[1]))
