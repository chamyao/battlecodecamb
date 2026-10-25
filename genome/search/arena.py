"""Survival arena: a population of genomes evolving against itself, plus fixed anchors.

    python3 -m genome.search.arena --out runs/arenaA --tag A --seed genome/seeds/v23.genome --budget 8
    python3 -m genome.search.arena --out runs/arenaB --tag B --seed ... --budget 3 --intel-branch genome/intel

- Population: up to --capacity genomes, starting from the seed; first-generation mutants fill it.
- Matches: continuous and sampled. A match is --match-games games (--match-games/2 maps from a cycled
  map list, both sides of each map, same seed for both sides). Each newborn plays --newborn-matches
  matches against random members; between births, random pairings (members with uncertain ratings
  are picked more often). Ratings: TrueSkill (1v1, per game), with uncertainty; every match is logged.
- Death: over capacity, the lowest-rated genome dies. Only genomes with >= --min-games games, outside
  a protected species (younger than --protect-games games) and not taking a species below --min-species
  members are eligible; if nobody is, the smallest-species rule is relaxed before going over capacity.
- Birth: parent by tournament (--tournament) on rating; fixed operator mix: edge mutation 70% (two
  edges 25% of those), crossover 15%, constant tuning 15%; Opus every 10th LLM call. Crossover partner:
  same species with probability 0.8 (crossover by gene ID), else another species (crossover by meaning).
  Invalid children and behavioural twins (identical per-game outcomes to a member on the twin-check
  games) do not enter.
- Species: NEAT-style distance to each species representative: (gene IDs in only one genome
  + 0.5 x shared IDs whose bodies differ) / genome size; below --species-delta joins that species.
- Anchors: fixed opponents (--anchors) that are rated but never die and are never parents; every
  --champion-every births the current top genome is frozen as a champion anchor.
- Ladder gate (outside selection, gate.py): every --gate-every births the top --gate-top genomes with
  >= --gate-min-games games get a --gate-screen-games screen vs --gate-ref; at >= --gate-screen, each is played
  --gate-h2h games per seed (two fresh seeds) head to head vs --gate-ref (>= 53.5% over 800 games: the
  lower bound at --z standard errors above 50%) and --gate-games per seed vs every fixed anchor (no drop
  > --regress vs the reference's own rate). Passing genomes go to <out>/candidates/. Each gated genome is
  also played vs the reference with fuel x10 (behavioural vs fuel-only strength).
- Intel (--intel-branch, arena B): genome/intel/GAPS.md lines relevant to the mutated edge go into the
  mutation prompt; genome/intel/directed/*.genome are ingested once each as newborns.
- Logs (append-only JSONL, every record tagged with the arena): children, births, deaths, species,
  matches, gates, summaries; <out>/summary.md every --summary-every births. <out>/state.json is the
  checkpoint: a restart resumes.
"""
import argparse
import json
import math
import random
import re
import subprocess
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from funsearch.evaluate import MAPS, ROOT

from .. import build as gbuild
from .. import lang
from . import edit, operators
from .claude import BudgetExceeded, Claude
from .score import Scorer

FRESH_SEEDS = (5_000_011, 6_000_011)
MORE_SEEDS = (7_000_011, 8_000_011)
TWIN_SEED = 4_000_037

# ---------------------------------------------------------------- TrueSkill, 1v1 without draws
MU0, SIGMA0 = 25.0, 25.0 / 3
FIXED_DEFAULT = True
BETA, TAU = 25.0 / 6, 25.0 / 300


