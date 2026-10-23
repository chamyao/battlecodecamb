"""Deduplicated summary of the block proposals (# PROPOSE: lines) a run's replies made.

    python3 -m funsearch.proposals long2 [more runs...]
"""
import collections
import json
import re
import sys

from .evaluate import ROOT


def main():
    groups = collections.defaultdict(list)
    for run in sys.argv[1:]:
        try:
            lines = open(ROOT / "runs" / run / "proposals.jsonl").read().splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            r = json.loads(line)
            name = re.match(r"\s*(\w+)", r["proposal"])
            groups[name.group(1) if name else r["proposal"]].append(r)
    for name, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        scores = [r["score"] for r in rs if r["score"] is not None]
        best = f", best program score {max(scores):.3f}" if scores else ""
        print(f"{name}: {len(rs)}x{best}")
        for text in list(dict.fromkeys(r["proposal"] for r in rs))[:3]:
            print(f"    {text[:200]}")


if __name__ == "__main__":
    main()
