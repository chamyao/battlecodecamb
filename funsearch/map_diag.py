"""Per-map ablation (hooks/starvation diagnosis): which tune-line change matters on a map.

Variants from v7zg-cast: +draft (tune-1), +bag (bag 25 / hurt 0.3 on v7zg-cast), +gate, tune-2, tune-3.
Per pairing: win rate, our tributed gems, our deaths (and gems lost on death), elk deaths, our captures
and captured gems. GAME_EVENTS=1 logs; one thread so a game's events precede its details line.
usage: map_diag.py MAP [GAMES]"""
import json, os, subprocess, sys, collections
sys.path.insert(0, '.')
from funsearch.race import *
from funsearch.fuel_guard import guard

BAG = [("or health() < 0.5 * max_health()\n", "or health() < 0.3 * max_health()\n"), ("gems() >= 10 or", "gems() >= 25 or")]


def variants():
    v = open("policies/v7zg-cast.policy").read()
    bag = v
    for o, n in BAG:
        bag = bag.replace(o, n)
    t1 = open("policies/tune-1.policy").read()
    return {"v7zg-cast": v, "+draft(tune-1)": t1, "+bag": bag, "+gate": guard(v, 55000, "goal"),
            "tune-2": open("policies/tune-2.policy").read(), "tune-3": open("policies/tune-3.policy").read()}


def play(a_pol, b_pol, mp, games, seed, bot_seeds=False):
    env = dict(os.environ, GAME_EVENTS="1")
    out = subprocess.run([str(EVAL_BIN), "--a", a_pol, "--b", b_pol, "--games", str(games), "--threads", "1", "--seed",
                          str(seed), "--details", *(["--bot-seeds"] if bot_seeds else []), mp],
                         capture_output=True, text=True, env=env, timeout=7200).stdout.splitlines()
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
        agg["opp_gems"] += d["gems"][1 - us]
        for e in ev:
            f = dict(x.split("=", 1) for x in e.split()[2:] if "=" in x)
            kind = e.split()[2]
            if kind == "death" and f.get("team") == str(us):
                agg["deaths"] += 1
                agg["gems_lost"] += int(f.get("gems", 0))
                agg["deaths_by_camp"] += "camp" in e
                agg["deaths_by_champ"] += "by=champ" in e
            if kind == "capture" and f.get("team") == str(us):
                agg["captures"] += 1
                agg["captured_gems"] += int(f.get("gems", 0))
        ev = []
    n = max(1, agg["games"])
    return {k: round(agg[k] / n, 2) if k not in ("games",) else agg[k] for k in
            ("games", "wins", "gems", "opp_gems", "deaths", "gems_lost", "deaths_by_camp", "deaths_by_champ", "captures", "captured_gems")}


if __name__ == "__main__":
    mp = f"maps/{sys.argv[1]}.map26a"
    games = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    vs = variants()
    pols = {k: compile_text(t) for k, t in vs.items()}
    opps = {"v7zg-cast": pols["v7zg-cast"], "tune-3": pols["tune-3"], "opp-icecream": compile_file("policies/opp-icecream.policy")}
    log = open(f"runs/tune/mapdiag-{sys.argv[1]}.log", "a")
    for on, op in opps.items():
        for vn, vp in pols.items():
            r = play(vp, op, mp, games, 21)
            log.write(f"{vn} vs {on}: {json.dumps(r)}\n"); log.flush()
