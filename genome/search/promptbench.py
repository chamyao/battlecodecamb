"""Prompt bench: a meta loop over mutation prompts, outside the arenas (design: genome/arenaa arenaa/PROMPTBENCH.md).

    python3 -m genome.search.promptbench --out $OUT --parents-from arenaA-1/arena --rounds 1 --budget 0.8

One round: every prompt variant writes the same (parent, link) children (paired design): the seed plus the
--parents longest-lived live genomes of an arena state, --links one-edge links each picked once with a fixed seed,
Haiku only. Invalid children and behavioural twins of their parent are failures. Each valid child plays its parent
over the 80 distinct games (every map from both sides; games are fixed by map and side, policies seeded as deployed); children at >= --prodigy-screen also play every fixed anchor
(--games each; the parent's anchor rates are measured once on the same seed).

Measures per prompt: prodigy rate (one-sided 95% lower bound of the child-vs-parent win rate above 0.5, i.e.
>= 48/80) and the prodigies' gain vs the anchors over their parents; 90th percentile and max child-vs-parent
win rate (failures count as 0.5); twin and invalid rates; lines changed; genes added; $ per child.

Outer loop (--rounds > 1): keep the top --keep prompts; Opus writes --new new variants from the round's table.
Each round's winner is re-tested on --retest-parents fresh parents (--retest-from, an arena state) and fresh
seeds; the result goes to rounds.jsonl as "retest".

Logs in --out: prompts.jsonl, children.jsonl, games.jsonl, rounds.jsonl, genomes/.
"""
import argparse
import json
import math
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from funsearch.evaluate import MAPS, ROOT

from .. import build as gbuild
from .. import lang
from . import edit, operators, prompts
from .claude import HAIKU, OPUS, BudgetExceeded, Claude
from .score import Scorer

ANCHORS = ("policies/candidates/style-gconv1.policy", "policies/candidates/tune-v20-L1.policy",
           "policies/candidates/rall2-ca4-lean-g.policy", "policies/v7.policy", "policies/opp-tune5-metadraft.policy")
TWIN_SEED = 4_000_037
GAME_SEED = 1_000_003
RETEST_SEED = 1_500_007
LINK_SEED = 7

AIM = prompts._AIM
ROUND1 = {
    "default": AIM,
    "creative": prompts._CREATIVE,
    "missing": "Add a behaviour for a situation these genes do not handle yet: find a case the current rules ignore "
               "or handle badly (a threat, an opportunity, a phase of the game) and write the genes that handle it.",
    "weights": "Change what these genes value: reweigh the terms of the decision, add a new consideration to the "
               "score, or remove one that misleads it, so the champion prefers different options than it does now.",
    "mechanism": "Replace one rule in these genes with a different mechanism that serves the same purpose (for "
                 "example a threshold replaced by a comparison of two estimates, or a fixed target by a computed "
                 "one), rather than adjusting its numbers.",
    "temperament": "Make the champion bolder or more careful in the situations these genes decide, whichever you "
                   "judge is the bigger weakness, and make the change decisively.",
    "helper": "Write a new helper gene that computes something the genome does not know yet (an estimate, a count, "
              "a tile set, a prediction) and use it in these genes to make a better decision.",
    "simplify": "Simplify drastically: rewrite these genes to do their job with much less code, dropping rules that "
                "rarely matter, so the remaining logic is clearer and cheaper in fuel.",
}


def task_text(paragraph):
    """The full mutation task with the 'what kind of change' paragraph replaced."""
    return prompts.MUTATE_TASK.replace(AIM, paragraph.strip())


def prodigy_min(n):
    """Smallest win count whose one-sided 95% lower bound (normal approx.) is above 0.5."""
    return next(k for k in range(n + 1) if (k / n - 1.645 * math.sqrt(0.25 / n)) > 0.5)


