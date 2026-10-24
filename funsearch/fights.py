"""Per-fight statistics from the simulator's GAME_EVENTS stream (style line).

An engagement is a run of champion-on-champion hits ("@@EV chit"), each within GAP rounds of the engagement's last
hit and within RADIUS tiles (Chebyshev) of its last hit position; champion deaths join the engagement they happen
in. play(a, b, ...) plays compiled policies with events on and returns A's-view statistics per game and summed,
including the TOP_TEAMS-style signature terms (kills, deaths, champion damage, outnumbered-death share,
first-kill round) used by funsearch/fit.py.
"""
import json
import os
import statistics
import subprocess

from .evaluate import EVAL_BIN, MAPS

GAP, RADIUS = 10, 8
MIN_FIGHT_DAMAGE = 200  # engagements below this total are stray pokes, ignored in per-fight averages


def _kv(parts):
    return dict(x.split("=", 1) for x in parts if "=" in x)


def segment(events, us):
    """events: (round, kind, fields, raw) for one game; us: A's team id. Returns the game's engagements."""
    open_, done = [], []
    for r, kind, f, raw in events:
        if kind == "chit":
            x, y = map(int, f["pos"].split(","))
            eng = next((e for e in open_ if r - e["last"] <= GAP and max(abs(x - e["x"]), abs(y - e["y"])) <= RADIUS),
                       None)
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


LOW_HP, LOW_HP_RANGE, LOW_HP_WINDOW = 0.5, 5, 15  # as analysis/low_hp.py (crossings, 15 rounds)


def low_hp_episodes(events, team):
    """Low-HP crossings of `team`'s champions (analysis/low_hp.py's definition, from hit events): an enemy
    champion hit from within LOW_HP_RANGE tiles takes the champion from >= LOW_HP of max health to below it; the
    episode counts as a death if the champion dies within LOW_HP_WINDOW rounds. Returns (episodes, deaths)."""
    open_ep, episodes, deaths = {}, 0, 0
    for r, kind, f, raw in events:
        for c, start in list(open_ep.items()):
            if r - start > LOW_HP_WINDOW:
                del open_ep[c]
        if kind == "chit" and int(f["team"]) != team and "hp" in f:
            dst = int(f["dst"])
            x, y = map(int, f["pos"].split(","))
            sx, sy = map(int, f["spos"].split(","))
            hp, mx = float(f["hp"]), float(f["max"])
            crossed = hp + float(f["dmg"]) >= LOW_HP * mx > hp  # this hit took it from >= half health to below
            if dst not in open_ep and hp > 0 and crossed and max(abs(x - sx), abs(y - sy)) <= LOW_HP_RANGE:
                open_ep[dst] = r
                episodes += 1
        elif kind == "death" and int(f["team"]) == team:
            c = int(f["champ"])
            if c in open_ep:
                deaths += 1
                del open_ep[c]
    return episodes, deaths


