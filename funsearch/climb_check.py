"""Does the per-child climb help? Re-score accepted climbs tuned vs untuned on fresh seeds.

    python3 -m funsearch.climb_check RUN_DIR [RUN_DIR ...] [--games 40] [--seed 5000011]

For every child whose metrics.tuned.changed is non-empty: rebuild the untuned child (from tuned.untuned_lines, or by
reversing each "old->new" change on its line when that is unambiguous), score both against the run's screen
opponents (as logged in its metrics) with `games` per opponent on a fresh seed, and print the difference. Also prints
the accept rate and whether accepted children were confirmed (metrics.confirmed) or validated at a boundary.
"""
import argparse
import json
import re
from pathlib import Path

from .evaluate import ROOT, evaluate
from .tune import literals

POOL = ROOT / "policies" / "pool"


def untuned_text(text, tuned):
    lines = text.split("\n")
    if tuned.get("untuned_lines"):
        for i, l in tuned["untuned_lines"].items():
            lines[int(i)] = l
        return "\n".join(lines)
    for key, ch in tuned["changed"].items():
        old, new = ch.split("->")
        if ":" in key and key.split(":", 1)[0].isdigit():
            ln = int(key.split(":", 1)[0])
            lits = [x for x in literals(text) if x["line"] == ln and x["value"] == new]
        else:
            lits = [x for x in literals(text) if x["name"] == key and x["value"] == new]
        if len(lits) != 1:
            return None  # ambiguous: cannot rebuild
        x = lits[0]
        text = text[: x["start"]] + old + text[x["end"]:]
    return text


def opponents_of(metrics):
    out = []
    for k, v in metrics.items():
        if not isinstance(v, dict) or "win_rate" not in v:
            continue
        if k.startswith("builtin:"):
            out.append(k)
        elif (POOL / f"{k}.policy").exists():
            out.append(str(POOL / f"{k}.policy"))
    return tuple(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--games", type=int, default=40, help="games per opponent per policy")
    ap.add_argument("--seed", type=int, default=5_000_011)
    ap.add_argument("--threads", type=int, default=8)
    args = ap.parse_args()
    for run in args.runs:
        path = Path(run) / "programs.jsonl" if Path(run).is_dir() else Path(run)
        rows = [json.loads(l) for l in open(path) if l.strip()]
        climbed = [r for r in rows if (r.get("metrics") or {}).get("tuned")]
        acc = [r for r in climbed if r["metrics"]["tuned"].get("changed")]
        print(f"== {path.parent.name}: {len(climbed)} climbed, {len(acc)} accepted "
              f"({len(acc) / max(1, len(climbed)):.0%})")
        diffs = []
        for r in acc:
            t, m = r["metrics"]["tuned"], r["metrics"]
            base = untuned_text(r["text"], t)
            conf = "confirmed" if m.get("confirmed") else "screen only"
            if base is None:
                print(f"  #{r['id']}: {t['changed']} (cannot rebuild the untuned child) {conf}")
                continue
            opps = opponents_of(m)
            a = evaluate(r["text"], opponents=opps, games=args.games, threads=args.threads, seed=args.seed)
            b = evaluate(base, opponents=opps, games=args.games, threads=args.threads, seed=args.seed)
            if not (a.ok and b.ok):
                print(f"  #{r['id']}: evaluation error {a.error or b.error}")
                continue
            diffs.append(a.score - b.score)
            print(f"  #{r['id']} {t['changed']}: climb games {t['before']:.3f} -> {t['after']:.3f}; fresh seed "
                  f"untuned {b.score:.3f} tuned {a.score:.3f} ({a.score - b.score:+.3f}, {args.games * len(opps)} games "
                  f"each); run score {r['score']:.3f} {conf}")
        if diffs:
            print(f"  mean fresh-seed gain {sum(diffs) / len(diffs):+.3f} over {len(diffs)} accepted climbs")


if __name__ == "__main__":
    main()
