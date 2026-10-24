"""Diversity and per-variant report for a run (exploration mode or not).

    python3 -m funsearch.explore_report RUN [RUN ...]

Overall: programs, validity, distinct drafts (first two picks), block coverage, behaviour cells filled,
best score. Per prompt-variant value (exploration runs): calls, validity, mean/max score, and novelty:
the share of children that open a new behaviour cell, use a block none of their parents use, or bring
a draft core not seen before in the run.
"""
import json
import re
import sys
from collections import defaultdict

from policygen.blocks import REGISTRY

from .database import cell_of, draft_core
from .evaluate import ROOT, refresh_exec_blocks

NAMES = {b.name for b in REGISTRY if not b.infix}
# recently added blocks whose uptake we track (gap sensors, capture metric, ability/unit info)
WATCH = [b for b in ("unit_max_health", "unit_strength", "unit_focus", "enemies_near", "allies_near", "strength_at",
                     "unit_tributing", "unit_is", "unit_shield", "slot_stun", "slot_range", "slot_radius",
                     "threat_eta", "altar_eta", "retreat_eta", "enemy_between", "group_contested", "team_gems",
                     "unseen_enemies_near", "bank_detour", "group_rate") if b in NAMES]


def blocks_used(text):
    return {n for n in re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", text) if n in NAMES}


def exec_blocks_of(run, rows, valid):
    """Executed blocks (vs builtin:starter) per valid program: from metrics when measured vs starter, else
    from (or computed into) runs/<run>/exec_blocks_v2.json, the cache funsearch.run also uses."""
    got = refresh_exec_blocks(valid, ROOT / "runs" / run / "exec_blocks_v2.json")
    return {k: set(v) for k, v in got.items()}


def yield_vs(metrics, ref_name):
    """(our gems per capture - ref's, our win rate) in the screen games against ref_name: both sides' yield is
    measured in the same games, so no seed baseline is needed. None when not logged."""
    m = (metrics or {}).get(ref_name)
    if not isinstance(m, dict) or "captures" not in m or not m["captures"][0] or not m["captures"][1]:
        return None
    ours = m["gems_captured"][0] / m["captures"][0]
    theirs = m["gems_captured"][1] / m["captures"][1]
    return ours - theirs, ours, theirs, m["win_rate"]


def yield_report(rows, valid, ref_name="v21", top=8, flag_delta=1.0):
    """Capture yield next to the score: top children by score with gems per capture against ref_name in the same
    games (child vs ref), and a FLAG for any child at >= ref + flag_delta while winning >= 50% vs ref_name."""
    kids = [r for r in valid if r["model"] not in ("seed", "reset") and yield_vs(r["metrics"], ref_name)]
    if not kids:
        print("  yield: not logged yet (needs the capture metrics build)")
        return
    line = []
    for r in sorted(kids, key=lambda r: -r["score"])[:top]:
        d, ours, theirs, w = yield_vs(r["metrics"], ref_name)
        m = r["metrics"][ref_name]
        line.append(f"#{r['id']} {r['score']:.3f} submitted {m['a_gems'] - m['b_gems']:+.0f}/game gpc {ours:.1f} vs "
                    f"{theirs:.1f} ({d:+.1f}) win {w:.0%}")
    print(f"  yield vs {ref_name} (gems per capture, child vs {ref_name} in the same games; top by score): " +
          "  ".join(line))
    best = max(kids, key=lambda r: yield_vs(r["metrics"], ref_name)[0])
    d, ours, theirs, w = yield_vs(best["metrics"], ref_name)
    print(f"  yield best: #{best['id']} gpc {ours:.1f} vs {theirs:.1f} ({d:+.1f}), win {w:.0%}, score {best['score']:.3f}")
    for r in kids:
        d, ours, theirs, w = yield_vs(r["metrics"], ref_name)
        if d >= flag_delta and w >= 0.5:
            print(f"  FLAG yield: #{r['id']} gems per capture {ours:.1f} vs {ref_name} {theirs:.1f} ({d:+.1f}) with "
                  f"{w:.0%} vs {ref_name} (score {r['score']:.3f})")


def report(run, step=25):
    rows = [json.loads(line) for line in open(ROOT / "runs" / run / "programs.jsonl")]
    by_id = {r["id"]: r for r in rows}
    valid = [r for r in rows if r["error"] is None and r["score"] is not None and r["score"] > float("-inf")]
    cells, drafts, used = set(), set(), set()
    per = defaultdict(lambda: defaultdict(lambda: dict(n=0, ok=0, scores=[], new_cell=0, new_block=0, new_draft=0)))
    for r in rows:
        ok = r in valid
        cell = cell_of(r["text"], r["metrics"]) if ok else None
        draft = draft_core(r["text"]) if ok else None
        blocks = blocks_used(r["text"]) if ok else set()
        parent_blocks = set().union(*(blocks_used(by_id[p]["text"]) for p in r["parents"] if p in by_id)) if r["parents"] else set()
        flags = dict(new_cell=ok and cell not in cells, new_block=ok and bool(r["parents"]) and bool(blocks - parent_blocks),
                     new_draft=ok and draft not in drafts)
        variant = r["metrics"].get("variant") or {}
        if r["model"] not in ("seed", "reset") and not r["model"].startswith("inject"):
            keys = [("all", "all"), ("model", r["model"])] + [(k, str(v)) for k, v in variant.items()]
            for dim, val in keys:
                s = per[dim][val]
                s["n"] += 1
                s["ok"] += ok
                if ok:
                    s["scores"].append(r["score"])
                for f, v in flags.items():
                    s[f] += bool(v)
        if ok:
            cells.add(cell)
            drafts.add(draft)
            used |= blocks
    best = max(valid, key=lambda r: r["score"]) if valid else None
    execd = exec_blocks_of(run, rows, valid)
    executed = set().union(*execd.values()) if execd else set()
    spend = sum(r["metrics"].get("cost", 0) for r in rows)
    print(f"== {run}: {len(rows)} programs, {len(valid)} valid, ${spend:.2f}; distinct drafts {len(drafts)}; "
          f"blocks present {len(used)}/{len(NAMES)}, EXECUTED {len(executed)}/{len(NAMES)}; behaviour cells "
          f"{len(cells)}; best {best['score']:.3f} (#{best['id']})" if best else f"== {run}: no valid programs")
    # curves by program index: best score so far and executed-block coverage so far
    curve, seen, top = [], set(), float("-inf")
    for r in rows:
        if r in valid:
            top = max(top, r["score"])
            seen |= execd.get(r["id"], set())
        if r["id"] % step == step - 1 or r is rows[-1]:
            curve.append(f"{r['id'] + 1}:{top:.3f}/{len(seen)}")
    print("  curve (programs:best/executed blocks): " + "  ".join(curve))
    # newly added blocks: are children picking them up? (contained in the text / executed in play)
    kids = [r for r in valid if r["model"] not in ("seed", "reset") and not r["model"].startswith("inject")]
    watch_line = []
    for b in WATCH:
        present = sum(1 for r in kids if re.search(rf"\b{b}\(", r["text"]))
        executed = sum(1 for r in kids if b in execd.get(r["id"], set()))
        watch_line.append(f"{b} {executed}/{present}")
    print(f"  new blocks, children executing/containing (of {len(kids)}): " + ", ".join(watch_line))
    # uptake over time, split by whether the prompt listed the new blocks (vocab variant)
    def uptake(rs):
        if not rs:
            return "-"
        has = sum(1 for r in rs if any(re.search(rf"\b{b}\(", r["text"]) for b in WATCH))
        ran = sum(1 for r in rs if execd.get(r["id"], set()) & set(WATCH))
        return f"{ran}/{has}/{len(rs)}"
    seg = []
    for lo in range(0, (rows[-1]["id"] + 1) if rows else 0, 2 * step):
        part = [r for r in kids if lo <= r["id"] < lo + 2 * step]
        voc = [r for r in part if (r["metrics"].get("variant") or {}).get("vocab")]
        seg.append(f"{lo}-{lo + 2 * step - 1}: vocab {uptake(voc)} other {uptake([r for r in part if r not in voc])}")
    print("  new-block uptake by programs (executing/containing/valid children): " + "  ".join(seg))
    yield_report(rows, valid)
    for dim in per:
        print(f"  {dim}:")
        for val, s in sorted(per[dim].items(), key=lambda kv: -kv[1]["n"]):
            sc = s["scores"]
            mean = f"{sum(sc) / len(sc):.3f}" if sc else "-"
            top = f"{max(sc):.3f}" if sc else "-"
            print(f"    {val:<14} n {s['n']:>3}  valid {s['ok'] / s['n']:4.0%}  mean {mean}  max {top}  "
                  f"new cell {s['new_cell'] / s['n']:4.0%}  new block {s['new_block'] / s['n']:4.0%}  "
                  f"new draft {s['new_draft'] / s['n']:4.0%}")
    return dict(drafts=len(drafts), blocks=len(used), executed=len(executed), cells=len(cells),
                best=best["score"] if best else None)


if __name__ == "__main__":
    for run in sys.argv[1:]:
        report(run)
