"""TOP_TEAMS metrics (docs/TOP_TEAMS.md on analysis/sprint1) from GAME_EVENTS: per game for policy A, deaths, deaths to
champions, kills of enemy champions, gems lost dying, recalls started, recalls cut by damage, and deaths within 5
rounds of a recall start (mid-recall deaths; 23% of tune-5's ladder deaths to the top teams).
usage as a module: metrics(a_pol, b_pol, maps, games, seed) -> dict"""
import collections, json, os, subprocess, sys
sys.path.insert(0, '.')
from funsearch.race import *


def metrics(a_pol, b_pol, maps=None, games=80, seed=1, threads=4):
    env = dict(os.environ, GAME_EVENTS="1")
    out = subprocess.run([str(EVAL_BIN), "--a", a_pol, "--b", b_pol, "--games", str(games), "--threads", "1", "--seed",
                          str(seed), "--details", *(maps or MAPS)], capture_output=True, text=True, env=env,
                         timeout=7200).stdout.splitlines()
    agg = collections.Counter()
    ev = []
    for l in out:
        if l.startswith("@@EV"):
            ev.append(l)
            continue
        if not l.startswith('{"game"'):
            continue
        d = json.loads(l)
        us = 0 if d["a_side"] == "A" else 1
        agg["games"] += 1
        agg["wins"] += d["winner"] == us
        agg["gems"] += d["gems"][us]
        last_recall = {}
        for e in ev:
            p = e.split()
            r = int(p[1][2:])
            kind = p[2]
            f = dict(x.split("=", 1) for x in p[3:] if "=" in x)
            if kind == "recall" and f["team"] == str(us):
                agg["recalls"] += 1
                last_recall[f["champ"]] = r
            elif kind == "recallcut" and f["team"] == str(us):
                agg["recall_cut"] += 1
            elif kind == "death":
                if f["team"] == str(us):
                    agg["deaths"] += 1
                    agg["gems_lost"] += int(f["gems"])
                    if "by=champ" in e:
                        agg["deaths_champ"] += 1
                        if r - last_recall.get(f["champ"], -99) <= 5:
                            agg["mid_recall_deaths"] += 1
                elif "by=champ" in e:
                    agg["kills"] += 1
        ev = []
    n = max(1, agg["games"])
    res = {k: round(agg[k] / n, 2) for k in ("wins", "gems", "deaths", "deaths_champ", "kills", "gems_lost", "recalls", "recall_cut", "mid_recall_deaths")}
    res["games"] = agg["games"]
    return res


if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    print(json.dumps(metrics(compile_file(a), compile_file(b), games=int(sys.argv[3]) if len(sys.argv) > 3 else 80)))