def play(a_pol, b_pol, games=40, seed=1, maps=None, timeout=3600):
    """A and B are compiled .pol paths (or builtin:...). One interp_eval process, single-threaded (event lines of
    parallel games would interleave). Returns {"games": [per-game dicts], "summary": {...}} from A's view."""
    env = dict(os.environ, GAME_EVENTS="1")
    out = subprocess.run([str(EVAL_BIN), "--a", a_pol, "--b", b_pol, "--games", str(games), "--threads", "1",
                          "--seed", str(seed), "--details", *(maps or MAPS)], capture_output=True, text=True, env=env,
                         timeout=timeout).stdout.splitlines()
    per_game, ev = [], []
    for line in out:
        if line.startswith("@@EV"):
            p = line.split()
            ev.append((int(p[1][2:]), p[2], _kv(p[3:]), line))
            continue
        if line.startswith("{\"error\""):
            raise RuntimeError(json.loads(line)["error"])
        if not line.startswith('{"game"'):
            continue
        d = json.loads(line)
        us = 0 if d["a_side"] == "A" else 1
        engs = segment(ev, us)
        our_kill_rounds = [r for r, k, f, raw in ev if k == "death" and "by=champ" in raw and int(f["team"]) != us]
        per_game.append({
            "map": d["map"], "win": int(d["winner"] == us), "gems": d["gems"][us], "opp_gems": d["gems"][1 - us],
            "kills": d["kills"][us] if "kills" in d else len(our_kill_rounds),
            "opp_kills": d["kills"][1 - us] if "kills" in d else sum(
                1 for r, k, f, raw in ev if k == "death" and "by=champ" in raw and int(f["team"]) == us),
            "deaths": d["deaths"][us] if "deaths" in d else None,
            "opp_deaths": d["deaths"][1 - us] if "deaths" in d else None,
            "champ_dmg": d["champ_damage"][us] if "champ_damage" in d else sum(e["dealt"] for e in engs),
            "opp_champ_dmg": d["champ_damage"][1 - us] if "champ_damage" in d else sum(e["taken"] for e in engs),
            "first_kill_round": min(our_kill_rounds) if our_kill_rounds else None,
            "engagements": [e for e in engs if e["dealt"] + e["taken"] >= MIN_FIGHT_DAMAGE],
            "our_deaths_in_fights": sum(e["our_deaths"] for e in engs),
            "our_out_deaths": sum(e["our_out_deaths"] for e in engs),
            "their_deaths_in_fights": sum(e["their_deaths"] for e in engs),
            "their_out_deaths": sum(e["their_out_deaths"] for e in engs),
            "low_hp": low_hp_episodes(ev, us), "opp_low_hp": low_hp_episodes(ev, 1 - us),
        })
        ev = []
    return {"games": per_game, "summary": summarize(per_game)}


def summarize(per_game):
    n = max(1, len(per_game))
    engs = [e for g in per_game for e in g["engagements"]]
    m = max(1, len(engs))
    fk = [g["first_kill_round"] for g in per_game if g["first_kill_round"] is not None]
    their_d = sum(g["their_deaths_in_fights"] for g in per_game)
    our_d = sum(g["our_deaths_in_fights"] for g in per_game)
    return {
        "games": len(per_game),
        "win": sum(g["win"] for g in per_game) / n,
        "gems": sum(g["gems"] for g in per_game) / n,
        "opp_gems": sum(g["opp_gems"] for g in per_game) / n,
        "kills": sum(g["kills"] for g in per_game) / n,
        "opp_kills": sum(g["opp_kills"] for g in per_game) / n,
        "champ_dmg": sum(g["champ_dmg"] for g in per_game) / n,
        "opp_champ_dmg": sum(g["opp_champ_dmg"] for g in per_game) / n,
        "first_kill_round": statistics.median(fk) if fk else 2000.0,
        "fight_score": sum((e["dealt"] - e["taken"]) / (e["dealt"] + e["taken"]) for e in engs) / m,
        "engagements": len(engs) / n,
        # share of the OPPONENT's deaths in fights that came while it was outnumbered (TOP_TEAMS "2v1 share")
        "opp_out_death_share": sum(g["their_out_deaths"] for g in per_game) / max(1, their_d),
        # the same for A itself (gap metrics for our own bot), and A's per-game death counts in fights
        "out_death_share": sum(g["our_out_deaths"] for g in per_game) / max(1, our_d),
        "out_deaths": sum(g["our_out_deaths"] for g in per_game) / n,
        "fight_deaths": our_d / n,
        "fights_won": sum(e["dealt"] > e["taken"] for e in engs) / m,
        # P(death within LOW_HP_WINDOW rounds | below LOW_HP health with an enemy champion within LOW_HP_RANGE)
        "low_hp_death_rate": sum(g["low_hp"][1] for g in per_game) / max(1, sum(g["low_hp"][0] for g in per_game)),
        "low_hp_episodes": sum(g["low_hp"][0] for g in per_game) / n,
        "opp_low_hp_death_rate": sum(g["opp_low_hp"][1] for g in per_game) / max(1, sum(g["opp_low_hp"][0] for g in per_game)),
        "dealt_per_fight": sum(e["dealt"] for e in engs) / m,
        "taken_per_fight": sum(e["taken"] for e in engs) / m,
    }