class Bench:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out)
        (self.out / "genomes").mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.claude = Claude(a.budget, opus_every=0)
        self.claude.spent = sum(r.get("cost", 0.0) for r in self.read("children")) + \
            sum(r.get("cost", 0.0) for r in self.read("prompts"))
        self.sc = Scorer([], threads=1, bot_seeds=True)
        self.maps = sorted(MAPS)
        self.cache = {}  # (spec a, spec b, seed, games) -> stats

    def write(self, kind, rec):
        with self.lock, open(self.out / f"{kind}.jsonl", "a") as f:
            f.write(json.dumps({"t": round(time.time()), **rec}) + "\n")

    def read(self, kind):
        p = self.out / f"{kind}.jsonl"
        return [json.loads(l) for l in open(p)] if p.exists() else []

    def play(self, a, b, seed, games):
        """Games are fixed by map and side, so a pair's distinct games are every map once from each side (80);
        `games` above that only repeats them and is capped."""
        n = min(games, 2 * len(self.maps))
        key = (a, b, n)
        if key not in self.cache:
            self.cache[key] = self.sc.play(a, b, seed, n, threads=1, maps=self.maps[:n // 2])
        return self.cache[key]

    def fingerprint(self, spec):
        outs = []
        for anc in ANCHORS[:2]:
            st = self.play(spec, self.sc._spec(str(ROOT / anc)), TWIN_SEED, 8)
            outs.append((st.get("results"), st["a_gems"], st["b_gems"]))
        return json.dumps(outs)

    # ---- parents and links
    def parents(self, state_dir, n, exclude=(), with_seed=True):
        d = Path(state_dir)
        s = json.loads((d / "state.json").read_text())
        live = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"] and m["name"] not in exclude]
        out = [("seed", Path(self.a.seed).read_text())] if with_seed else []
        out += [(f"{d.parent.name}:{m['name']}", (d / m["path"]).read_text())
                for m in sorted(live, key=lambda m: -m["games"])[:n]]
        return out

    def links(self, parents, k, seed):
        rng = random.Random(seed)
        cells = []
        for name, text in parents:
            g = lang.parse(text)
            edges = g.edges() or [("score", "score", "self")]
            for e in rng.sample(edges, min(k, len(edges))):
                cells.append((name, text, e))
        return cells

    # ---- one child
    def child(self, rnd, pid, task, cell, idx, seed):
        pname, ptext, edge = cell
        rec = {"round": rnd, "prompt": pid, "parent": pname, "link": list(edge), "cell": idx}
        try:
            c = operators.mutate(ptext, self.claude, random.Random(idx), f"p{rnd}{pid[:3]}{idx}x", None,
                                 edges=[tuple(edge)], task=task, model=HAIKU)
        except BudgetExceeded:
            raise
        except Exception as e:
            rec.update(error=f"{type(e).__name__}: {e}", cost=0.0)
            return rec
        rec.update(cost=c.cost, error=c.error, lines=c.log.get("lines_changed"),
                   genes_added=len(c.log.get("genes_added", [])), out_tokens=c.log.get("llm", {}).get("out"))
        if c.source is None:
            return rec
        path = self.out / "genomes" / f"r{rnd}-{pid}-{idx}.genome"
        path.write_text(c.source)
        try:
            spec = f"genome:{gbuild.build(c.source)}"
            pspec = f"genome:{gbuild.build(ptext)}"
            if self.fingerprint(spec) == self.fingerprint(pspec):
                rec["error"] = "behavioural twin"
                return rec
            st = self.play(spec, pspec, seed, self.a.games)
            rec.update(wins=st["a_wins"], games=st["games"], win_rate=st["a_wins"] / st["games"])
            self.write("games", {"round": rnd, "prompt": pid, "cell": idx, "vs": "parent", "results": st.get("results"),
                                 "wins": st["a_wins"], "games": st["games"]})
            if rec["win_rate"] >= self.a.prodigy_screen:
                gains = {}
                for anc in ANCHORS:
                    aspec = self.sc._spec(str(ROOT / anc))
                    cs, ps = self.play(spec, aspec, seed, self.a.games), self.play(pspec, aspec, seed, self.a.games)
                    gains[Path(anc).stem] = round((cs["a_wins"] - ps["a_wins"]) / cs["games"], 3)
                    self.write("games", {"round": rnd, "prompt": pid, "cell": idx, "vs": Path(anc).stem,
                                         "results": cs.get("results"), "wins": cs["a_wins"], "games": cs["games"],
                                         "parent_wins": ps["a_wins"]})
                rec["anchor_gain"] = gains
                rec["anchor_gain_mean"] = round(sum(gains.values()) / len(gains), 3)
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        return rec

    def measures(self, recs):
        n = len(recs)
        kmin = prodigy_min(self.a.games)
        ok = [r for r in recs if not r.get("error")]
        wr = sorted([r.get("win_rate", 0.5) if not r.get("error") else 0.5 for r in recs])
        prod = [r for r in ok if r.get("wins", 0) >= kmin]
        cost = sum(r.get("cost", 0.0) for r in recs)
        return {"children": n, "valid": len(ok), "prodigies": len(prod), "prodigy_rate": round(len(prod) / n, 3) if n else 0,
                "prodigy_anchor_gain": round(sum(r.get("anchor_gain_mean", 0) for r in prod) / len(prod), 3) if prod else None,
                "p90": wr[int(0.9 * (n - 1))] if n else None, "max": wr[-1] if n else None,
                "mean_vs_parent": round(sum(r["win_rate"] for r in ok) / len(ok), 3) if ok else None,
                "twin_rate": round(sum(1 for r in recs if r.get("error") == "behavioural twin") / n, 3) if n else 0,
                "invalid_rate": round(sum(1 for r in recs if r.get("error") and r["error"] != "behavioural twin") / n, 3) if n else 0,
                "lines_mean": round(sum(r.get("lines") or 0 for r in ok) / len(ok), 1) if ok else None,
                "genes_added_mean": round(sum(r.get("genes_added") or 0 for r in ok) / len(ok), 2) if ok else None,
                "usd_per_child": round(cost / n, 5) if n else 0, "prodigy_min_wins": kmin}

    def run_prompts(self, rnd, variants, cells, seed, tag):
        """All children of all variants on all cells; returns {pid: measures}."""
        done = {(r["prompt"], r["cell"]) for r in self.read("children") if r["round"] == rnd and r.get("tag") == tag}
        jobs = [(pid, idx, cell) for pid in variants for idx, cell in enumerate(cells) if (pid, idx) not in done]

        def one(j):
            pid, idx, cell = j
            rec = self.child(rnd, pid, task_text(variants[pid]), cell, idx, seed)
            rec["tag"] = tag
            self.write("children", rec)
            print(f"[r{rnd} {tag}] {pid} cell {idx} ({cell[0]}, {cell[2][0]}->{cell[2][1]}): "
                  f"{rec.get('error') or rec.get('win_rate')} ${self.claude.spent:.3f}", flush=True)
            return rec

        with ThreadPoolExecutor(self.a.workers) as ex:
            list(ex.map(one, jobs))
        recs = [r for r in self.read("children") if r["round"] == rnd and r.get("tag") == tag]
        return {pid: self.measures([r for r in recs if r["prompt"] == pid]) for pid in variants}

    def new_variants(self, rnd, variants, table, k):
        rows = "\n".join(f"- {pid}: {json.dumps(table[pid])}\n  text: {variants[pid]}" for pid in variants)
        system = [prompts.SYSTEM_BASE, f"""# Your task: write better mutation instructions
A mutation prompt asks a model to change the two genes on one link of a genome. The part that varies is one
paragraph telling it what kind of change to make. Below are the paragraphs tried this round with their results on a
paired benchmark: each wrote the same {table[next(iter(table))]['children']} children; a prodigy is a child that beats
its parent clearly (>= {table[next(iter(table))]['prodigy_min_wins']}/{self.a.games} games); p90/max are child-vs-parent
win rates (failures count 0.5); twins are children that play exactly like their parent.

Write {k} new paragraphs that should produce more prodigies: combine or mutate the best ones, or try new
instructions. Each at most 3 sentences, written to the mutating model. Reply with a JSON object
{{"name": "paragraph", ...}} with {k} short lowercase names, in one ```json block, then nothing else."""]
        text, model, cost, info = self.claude.ask(system, f"Round {rnd} results:\n{rows}\n\nWrite the {k} paragraphs.",
                                                  model=OPUS)
        m = re.search(r"```json\s*\n(.*?)```", text or "", re.S)
        new = json.loads(m.group(1)) if m else {}
        out = {}
        for name, para in list(new.items())[:k]:
            pid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:24] or f"v{len(out)}"
            while pid in variants or pid in out:
                pid += "x"
            out[pid] = para
            self.write("prompts", {"round": rnd + 1, "id": pid, "text": para, "origin": "opus", "cost": cost / max(1, k)})
        return out

    def run(self):
        a = self.a
        parents = self.parents(a.parents_from, a.parents)
        cells = self.links(parents, a.links, LINK_SEED)
        self.write("rounds", {"event": "setup", "parents": [p[0] for p in parents],
                              "cells": [(c[0], list(c[2])) for c in cells]})
        known = {}
        for r in self.read("prompts"):
            known.setdefault(r["round"], {})[r["id"]] = r["text"]
        variants = known.get(1) or dict(ROUND1)
        if 1 not in known:
            for pid, t in variants.items():
                self.write("prompts", {"round": 1, "id": pid, "text": t, "origin": "round1", "cost": 0.0})
        for rnd in range(1, a.rounds + 1):
            variants = known.get(rnd, variants)
            try:
                table = self.run_prompts(rnd, variants, cells, GAME_SEED, "bench")
            except BudgetExceeded as e:
                print(f"budget: {e}", flush=True)
                break
            ranked = sorted(table, key=lambda p: (-table[p]["prodigy_rate"], -(table[p]["p90"] or 0),
                                                  -(table[p]["mean_vs_parent"] or 0)))
            self.write("rounds", {"event": "round", "round": rnd, "table": table, "ranked": ranked})
            print(f"round {rnd}: " + "; ".join(f"{p} {table[p]['prodigies']}/{table[p]['children']} "
                                                f"p90 {table[p]['p90']}" for p in ranked), flush=True)
            winner = ranked[0]
            if a.retest_from:
                used = {p[0].split(":")[-1] for p in parents}
                fresh = self.parents(a.retest_from, a.retest_parents, exclude=used, with_seed=False)
                rcells = self.links(fresh, a.links, LINK_SEED + rnd)
                try:
                    rt = self.run_prompts(rnd, {winner: variants[winner], "default": variants.get("default", AIM)}
                                          if winner != "default" else {winner: variants[winner]},
                                          rcells, RETEST_SEED + rnd, "retest")
                    self.write("rounds", {"event": "retest", "round": rnd, "winner": winner, "table": rt,
                                          "parents": [p[0] for p in fresh]})
                    print(f"retest round {rnd}: {json.dumps(rt)}", flush=True)
                except BudgetExceeded as e:
                    print(f"budget: {e}", flush=True)
                    break
            if rnd < a.rounds:
                keep = {p: variants[p] for p in ranked[:a.keep]}
                try:
                    new = self.new_variants(rnd, variants, table, a.new)
                except BudgetExceeded as e:
                    print(f"budget: {e}", flush=True)
                    break
                for pid, t in keep.items():
                    self.write("prompts", {"round": rnd + 1, "id": pid, "text": t, "origin": "kept", "cost": 0.0})
                known[rnd + 1] = {**keep, **new}
        print(f"done: spent ${self.claude.spent:.3f}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--parents-from", required=True, help="arena output dir whose live genomes are the parents")
    ap.add_argument("--seed", default=str(ROOT / "genome/seeds/v23.genome"))
    ap.add_argument("--parents", type=int, default=4, help="longest-lived live genomes besides the seed")
    ap.add_argument("--links", type=int, default=8)
    ap.add_argument("--games", type=int, default=80, help="games per pair (80 = every map from both sides; more "
                                                         "would only repeat the same games)")
    ap.add_argument("--prodigy-screen", type=float, default=0.60)
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--keep", type=int, default=2)
    ap.add_argument("--new", type=int, default=6)
    ap.add_argument("--retest-from", default="", help="arena output dir for the winner's fresh parents")
    ap.add_argument("--retest-parents", type=int, default=5)
    ap.add_argument("--budget", type=float, default=0.8)
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    Bench(a).run()


if __name__ == "__main__":
    main()
