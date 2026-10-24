"""Differential replay of an official .repl26a through the simulator.

Feeds both teams' recorded actions (dump.js output) to cambsim and, at the start of every
champion turn, compares the simulator's full state with the engine's (positions, HP, alive,
gold, gems, kills; camp HP; submitted gems). Reports the first divergence (and a few more).
Usage: PYTHONPATH=sim/build python3 rereplay.py MAP.map26a DUMP.jsonl [--max N]
"""
import json, sys
import cambsim
DASH = 6  # AbilityKind::dash

mp, dump = sys.argv[1], sys.argv[2]
MAXD = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 5
recs = [json.loads(l) for l in open(dump)]
final = recs[-1]; turns = recs[:-1]
picks = [[p for p in final["drafts"][t] if p >= 0] for t in (0, 1)]
diffs = []; state = {"i": 0, "errs": 0, "turns": 0}


def note(msg):
    diffs.append(msg)
    print(msg, flush=True)
    if len(diffs) >= MAXD: raise SystemExit(1)


def compare(api, rec):
    rnd, champs, camps, sa, sb = api.truth()
    eng = rec["before"]
    if rnd != rec["r"]: note(f"r{rec['r']} c{rec['c']}: sim round {rnd}")
    # match champions by (team, type)
    sim = {(c[1], c[2]): c for c in champs}
    for e in eng["ch"]:
        s = sim.get((e[0], e[1]))
        if s is None: note(f"r{rec['r']}: no sim champion team {e[0]} type {e[1]}"); continue
        _, team, typ, alive, x, y, hp, mhp, gold, gems, kills, st, fo = s
        se = [int(alive), x if alive else -1, y if alive else -1, round(hp, 2), gold, gems, kills]
        ee = [e[2], e[3] if e[2] else -1, e[4] if e[2] else -1, e[5], e[6], e[7], e[8]]
        bad = [n for n, a, b in zip("alive x y hp gold gems kills".split(), se, ee) if (abs(a - b) > 0.02 if n == "hp" else a != b)]
        if bad: note(f"r{rec['r']} before turn of team {rec['team']} type {rec['type']}: champion team {team} type {typ}: {bad} sim {se} engine {ee}")
    for k, (s, e) in enumerate(zip(camps, eng["camps"])):
        if (e[0], e[1]) == (-1, -1):  # not present in the engine (dead): sim keeps the spawn tile
            if s[2] > 0 and s[3] != 0: note(f"r{rec['r']}: camp {k} dead in engine, sim hp {s[2]:.2f} life {s[3]}")
            continue
        if (s[0], s[1]) != (e[0], e[1]) or abs(s[2] - e[2]) > 0.02:
            note(f"r{rec['r']} before turn of team {rec['team']} type {rec['type']}: camp {k} at {e[0]},{e[1]} sim hp {s[2]:.2f} engine {e[2]}")
    if [sa, sb] != eng["sub"]: note(f"r{rec['r']}: submitted sim {[sa, sb]} engine {eng['sub']}")


def unit_at(api, x, y):
    _, champs, camps, _, _ = api.truth()
    for c in champs:
        if c[3] and (c[4], c[5]) == (x, y): return 1, c[0]
    for k, c in enumerate(camps):
        if (c[0], c[1]) == (x, y) and c[2] > 0 and c[3] != 0: return 2, k  # life 0 = dead (CampLife)
    e, locks = api.altar_locks()
    for lk in (locks if e == 0 else []):
        if (lk.x, lk.y) == (x, y): return 6, lk.handle  # EntityKind::altar_lock
    return 0, 0


def act(api, rec, a):
    k = a["k"]; t = a.get("t", [0, 0])
    if k == "Move": r = api.move_to(*t)
    elif k == "Movement blocked":  # a failed move input in the engine: must fail here too
        e, ok = api.move_to(*t)
        if e == 0 and ok: note(f"r{rec['r']} team {rec['team']} type {rec['type']}: blocked move {a} succeeded in the sim")
        return
    elif k == "Attack":
        kind, h = unit_at(api, *t); r = api.attack(kind, h)
    elif k == "Cast ability":
        sl = a.get("sl", 0)
        e, pr = api.champion_ability_props(api.my_champion(), sl)
        if e == 0 and pr.targets & 16: kind, h = 0, 0  # ground-targeted: the tile
        elif e == 0 and pr.targets == 8: kind, h = 1, api.my_champion()  # self
        else: kind, h = unit_at(api, *t)
        r = api.cast(sl, kind, h, *t)
    elif k == "Set priority": r = api.set_priority(a["p"])
    elif k == "Place ward": r = api.place_ward(*t)
    elif k == "Recall": r = api.recall()
    elif k == "Cancel channel": r = api.cancel_channel()
    elif k == "Submit gems": r = api.submit_gems(*t)
    elif k == "Shop":
        r = []
        d = dict(a.get("items", []))
        for j in range(0, 42, 2):  # shard j, emblem j+1: 5 shards combine on purchase
            n = d.get(j, 0) + 5 * d.get(j + 1, 0)
            if n > 0: r.append(api.buy_item(j, n))
        for j, n in a.get("cons", []):
            for _ in range(max(0, n)): r.append(api.buy_consumable(j))
    elif k == "Sell item":
        r = [api.sell(j) for j, n in a.get("items", []) if n < 0]
    elif k == "Teleport channel": r = api.use_consumable(0, *t)
    elif k == "Place altar lock": r = api.use_consumable(2, *t)
    elif k == "Resign": r = api.resign()
    elif k in ("Teleport complete", "Respawn", "Turn rollover", "Capture", "Gems submitted", "Bot error", "Input", "Phase", "Draft champion"):
        return
    else:
        note(f"r{rec['r']}: unhandled action {k}"); return
    errs = [x for x in (r if isinstance(r, list) else [r]) if (x[0] if isinstance(x, tuple) else x) != 0]
    if errs:
        state["errs"] += 1
        note(f"r{rec['r']} team {rec['team']} type {rec['type']}: {k} {a} -> sim error {errs}")


class Replayer(cambsim.Player):
    def __init__(self, team):
        super().__init__(); self.team = team; self.pick = 0

    def turn(self, api):
        if api.champ < 0:
            if self.pick < len(picks[self.team]):
                api.draft_champion(picks[self.team][self.pick]); self.pick += 1
            return
        if state["i"] >= len(turns): return
        rec = turns[state["i"]]
        _, champs, _, _, _ = api.truth()
        me = champs[api.my_champion()]
        if (me[1], me[2]) != (rec["team"], rec["type"]):
            note(f"r{rec['r']}: turn order: sim runs team {me[1]} type {me[2]}, engine team {rec['team']} type {rec['type']}")
            return
        state["i"] += 1; state["turns"] += 1
        compare(api, rec)
        for a in rec["acts"]: act(api, rec, a)


m = cambsim.load_map(mp)
try:
    res = cambsim.Match(m, Replayer(0), Replayer(1), seed=1, unlimited_fuel=True, max_rounds=final["round"]).run()
    print("sim result", res)
    print("engine final: round", final["round"], "outcome", final["outcome"], "submitted", final["after"]["sub"])
except SystemExit:
    pass
print(f"turns compared {state['turns']} of {len(turns)}; divergences reported {len(diffs)}")
