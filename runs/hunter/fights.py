# Per-fight signal (style line): segment sim games into engagements from GAME_EVENTS champion hits and deaths.
# usage: fights.py A.policy B.policy [games] [seed] [--json]   (A's view)
# An engagement is a run of champion-on-champion hits, each within GAP rounds of the engagement's last hit and
# within RADIUS tiles (Chebyshev) of its last hit position. Champion deaths join the engagement they happen in.
# Per engagement: damage dealt / taken, champions involved per side, deaths, and deaths while outnumbered
# (the victim's side had fewer champions involved). Score per engagement = (dealt - taken) / (dealt + taken).
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from policygen.compile import to_prefix  # noqa: E402
from policygen.text import parse  # noqa: E402
from funsearch.evaluate import EVAL_BIN, MAPS  # noqa: E402

GAP, RADIUS = 10, 8


def comp(p):
    if p.startswith("builtin:"):
        return p
    fd, out = tempfile.mkstemp(suffix=".pol")
    os.write(fd, to_prefix(parse(open(p).read())).encode())
    os.close(fd)
    return out


def kv(parts):
    return dict(x.split("=", 1) for x in parts if "=" in x)


def segment(events, us):
    """events: parsed @@EV lines of one game; us: A's team id. Returns a list of engagement dicts."""
    open_, done = [], []
    for r, kind, f, raw in events:
        if kind == "chit":
            x, y = map(int, f["pos"].split(","))
            eng = None
            for e in open_:
                if r - e["last"] <= GAP and max(abs(x - e["x"]), abs(y - e["y"])) <= RADIUS:
                    eng = e
                    break
            if eng is None:
                eng = {"start": r, "last": r, "x": x, "y": y, "dealt": 0.0, "taken": 0.0, "ours": set(), "theirs": set(),
                       "our_deaths": 0, "their_deaths": 0, "our_out_deaths": 0, "their_out_deaths": 0}
                open_.append(eng)
            eng["last"], eng["x"], eng["y"] = r, x, y
            src, dst, dmg = int(f["src"]), int(f["dst"]), float(f["dmg"])
            if int(f["team"]) == us:
                eng["dealt"] += dmg
                eng["ours"].add(src)
                eng["theirs"].add(dst)
            else:
                eng["taken"] += dmg
                eng["theirs"].add(src)
                eng["ours"].add(dst)
        elif kind == "death" and "by=champ" in raw:
            x, y = map(int, f["pos"].split(","))
            for e in open_:
                if r - e["last"] <= GAP and max(abs(x - e["x"]), abs(y - e["y"])) <= RADIUS:
                    mine = int(f["team"]) == us
                    side, other = ("ours", "theirs") if mine else ("theirs", "ours")
                    out = len(e[side]) < len(e[other])
                    if mine:
                        e["our_deaths"] += 1
                        e["our_out_deaths"] += out
                    else:
                        e["their_deaths"] += 1
                        e["their_out_deaths"] += out
                    break
        still = []
        for e in open_:
            (still if r - e["last"] <= GAP else done).append(e)
        open_ = still
    return done + open_


def run(a, b, games=80, seed=1):
    env = dict(os.environ, GAME_EVENTS="1")
    out = subprocess.run([str(EVAL_BIN), "--a", comp(a), "--b", comp(b), "--games", str(games), "--threads", "1",
                          "--seed", str(seed), "--details", *MAPS], capture_output=True, text=True, env=env,
                         timeout=7200).stdout.splitlines()
    engs, games_n, wins, ev = [], 0, 0, []
    for line in out:
        if line.startswith("@@EV"):
            p = line.split()
            ev.append((int(p[1][2:]), p[2], kv(p[3:]), line))
            continue
        if not line.startswith('{"game"'):
            continue
        d = json.loads(line)
        us = 0 if d["a_side"] == "A" else 1
        games_n += 1
        wins += d["winner"] == us
        engs += segment(ev, us)
        ev = []
    n = max(1, games_n)
    big = [e for e in engs if e["dealt"] + e["taken"] >= 200]  # ignore stray pokes
    m = max(1, len(big))
    score = sum((e["dealt"] - e["taken"]) / (e["dealt"] + e["taken"]) for e in big) / m
    res = {
        "games": games_n, "win": round(wins / n, 3),
        "engagements_per_game": round(len(big) / n, 2),
        "fight_score": round(score, 3),  # mean per-engagement damage margin, -1..1
        "fights_won": round(sum(e["dealt"] > e["taken"] for e in big) / m, 3),
        "dealt_per_fight": round(sum(e["dealt"] for e in big) / m), "taken_per_fight": round(sum(e["taken"] for e in big) / m),
        "our_deaths_pg": round(sum(e["our_deaths"] for e in engs) / n, 2),
        "their_deaths_pg": round(sum(e["their_deaths"] for e in engs) / n, 2),
        "our_outnumbered_deaths_pg": round(sum(e["our_out_deaths"] for e in engs) / n, 2),
        "their_outnumbered_deaths_pg": round(sum(e["their_out_deaths"] for e in engs) / n, 2),
        "our_out_death_share": round(sum(e["our_out_deaths"] for e in engs) / max(1, sum(e["our_deaths"] for e in engs)), 3),
    }
    return res


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = run(args[0], args[1], int(args[2]) if len(args) > 2 else 80, int(args[3]) if len(args) > 3 else 1)
    print(json.dumps(r) if "--json" in sys.argv else f"{Path(args[0]).name} vs {Path(args[1]).name}: {r}")
