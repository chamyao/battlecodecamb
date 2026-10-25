"""Learning curve of an arena from its panel files (panelwatch output): per milestone, the births and time at the snapshot,
the best and the mean of the top-3 panel scores, and births per hour since the previous snapshot.

    python3 -m genome.search.curve panelZ-1/panel.jsonl panelZ-1x/panel.jsonl [--out curve.json]

Several files are one curve in order (e.g. a run and its resumed continuation). Only fully played genomes count.
"""
import argparse
import collections
import json


def curve(paths):
    snaps, wins = {}, collections.defaultdict(lambda: [0, 0, 0])  # (milestone, genome) -> wins, games, opponents
    n_opp = 0
    for path in paths:
        for r in map(json.loads, open(path)):
            m = str(r["milestone"])
            if r.get("kind") == "snapshot":
                snaps[m] = {"births": r["births"], "t": r["t"], "genomes": [g["name"] for g in r["genomes"]]}
            elif r.get("kind") == "panel":
                w = wins[(m, r["genome"])]
                w[0] += r["wins"]
                w[1] += r["games"]
                w[2] += 1
    n_opp = max((w[2] for w in wins.values()), default=0)
    rows, prev = [], None
    for m, s in sorted(snaps.items(), key=lambda kv: kv[1]["births"]):
        done = [(wins[(m, g)][0], g) for g in s["genomes"] if wins[(m, g)][2] == n_opp]
        if not done:
            continue
        top = sorted(done, reverse=True)
        games = wins[(m, top[0][1])][1]
        row = {"milestone": m, "births": s["births"], "t": s["t"], "best": top[0][0], "best_genome": top[0][1],
               "mean_top3": round(sum(w for w, _ in top[:3]) / len(top[:3]), 1), "games": games,
               "complete": len(done) == len(s["genomes"])}
        if prev and s["t"] > prev["t"]:
            row["births_per_hour"] = round((s["births"] - prev["births"]) * 3600 / (s["t"] - prev["t"]), 1)
        rows.append(row)
        prev = row
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("panels", nargs="+")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    rows = curve(a.panels)
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rows, f, indent=1)
    for r in rows:
        print(f"m{r['milestone']:>6} births {r['births']:>5}  best {r['best']:>4}/{r['games']} ({r['best_genome']})  "
              f"top3 {r['mean_top3']:>6}  {r.get('births_per_hour', '')}{'' if r['complete'] else '  (partial)'}")


if __name__ == "__main__":
    main()