def _pdf(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def _cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def rate_game(w, l):
    """Update two rating dicts {mu, sigma} in place for one game won by w."""
    for r in (w, l):
        r["sigma"] = math.sqrt(r["sigma"] ** 2 + TAU ** 2)
    c = math.sqrt(2 * BETA ** 2 + w["sigma"] ** 2 + l["sigma"] ** 2)
    t = (w["mu"] - l["mu"]) / c
    v = _pdf(t) / max(_cdf(t), 1e-12)
    ww = v * (v + t)
    w["mu"] += w["sigma"] ** 2 / c * v
    l["mu"] -= l["sigma"] ** 2 / c * v
    w["sigma"] *= math.sqrt(max(1e-6, 1 - w["sigma"] ** 2 / c ** 2 * ww))
    l["sigma"] *= math.sqrt(max(1e-6, 1 - l["sigma"] ** 2 / c ** 2 * ww))


# ---------------------------------------------------------------- the arena

class Arena:
    def __init__(self, args):
        self.a = args
        self.out = Path(args.out)
        for d in ("genomes", "candidates"):
            (self.out / d).mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.sc = Scorer([], threads=1, bot_seeds=args.bot_seeds)
        if args.llm_queue:  # every Claude call goes to a file queue answered by a Claude Code session (queuellm.py)
            from .queuellm import QueueClaude
            self.claude = QueueClaude(args.llm_queue, args.queue_timeout, self.queue_feedback)
            self.q_reported, self.q_alive = set(), set()
        else:
            self.claude = Claude(args.budget, opus_every=args.opus_every)
        self.claude.spent = sum(r.get("cost", 0.0) for r in self._read("children"))
        self.maps = sorted(MAPS)
        self.specs = {}
        state = self.out / "state.json"
        if state.exists():
            self.s = json.loads(state.read_text())
            self.log(f"resumed: {len(self.genomes())} genomes, {self.s['births']} births, "
                     f"{self.s['matches']} matches, spent ${self.claude.spent:.2f}")
        else:
            self.s = {"members": {}, "species": {}, "births": 0, "deaths": 0, "matches": 0, "games": 0,
                      "map_ptr": 0, "newborn_queue": [], "top": None, "top_streak": 0, "gated": [],
                      "intel_seen": [], "bars": {}, "next_species": 0, "since_birth": 0}
            for path in args.anchors.split(","):
                self._add_anchor(Path(path).stem, path)
            text = Path(args.seed).read_text()
            m = self._add_genome(text, "seed", [], {"op": "seed"})
            self.log(f"new arena {args.tag}: seed {m['name']} in species {m['species']}, "
                     f"{len(self.anchors())} anchors")
        if args.refingerprint:  # resumed on another runtime: redo the twin-check games of every live genome
            for m in self.genomes():
                m["fingerprint"] = self.fingerprint((self.out / m["path"]).read_text())
            self.log(f"re-fingerprinted {len(self.genomes())} genomes on this runtime")
        for spec in filter(None, args.add_anchors.split(",")):  # new fixed anchors joining a resumed arena
            name, _, path = spec.rpartition("=")  # name=path (e.g. to freeze a copy of a member), or path
            name = name or Path(path).stem
            if name in self.s["members"]:
                self.log(f"anchor {name} not added: the name is taken (pass NAME=path)")
            else:
                m = self._add_anchor(name, path)
                m["calibrating"] = True  # rated like a member for --calibrate-games games, then frozen
                m["calibrate_until"] = args.calibrate_games
                self.log(f"added anchor {name} (calibrating for {args.calibrate_games} games)")
        if args.recalibrate_anchors:  # e.g. after a runtime change: policy anchors rated again, then refrozen
            for m in self.anchors():
                if m.get("source") is None and m["path"].endswith(".policy") and not m.get("calibrating"):
                    m["calibrating"], m["calibrate_until"] = True, m["games"] + args.calibrate_games
                    m["sigma"] = max(m["sigma"], args.recalibrate_sigma)
                    self.log(f"recalibrating anchor {m['name']} (mu {m['mu']:.2f}) for {args.calibrate_games} games")
        if args.fixed_anchors:  # freeze every anchor at its current mu (keeps the scale, fixed from here on)
            for m in self.anchors():
                if not m.get("calibrating"):
                    m["sigma"] = args.anchor_sigma
            self.log("fixed anchors: " + ", ".join(f"{m['name']} {m['mu']:.2f}" for m in self.anchors()))
        self.anchor_weights = {k: float(v) for k, _, v in (x.partition("=") for x in args.anchor_weight)}
        self.rng = random.Random(self.s["births"] * 7919 + self.s["matches"] + 1)
        self.gaps, self.gaps_t = [], 0.0

    # ---- logging
    def _write(self, kind, rec):
        rec = {"arena": self.a.tag, "t": round(time.time(), 1), **rec}
        with open(self.out / f"{kind}.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")

    def _read(self, kind):
        p = self.out / f"{kind}.jsonl"
        return [json.loads(l) for l in open(p)] if p.exists() else []

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] [{self.a.tag}] {msg}"
        print(line, flush=True)
        with open(self.out / "log.txt", "a") as f:
            f.write(line + "\n")

    def save(self):
        tmp = self.out / "state.json.tmp"
        tmp.write_text(json.dumps(self.s))
        tmp.replace(self.out / "state.json")

    # ---- members
    def genomes(self):
        return [m for m in self.s["members"].values() if m["kind"] == "genome" and m["alive"]]

    def anchors(self):
        return [m for m in self.s["members"].values() if m["kind"] == "anchor"]

    def players(self):
        return self.genomes() + self.anchors()

    def spec(self, m):
        if m["name"] not in self.specs:
            path = self.out / m["path"] if not Path(m["path"]).is_absolute() else Path(m["path"])
            if m["path"].endswith(".genome"):
                self.specs[m["name"]] = f"genome:{gbuild.build(path.read_text())}"
            else:
                self.specs[m["name"]] = self.sc._spec(str(path))
        return self.specs[m["name"]]

    def _add_anchor(self, name, path, rating=None, source=None):
        # fixed anchors: absolute paths in the checkout; champions: relative to the output directory
        m = {"name": name, "kind": "anchor", "path": str(Path(path).resolve()) if source is None else path, "mu": MU0, "sigma": SIGMA0,
             "games": 0, "wins": 0, "alive": True, "born": self.s["births"], "species": None, "parents": [],
             "fingerprint": None, "source": source}
        if rating:
            m["mu"], m["sigma"] = rating
        if self.a.fixed_anchors and rating:
            m["sigma"] = self.a.anchor_sigma
        self.s["members"][name] = m
        return m

    def _add_genome(self, text, name, parents, info, fingerprint=None):
        path = f"genomes/{name}.genome"
        (self.out / path).write_text(text)
        ps = [self.s["members"][p] for p in parents]
        mu = sum(p["mu"] for p in ps) / len(ps) if ps else MU0
        m = {"name": name, "kind": "genome", "path": path, "mu": mu, "sigma": self.a.newborn_sigma if ps else SIGMA0,
             "games": 0, "wins": 0, "alive": True, "born": self.s["births"], "parents": parents,
             "fingerprint": fingerprint, "anchor_games": {}}
        m["species"] = self._species_of(text, name)
        self.s["members"][name] = m
        if m["fingerprint"] is None:
            m["fingerprint"] = self.fingerprint(text)
        self._write("births", {"name": name, "birth": self.s["births"], "parents": parents, "species": m["species"],
                               "mu": mu, **info})
        return m

    # ---- species
    def _canon(self, text):
        return {i: edit.body_canon(t) for i, t in edit.segments(text)[2].items()}

    def distance(self, ta, tb):
        a, b = self._canon(ta), self._canon(tb)
        disjoint = len(set(a) ^ set(b))
        changed = sum(1 for i in set(a) & set(b) if a[i] != b[i])
        return (disjoint + 0.5 * changed) / max(len(a), len(b), 1)

    def _species_of(self, text, name):
        for sid, sp in self.s["species"].items():
            rep = self.out / sp["rep_path"]
            if self.distance(text, rep.read_text()) < self.a.species_delta:
                return sid
        sid = f"S{self.s['next_species']}"
        self.s["next_species"] += 1
        self.s["species"][sid] = {"rep": name, "rep_path": f"genomes/{name}.genome", "born": self.s["births"],
                                  "games_at_birth": self.s["games"], "games": 0}
        self._write("species", {"species": sid, "founder": name, "birth": self.s["births"]})
        self.log(f"new species {sid} founded by {name}")
        return sid

    def species_members(self, sid):
        return [m for m in self.genomes() if m["species"] == sid]

    def protected(self, sid):
        return self.s["species"][sid]["games"] < self.a.protect_games

    # ---- twin check: per-game outcomes on fixed games vs two anchors
    def fingerprint(self, text):
        spec = f"genome:{gbuild.build(text)}"
        outs = []
        for anc in self.anchors()[:2]:
            st = self.sc.play(spec, self.spec(anc), TWIN_SEED, self.a.match_games, threads=1)
            if "error" in st:
                raise RuntimeError(st["error"])
            outs.append((st.get("results"), st["a_gems"], st["b_gems"]))
        return json.dumps(outs)

    # ---- matches
    # Every game is fixed by its map and side (genomes ignore the seed; policies are seeded as deployed with
    # --bot-seeds), so a pair has 80 distinct games. A match plays maps the pair has not played yet, both sides;
    # an exhausted pair is not matched again.
    def pair_key(self, an, bn):
        return "|".join(sorted((an, bn)))

    def next_maps(self, an, bn):
        k = self.a.match_games // 2
        played = set(self.s.setdefault("pair_maps", {}).get(self.pair_key(an, bn), []))
        ptr = self.s["map_ptr"]
        self.s["map_ptr"] = (ptr + k) % len(self.maps)
        order = [self.maps[(ptr + i) % len(self.maps)] for i in range(len(self.maps))]
        if not self.a.distinct_games:  # old behaviour: the global map pointer, repeats counted
            return order[:k]
        fresh = [m for m in order if Path(m).stem not in played][:k]
        self.s["pair_maps"].setdefault(self.pair_key(an, bn), []).extend(Path(m).stem for m in fresh)
        return fresh

    def exhausted(self, an, bn):
        if not self.a.distinct_games:
            return False
        return len(self.s.setdefault("pair_maps", {}).get(self.pair_key(an, bn), [])) >= len(self.maps)

    def pick_pair(self):
        """Newborn matches first; else a random pairing weighted toward uncertain genomes."""
        alive = {m["name"] for m in self.players()}
        while self.s["newborn_queue"]:
            a, b = self.s["newborn_queue"].pop(0)
            if a in alive and b in alive and not self.exhausted(a, b):
                return a, b
        gs = self.genomes()
        if len(gs) < 1:
            return None
        for _ in range(50):
            a = self.rng.choices(gs, [m["sigma"] for m in gs])[0]
            others = [m for m in self.players() if m["name"] != a["name"] and not self.exhausted(a["name"], m["name"])]
            if others:  # anchors can be drawn more often (--anchor-weight NAME=W)
                w = [self.anchor_weights.get(m["name"], 1.0) if m["kind"] == "anchor" else 1.0 for m in others]
                return a["name"], self.rng.choices(others, w)[0]["name"]
        return None

    def play_match(self, an, bn, seed, maps):
        with self.lock:
            a, b = self.s["members"][an], self.s["members"][bn]
            sa, sb = self.spec(a), self.spec(b)
        details = self.a.game_details or bool(self.a.llm_queue)
        out = subprocess.run([str(self.sc_eval()), "--a", sa, "--b", sb, "--games", str(2 * len(maps)),
                              "--threads", "1", "--seed", str(seed), *(["--bot-seeds"] if self.a.bot_seeds else []),
                              *(["--details"] if details else []), *maps], capture_output=True,
                             text=True, timeout=1800)
        if out.returncode != 0:
            return {"error": f"exit {out.returncode}: {out.stderr[-200:]}"}
        lines = [json.loads(l) for l in out.stdout.splitlines() if l.strip().startswith("{")]
        st = lines[-1]
        if details:  # per game: map, A won, A's and B's deaths not caused by enemy champions (camps, monoliths, ...)
            g = []
            for d in lines[:-1]:
                if "deaths" not in d:
                    continue
                at = 1 if d["a_side"] == "B" else 0
                g.append([Path(d["map"]).stem, int(d["winner"] == at), d["deaths"][at] - d["kills"][1 - at],
                          d["deaths"][1 - at] - d["kills"][at]])
            st["per_game"] = g
        return st

    @staticmethod
    def sc_eval():
        from .score import EVAL
        return EVAL

    def record_match(self, an, bn, seed, maps, st):
        with self.lock:
            if "error" in st:
                self.log(f"match {an} vs {bn} failed: {st['error']}")
                return
            a, b = self.s["members"].get(an), self.s["members"].get(bn)
            if a is None or b is None:
                return
            before = (a["mu"], b["mu"])
            for r in st.get("results", []):
                if r == 0.5:
                    continue
                w_, l_ = (a, b) if r > 0.5 else (b, a)
                keep = [(m["mu"], m["sigma"]) for m in (w_, l_)]
                rate_game(w_, l_)
                if self.a.fixed_anchors:  # anchors keep fixed ratings: only the genome learns from the game
                    for m, (mu, sg) in zip((w_, l_), keep):
                        if m["kind"] == "anchor" and not m.get("calibrating"):
                            m["mu"], m["sigma"] = mu, sg
            n, w = st["games"], st["a_wins"]
            for m in (a, b):
                if m.get("calibrating") and m["games"] + n >= m.get("calibrate_until", self.a.calibrate_games):
                    m["calibrating"], m["sigma"] = False, self.a.anchor_sigma
                    self.log(f"anchor {m['name']} frozen at mu {m['mu']:.2f} after {m['games'] + n} games")
            a["games"] += n
            b["games"] += n
            a["wins"] += w
            b["wins"] += n - w
            for x, y, wins in ((a, b, w), (b, a, n - w)):
                if x["kind"] == "genome" and y["kind"] == "anchor" and y.get("source") is None:
                    ag = x["anchor_games"].setdefault(y["name"], [0, 0])
                    ag[0] += wins
                    ag[1] += n
                if x["kind"] == "genome":
                    self.s["species"][x["species"]]["games"] += n
            for row in st.get("per_game", []):  # per member: wins by map, deaths not caused by champions
                mp, aw, ad, bd = row
                for m, won, dd in ((a, aw, ad), (b, 1 - aw, bd)):
                    ms = m.setdefault("map_stats", {}).setdefault(mp, [0, 0])
                    ms[0] += won
                    ms[1] += 1
                    nc = m.setdefault("nc_deaths", [0, 0])
                    nc[0] += dd
                    nc[1] += 1
            self.s["matches"] += 1
            self.s["games"] += n
            self.s["since_birth"] += 1
            self._write("matches", {"a": an, "b": bn, "seed": seed, "maps": [Path(m).stem for m in maps],
                                    "games": n, "a_wins": w, "results": st.get("results"),
                                    "a_gems": st["a_gems"], "b_gems": st["b_gems"],
                                    "a_fuel": st.get("a_fuel_per_game"), "a_susp": st.get("a_suspensions"),
                                    **({"per_game": st["per_game"]} if "per_game" in st else {}),
                                    "mu_before": before, "mu": [a["mu"], b["mu"]], "sigma": [a["sigma"], b["sigma"]]})
            self.cull()

    # ---- death
    def cull(self):
        while len(self.genomes()) > self.a.capacity:
            gs = self.genomes()
            ok = [m for m in gs if m["games"] >= self.a.min_games and not self.protected(m["species"])]
            strict = [m for m in ok if len(self.species_members(m["species"])) > self.a.min_species]
            pool = strict or [m for m in ok if len(self.species_members(m["species"])) > 1] or ok
            if not pool:
                return  # everyone is new or protected: stay over capacity for now
            v = min(pool, key=lambda m: m["mu"])
            v["alive"] = False
            self.s["deaths"] += 1
            self._write("deaths", {"name": v["name"], "mu": v["mu"], "sigma": v["sigma"], "games": v["games"],
                                   "species": v["species"], "rule": "strict" if strict else "relaxed",
                                   "population": len(gs) - 1})

    # ---- birth
    def tournament(self, pool):
        k = min(self.a.tournament, len(pool))
        return max(self.rng.sample(pool, k), key=lambda m: m["mu"])

    def intel_notes(self, names):
        if not self.a.intel_branch:
            return ""
        lines = self.gaps
        hit = [l for l in lines if any(re.search(rf"\b{re.escape(n)}\b", l) for n in names)]
        chosen = (hit or lines[:5])[:8]
        return ("\nLadder evidence about our bot's real losses (from genome/intel/GAPS.md):\n" +
                "\n".join(chosen)) if chosen else ""

    def propose(self, seq):
        """Runs in a worker thread: pick parents and an operator, make and check a child."""
        with self.lock:
            r = random.Random(self.rng.random())
            gs = self.genomes()
            parent = self.tournament(gs)
            u = r.random()
            op = "mutate" if u < 0.70 else "cross" if u < 0.85 else "tune"
            partner = None
            if op == "cross":
                same = [m for m in gs if m["species"] == parent["species"] and m["name"] != parent["name"]]
                other = [m for m in gs if m["species"] != parent["species"]]
                pool = same if (same and (r.random() < 0.8 or not other)) else other
                partner = self.tournament(pool) if pool else None
                if partner is None:
                    op = "mutate"
            ptext = (self.out / parent["path"]).read_text()
            prefix = f"{self.a.tag}{seq}"
        parents = [parent["name"]]
        if self.a.llm_queue:
            from .queuellm import QueueTimeout
            self.claude.context(op, [parent["name"]] + ([partner["name"]] if partner else []), seq)
            try:
                return self._propose_ops(op, ptext, parent, partner, parents, prefix, r, seq)
            except QueueTimeout as e:
                return self.check(operators.Child(None, op, "queue timeout", {"detail": str(e)}, "session"),
                                  parents, seq)
        return self._propose_ops(op, ptext, parent, partner, parents, prefix, r, seq)

    def _propose_ops(self, op, ptext, parent, partner, parents, prefix, r, seq):
        if op == "tune":
            child = operators.tune(ptext, r)
        elif op == "cross":
            btext = (self.out / partner["path"]).read_text()
            parents.append(partner["name"])
            if partner["species"] == parent["species"]:
                child = operators.crossover(ptext, btext, r)
                if child.error in ("child equals a parent", "parents identical where they share genes"):
                    child, parents = None, [parent["name"]]  # no new combination: mutate instead
            else:
                child = operators.llm_cross(ptext, parent["mu"], btext, partner["mu"], self.claude, prefix)
            if child is None:
                op = "mutate"
        if op == "mutate":
            two = 1.0 if r.random() < 0.25 else 0.0
            child = operators.mutate(ptext, self.claude, r, prefix, self._stats_line(parent), two,
                                     notes_fn=self.intel_notes, variant=self.a.mutate_prompt)
        return self.check(child, parents, seq)

    @staticmethod
    def _member_brief(m):
        """Compact per-member results for the session's feedback: rating, worst 3 maps by win rate (>= 2 games),
        and deaths per game not caused by enemy champions."""
        out = [m["name"], round(m["mu"], 2), round(m["sigma"], 2), m["games"]]
        ms = [(w / n, mp, w, n) for mp, (w, n) in m.get("map_stats", {}).items() if n >= 2]
        worst = [[mp, w, n] for _, mp, w, n in sorted(ms)[:3]]
        nc = m.get("nc_deaths", [0, 0])
        return out + [worst, round(nc[0] / nc[1], 2) if nc[1] else None]

    def queue_feedback(self):
        """Feedback for the next queued request: outcomes of earlier queued children not yet reported; for every live
        queued child [name, mu, sigma, games, worst 3 maps [map, wins, games], non-champion deaths per game]; the
        queued children that died since the last request; the top 5 (same fields)."""
        with self.lock:
            fb = {"outcomes": []}
            for r in self._read("children"):
                if r.get("model") != "session" or r["seq"] in self.q_reported:
                    continue
                self.q_reported.add(r["seq"])
                info = (r.get("log") or {}).get("llm")
                q = info.get("queue_seq") if isinstance(info, dict) else None
                out = "accepted" if r.get("accepted") else "twin" if r.get("twin_of") else "invalid"
                fb["outcomes"].append({"child_seq": r["seq"], "request": q, "op": r["op"], "outcome": out,
                                       **({"name": r["name"]} if r.get("accepted") else {}),
                                       **({"twin_of": r["twin_of"]} if r.get("twin_of") else {}),
                                       **({"error": (r.get("error") or "")[:160]} if out == "invalid" else {})})
                if r.get("accepted"):
                    self.q_alive.add(r["name"])
            mem = self.s["members"]
            alive = {n for n in self.q_alive if n in mem and mem[n].get("alive", True)}
            fb["died"] = sorted(self.q_alive - alive)
            self.q_alive = alive
            fb["rated"] = [self._member_brief(mem[n]) for n in sorted(alive)]
            fb["top5"] = [self._member_brief(m) for m in sorted(self.genomes(), key=lambda m: -m["mu"])[:5]]
            fb["births"] = self.s["births"]
            return fb

    def _stats_line(self, m):
        return f"rating {m['mu']:.1f} ± {m['sigma']:.1f} over {m['games']} games in the arena"

    def check(self, child, parents, seq, op=None):
        rec = {"seq": seq, "op": op or child.op, "model": child.model, "cost": child.cost, "parents": parents,
               "prompt": self.a.mutate_prompt,
               "log": child.log, "error": child.error}
        if child.source is None:
            return rec, None
        try:
            fp = self.fingerprint(child.source)
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
            return rec, None
        rec["fingerprint"] = fp
        return rec, child.source

    def accept(self, rec, source):
        with self.lock:
            twin = next((m["name"] for m in self.genomes() if m["fingerprint"] == rec.get("fingerprint")), None)
            if source is not None and twin:
                rec["error"], rec["twin_of"] = "behavioural twin", twin
            self.s["births"] += source is not None and not rec["error"]
            rec["birth"] = self.s["births"]
            if source is None or rec["error"]:
                self._write("children", {**rec, "accepted": False, "fingerprint": None})
                return None
            name = f"{self.a.tag}{self.s['births']}"
            m = self._add_genome(source, name, rec["parents"], {"op": rec["op"], "model": rec["model"]},
                                 fingerprint=rec["fingerprint"])
            self._write("children", {**rec, "accepted": True, "name": name, "species": m["species"],
                                     "fingerprint": None})
            others = [x["name"] for x in self.players() if x["name"] != name]
            for opp in self.rng.sample(others, min(self.a.newborn_matches, len(others))):
                self.s["newborn_queue"].append((name, opp))
            self.s["since_birth"] = 0
            self.cull()
            self.after_birth()
            return m

    def after_birth(self):
        b = self.s["births"]
        top = self.top()
        if top:
            if top["name"] == self.s["top"]:
                self.s["top_streak"] += 1
            else:
                self.s["top"], self.s["top_streak"] = top["name"], 1
        if b % self.a.champion_every == 0 and top:
            name = f"champ{b // self.a.champion_every}-{top['name']}"
            if not any(m.get("source") == top["name"] for m in self.anchors()):
                path = self.out / "genomes" / f"{name}.genome"
                path.write_text((self.out / top["path"]).read_text())
                self._add_anchor(name, f"genomes/{name}.genome", (top["mu"], top["sigma"]), source=top["name"])
                self.log(f"champion anchor {name} (mu {top['mu']:.1f})")
        if b % self.a.summary_every == 0:
            self.summary()
        self.save()

    def top(self):
        gs = [m for m in self.genomes() if m["games"] >= self.a.min_games]
        return max(gs, key=lambda m: m["mu"]) if gs else None

    # ---- ladder gate (genome/search/gate.py): every --gate-every births, the top --gate-top live genomes with
    # >= --gate-min-games games are screened vs the live bot; those at >= --gate-screen get the full gate
    def gate_due(self):
        return self.s["births"] >= self.s.get("next_gate", self.a.gate_every)

    def gate(self):
        from . import gate as G
        with self.lock:
            self.s["next_gate"] = self.s["births"] + self.a.gate_every
            pool = [m for m in self.genomes() if m["games"] >= self.a.gate_min_games and m["name"] not in self.s["gated"]]
            picks = sorted(pool, key=lambda m: -m["mu"])[:self.a.gate_top]
            for m in picks:
                self.s["gated"].append(m["name"])
            anchors = [m["path"] for m in self.anchors() if m.get("source") is None
                       and Path(m["path"]).resolve() != Path(self.a.gate_ref).resolve()]
        for t in picks:
            text = (self.out / t["path"]).read_text()
            rec = G.gate(text, self.a.gate_ref, anchors, self.a.gate_threads, self.a.gate_min_wins, self.a.regress,
                         self.s["bars"])
            rec = {"name": t["name"], "mu": t["mu"], "games": t["games"], "births": self.s["births"],
                   "ref": Path(self.a.gate_ref).name, **rec}
            self._write("gates", rec)
            deltas = {k: v["delta"] for k, v in rec["anchor_deltas"].items()}
            self.log(f"gate {t['name']} (mu {t['mu']:.1f}, {t['games']} games): h2h {rec['h2h_wins']}/{rec['h2h_games']}, "
                     f"anchor deltas {deltas}, fuel x10 {rec['h2h_fuel10_wins']}/{rec['h2h_games']} "
                     f"-> {'CANDIDATE' if rec['passed'] else 'no'}")
            if rec["passed"]:
                (self.out / "candidates" / f"{t['name']}.genome").write_text(text)
        self.save()

    # ---- intel (arena B)
    def refresh_intel(self):
        if not self.a.intel_branch or time.time() - self.gaps_t < self.a.intel_every:
            return []
        self.gaps_t = time.time()
        br = self.a.intel_branch
        subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", br], capture_output=True, timeout=120)
        g = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:genome/intel/GAPS.md"],
                           capture_output=True, text=True)
        if g.returncode == 0:
            self.gaps = [l.strip() for l in g.stdout.splitlines() if l.strip() and not l.startswith("#")]
        ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{br}", "genome/intel/directed/"],
                            capture_output=True, text=True)
        new = []
        for path in ls.stdout.split():
            if path.endswith(".genome") and path not in self.s["intel_seen"]:
                self.s["intel_seen"].append(path)
                t = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:{path}"], capture_output=True, text=True)
                new.append((path, t.stdout))
        return new

    def ingest(self, path, text, seq):
        try:
            lang.parse(text)
            child = operators.Child(text, "directed", None, {"file": path})
        except lang.GenomeError as e:
            child = operators.Child(None, "directed", f"GenomeError: {e}", {"file": path})
        known = set()
        for m in self.genomes():
            known |= set(edit.segments((self.out / m["path"]).read_text())[2])
        ids = set(edit.segments(text)[2]) if child.source else set()
        best = max(self.genomes(), key=lambda m: len(ids & set(edit.segments((self.out / m["path"]).read_text())[2])))
        return self.check(child, [best["name"]] if ids & known else [], seq, op="directed")

    # ---- summary
    def summary(self):
        gs = sorted(self.genomes(), key=lambda m: -m["mu"])
        anchors = sorted(self.anchors(), key=lambda m: -m["mu"])
        sp = {}
        for m in gs:
            sp[m["species"]] = sp.get(m["species"], 0) + 1
        top = [m for m in gs if m["games"] >= self.a.min_games][:3]
        cyc = {}
        for m in top:
            w = sum(v[0] for v in m["anchor_games"].values())
            n = sum(v[1] for v in m["anchor_games"].values())
            cyc[m["name"]] = round(w / n, 3) if n else None
        rec = {"births": self.s["births"], "deaths": self.s["deaths"], "matches": self.s["matches"],
               "games": self.s["games"], "spent": round(self.claude.spent, 3), "population": len(gs),
               "species": sp, "top": [(m["name"], round(m["mu"], 2), round(m["sigma"], 2), m["games"], m["species"])
                                      for m in gs[:5]],
               "anchors": [(m["name"], round(m["mu"], 2), m["games"]) for m in anchors],
               "top_vs_anchors": cyc}
        self._write("summaries", rec)
        lines = [f"# Arena {self.a.tag}: {time.strftime('%Y-%m-%d %H:%M')}", "",
                 f"births {rec['births']}, deaths {rec['deaths']}, matches {rec['matches']} ({rec['games']} games), "
                 f"spent ${rec['spent']:.2f}, population {len(gs)}, species {sp}", "",
                 "| genome | mu | sigma | games | species | win vs fixed anchors |", "| --- | --- | --- | --- | --- | --- |"]
        for m in gs[:10]:
            w = sum(v[0] for v in m["anchor_games"].values())
            n = sum(v[1] for v in m["anchor_games"].values())
            lines.append(f"| {m['name']} | {m['mu']:.2f} | {m['sigma']:.2f} | {m['games']} | {m['species']} | "
                         f"{w / n:.3f} ({n}) |" if n else f"| {m['name']} | {m['mu']:.2f} | {m['sigma']:.2f} | "
                         f"{m['games']} | {m['species']} | - |")
        lines += ["", "| anchor | mu | games |", "| --- | --- | --- |"]
        lines += [f"| {m['name']} | {m['mu']:.2f} | {m['games']} |" for m in anchors]
        gates = self._read("gates")
        if gates:
            lines += ["", "Gates: " + "; ".join(f"{g['name']} h2h {g['h2h']:.3f} {'PASS' if g['passed'] else 'fail'}"
                                                for g in gates[-5:])]
        (self.out / "summary.md").write_text("\n".join(lines) + "\n")
        self.log(f"summary: births {rec['births']} deaths {rec['deaths']} games {rec['games']} ${rec['spent']:.2f}; "
                 f"top {rec['top'][:3]}; top vs anchors {cyc}")

    # ---- main loop
    def run(self):
        a = self.a
        t_end = time.time() + a.max_hours * 3600
        births_open = True
        seq = len(self._read("children"))
        with ThreadPoolExecutor(a.threads) as mpool, ThreadPoolExecutor(a.births_in_flight) as bpool:
            matches, births = {}, {}
            while time.time() < t_end:
                # births: keep up to --births-in-flight proposals going once the newborn queue is drained
                with self.lock:
                    want_birth = (births_open and len(births) < a.births_in_flight
                                  and len(self.s["newborn_queue"]) <= a.threads
                                  and (len(self.genomes()) < a.capacity or self.s["since_birth"] >= a.random_matches)
                                  and not (a.max_births and self.s["births"] >= a.max_births))
                if want_birth:
                    seq += 1
                    births[bpool.submit(self.propose, seq)] = seq
                for path, text in self.refresh_intel():
                    seq += 1
                    births[bpool.submit(self.ingest, path, text, seq)] = seq
                # matches: keep every thread busy
                while len(matches) < a.threads:
                    with self.lock:
                        pair = self.pick_pair()
                        if pair is None:
                            break
                        mseed, maps = 9_000_000 + self.s["matches"] + len(matches), self.next_maps(*pair)
                    matches[mpool.submit(self.play_match, *pair, mseed, maps)] = (*pair, mseed, maps)
                if not matches and not births:
                    break
                done, _ = wait(list(matches) + list(births), timeout=30, return_when=FIRST_COMPLETED)
                for f in done:
                    if f in matches:
                        an, bn, mseed, maps = matches.pop(f)
                        try:
                            self.record_match(an, bn, mseed, maps, f.result())
                        except Exception as e:
                            self.log(f"match error: {type(e).__name__}: {e}")
                    else:
                        births.pop(f)
                        try:
                            rec, source = f.result()
                        except BudgetExceeded as e:
                            self.log(f"{e}: no more births")
                            births_open = False
                            continue
                        except Exception as e:
                            self.log(f"birth error: {type(e).__name__}: {e}")
                            continue
                        m = self.accept(rec, source)
                        if a.max_births and self.s["births"] >= a.max_births and births_open:
                            births_open = False
                            self.log(f"{self.s['births']} births (--max-births {a.max_births}): no more births")
                        if m:
                            self.log(f"birth {m['name']} ({rec['op']} {rec['model'] or ''}) of {rec['parents']} "
                                     f"species {m['species']}; {len(self.genomes())} genomes ${self.claude.spent:.2f}")
                        else:
                            self.log(f"rejected {rec['op']} {rec['model'] or ''}: {(rec['error'] or '')[:100]}")
                if self.gate_due():
                    self.gate()
                if not births_open and not births and self.s["since_birth"] >= a.tail_matches:
                    break
            self.summary()
            self.save()
        self.log(f"done: spent ${self.claude.spent:.2f}")
        if self.a.llm_queue:
            (Path(self.a.llm_queue) / "DONE").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True, help="arena name, written into every log record")
    ap.add_argument("--seed", required=True)
    ap.add_argument("--anchors", default=",".join(str(ROOT / p) for p in (
        "policies/candidates/style-gconv1.policy", "policies/v7.policy", "policies/candidates/tune-v20-L1.policy",
        "policies/candidates/rall2-ca4-lean-g.policy", "policies/opp-tune5-metadraft.policy")))
    ap.add_argument("--gate-ref", default=str(ROOT / "policies/candidates/style-gconv1.policy"))
    ap.add_argument("--budget", type=float, default=8.0)
    ap.add_argument("--opus-every", type=int, default=10)
    ap.add_argument("--capacity", type=int, default=24)
    ap.add_argument("--match-games", type=int, default=8)
    ap.add_argument("--newborn-matches", type=int, default=10)
    ap.add_argument("--random-matches", type=int, default=10, help="random matches between births (full arena)")
    ap.add_argument("--newborn-sigma", type=float, default=6.0)
    ap.add_argument("--min-games", type=int, default=40)
    ap.add_argument("--min-species", type=int, default=2)
    ap.add_argument("--protect-games", type=int, default=60)
    ap.add_argument("--species-delta", type=float, default=0.15)
    ap.add_argument("--tournament", type=int, default=3)
    ap.add_argument("--champion-every", type=int, default=50)
    ap.add_argument("--gate-every", type=int, default=60, help="births between gate rounds")
    ap.add_argument("--gate-top", type=int, default=3)
    ap.add_argument("--gate-min-games", type=int, default=200)
    ap.add_argument("--gate-min-wins", type=int, default=43, help="head-to-head wins of 80 vs the live bot to pass")
    ap.add_argument("--gate-h2h", type=int, default=400)
    ap.add_argument("--gate-games", type=int, default=200)
    ap.add_argument("--gate-threads", type=int, default=5)
    ap.add_argument("--z", type=float, default=2.0)
    ap.add_argument("--regress", type=float, default=0.03)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--births-in-flight", type=int, default=3)
    ap.add_argument("--summary-every", type=int, default=10)
    ap.add_argument("--max-hours", type=float, default=48)
    ap.add_argument("--tail-matches", type=int, default=200, help="matches played after the budget runs out")
    ap.add_argument("--llm-queue", default="", help="file-queue LLM backend directory (queuellm.py): a Claude Code "
                                                    "session answers every Claude call")
    ap.add_argument("--queue-timeout", type=float, default=900, help="seconds a queued request waits for its reply")
    ap.add_argument("--max-births", type=int, default=0, help="stop births at this total (0: budget only)")
    ap.add_argument("--game-details", action="store_true",
                    help="record per-game map results and non-champion deaths (always on with --llm-queue)")
    ap.add_argument("--fixed-anchors", action="store_true", default=FIXED_DEFAULT,
                    help="anchors keep fixed ratings (frozen at their current mu on resume)")
    ap.add_argument("--anchor-sigma", type=float, default=1.0)
    ap.add_argument("--anchor-weight", action="append", default=[],
                    help="NAME=W: draw this anchor W times as often as others as a random opponent (repeatable)")
    ap.add_argument("--add-anchors", default="", help="anchors to add to a resumed arena (comma list of path or NAME=path)")
    ap.add_argument("--calibrate-games", type=int, default=200, help="games a new anchor is rated before it is frozen")
    ap.add_argument("--recalibrate-anchors", action="store_true",
                    help="policy anchors are rated again for --calibrate-games games, then refrozen (after a runtime change)")
    ap.add_argument("--recalibrate-sigma", type=float, default=4.0, help="starting sigma of a recalibrating anchor")
    ap.add_argument("--refingerprint", action="store_true",
                    help="recompute live genomes' twin-check outcomes at start (after a runtime change)")
    ap.add_argument("--mutate-prompt", default="default", choices=["default", "creative"],
                    help="mutation prompt variant (genome/search/prompts.py MUTATE_TASKS); logged per child")
    ap.add_argument("--no-distinct-games", dest="distinct_games", action="store_false",
                    help="old matchmaking: maps from a global pointer, so a pair can replay (and re-count) a game")
    ap.add_argument("--no-bot-seeds", dest="bot_seeds", action="store_false",
                    help="policy anchors seeded per game instead of as deployed")
    ap.add_argument("--intel-branch", default="")
    ap.add_argument("--intel-every", type=float, default=600, help="seconds between intel fetches")
    ap.add_argument("--resume-from", default="", help="an earlier arena output directory (e.g. the last pushed "
                                                      "remote/genome copy of a died job): copied into --out to resume")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if args.resume_from and not (out / "state.json").exists():
        import shutil
        shutil.copytree(args.resume_from, out, dirs_exist_ok=True)
        # paths in state.json are relative to the output directory, except anchors (absolute, in the checkout)
        st = json.loads((out / "state.json").read_text())
        for m in st["members"].values():
            if m["kind"] == "anchor" and m.get("source") is None:
                m["path"] = _rebase(m["path"])
                for alt in (ROOT / "arena_policies" / Path(m["path"]).name, ROOT / Path(m["path"]).name):
                    if not Path(m["path"]).exists() and alt.exists():  # given inline again (service policies), or
                        m["path"] = str(alt)                           # copied to the checkout root (EC2 jobs)
            elif m["kind"] == "anchor":
                m["path"] = f"genomes/{Path(m['path']).name}"
        (out / "state.json").write_text(json.dumps(st))
    Arena(args).run()


def _rebase(path):
    """An absolute path from another checkout -> the same repository-relative path in this one."""
    parts = Path(path).parts
    # the repository-relative part starts at the first known top directory (arena_policies/ holds anchors a run was
    # given inline); a bare file name only if none is found
    tops = ("arena_policies", "policies", "genome")
    i = max((k for k, x in enumerate(parts[:-1]) if x in tops), default=len(parts) - 1)  # the last one: EC2 checkouts
    # live under .../genome/w/<job>/, so an earlier "genome" is part of the old root, not the repository path
    return str(ROOT.joinpath(*parts[i:]))


if __name__ == "__main__":
    main()
