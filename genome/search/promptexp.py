"""Prompt experiment 1 (genome/arenaa arenaa/PROMPT_EXP.md, 08c8e4d): A0 (today's link mutation, 7e40b6f) vs A1
(typed explicit link prompt, arenaa/prompts/mutate_link_v1.md) on the same (parent, link) cells, Haiku only.

    python3 -m genome.search.promptexp --out runs/promptexp --state arenaA-1=<dir> --state arenaA-3=<dir> \
        --arena-engine <sha> [--generate-only] [--report-only]

Runs in a worktree at 7e40b6f (its prompts and merge code are A0) with the runtime's lang.py. Each child: the 80
distinct games vs its parent and vs each anchor; each parent vs each anchor; the 40 null children (benchscore's
construction) vs each anchor and their parent. Logs go to children.jsonl / scores.jsonl; report.json at the end.
"""
import argparse
import ast
import json
import math
import os
import random
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from funsearch.evaluate import ROOT

from .. import lang
from . import edit, operators, prompts
from .claude import HAIKU, BudgetExceeded, Claude

ARENA_URL = os.environ.get("ARENA_URL", "https://138-201-121-171.sslip.io/arena")
ANCHORS = ("policies/candidates/style-gconv1.policy", "policies/candidates/tune-v20-L1.policy",
           "policies/candidates/rall2-ca4-lean-g.policy", "policies/v7.policy", "policies/opp-tune5-metadraft.policy",
           "policies/candidates/tune-v20-L1c.policy")
PARENTS = ("seed", "arenaA-1:A352", "arenaA-1:A344", "arenaA-1:A368", "arenaA-1:A354",
           "arenaA-3:A611", "arenaA-3:A659", "arenaA-3:A654", "arenaA-3:A662", "arenaA-3:A685",
           "arenaA-3:A690", "arenaA-3:A703", "arenaA-3:A701", "arenaA-3:A689")
NULL_PARENTS = ("seed", "arenaA-1:A352", "arenaA-1:A344", "arenaA-1:A368", "arenaA-1:A354")  # promptbench-2's
TYPES = ("T1", "T2", "T3", "T4", "T5")


# ---------------------------------------------------------------- arena service

def _http(url, data=None):
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"X-Arena-Client": "genome-search", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=130) as r:
        return json.loads(r.read())


def rate(engine, a, b, priority=1):
    """80 games (every map from both sides, bot seeds) of a vs b on the arena service: (a wins, games)."""
    body = json.dumps({"a": a, "b": b, "engine": engine, "fuel_mult": 1.0, "bot_seeds": True,
                       "priority": priority}).encode()
    m = _http(f"{ARENA_URL}/matches?wait=110", body)["match"]
    while m["status"] not in ("done", "failed", "cancelled"):
        m = _http(f"{ARENA_URL}/matches/{m['id']}?wait=110")
        m = m.get("match", m)
    if m["status"] != "done":
        raise RuntimeError(f"arena match {m['id']} {m['status']}")
    return m["result"]["a_wins"], m["result"]["games"]


def side(x):
    return {"text": x, "kind": "genome"} if "@gene" in x else f"repo:{x}"


# ---------------------------------------------------------------- links and cells

def trivial(gene_src):
    """A trivial wrapper (here, at_spawn, my tile ...): no parameters, one return, no numeric constant, no and/or,
    <= 2 calls."""
    fn = ast.parse(gene_src.strip()).body[0]
    if fn.args.args or len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return):
        return False
    nodes = list(ast.walk(fn.body[0]))
    if any(isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
           for n in nodes):
        return False
    if any(isinstance(n, ast.BoolOp) for n in nodes):
        return False
    return sum(isinstance(n, ast.Call) for n in nodes) <= 2


def eligible_links(src):
    g = lang.parse(src)
    _, _, genes = edit.segments(src)
    return sorted((a, b) for a, b, kind in g.edges()
                  if kind == "call" and a != b and not trivial(genes[g.genes[b].id]))


def make_cells(texts, links_per=8, seed_links=16):
    cells = []
    for p in PARENTS:
        links = eligible_links(texts[p])
        k = seed_links if p == "seed" else links_per
        for a, b in random.Random(f"links:{p}").sample(links, min(k, len(links))):
            cells.append({"parent": p, "a": a, "b": b})
    types = [TYPES[i % len(TYPES)] for i in range(len(cells))]
    random.Random("types").shuffle(types)
    for i, (c, t) in enumerate(zip(cells, types)):
        c.update(cell=i, type=t)
    return cells


# ---------------------------------------------------------------- the A1 prompt

def _language():
    text = prompts.LANGUAGE
    text = text[text.index("## A genome file"):]
    return "\n".join(l for l in text.splitlines() if not l.startswith("- Fuel:"))


A1_SYSTEM = f"""You edit one link of a program written in a small typed language (reference below). A link is a
caller gene and a gene it calls. You will be given the two genes' code and the signatures of the
genes around them. You rewrite those two genes. You do not see or change anything else.

# Language
{_language()}"""

TYPE_RULES = {
    "T1": "Rewrite both {A} and {B}: each must compute something different from now. No new genes.",
    "T2": "Create a new gene N between them: {A} calls N instead of {B}, and N calls {B} and changes or extends "
          "its result. {A} and N may change; {B} stays.",
    "T3": "Create a new gene N that computes something {A} and {B} do not compute now, and use it in {A}, {B} or "
          "both.",
    "T4": "{A} stops calling {B} and calls a new gene N instead: a different way to decide what {B} decides. {B} "
          "stays as it is for its other callers.",
    "T5": "Duplicate {B} as a new gene N adapted to {A}'s use (different parameters, thresholds or logic), and "
          "make {A} call N. {B} stays for its other callers.",
}


def _callers(genome):
    out = {}
    for g in genome.genes.values():
        for c in g.calls:
            out.setdefault(c, []).append(g.name)
    return {k: sorted(v) for k, v in out.items()}


def _table(genome, names):
    rows = [(prompts.signature(genome.genes[n]), genome.genes[n]) for n in names]
    w = max((len(s) for s, _ in rows), default=0) + 1
    return "\n".join(f"{s.ljust(w)}[{g.id}]  {g.desc}" for s, g in rows) or "(none)"


def _who(names):
    return " and ".join(", ".join(f"{n}()" for n in names).rsplit(", ", 1))


def a1_user(src, a, b, t):
    genome = lang.parse(src)
    _, _, genes = edit.segments(src)
    callers = _callers(genome)
    ga, gb = genome.genes[a], genome.genes[b]
    a_by = callers.get(a, []) or (["the fixed loop"] if a in edit.ENTRIES else [])
    b_other = [c for c in callers.get(b, []) if c != a]
    called = sorted((ga.calls | gb.calls) - {a, b})
    out = [f"# Link\n{a}  ->  {b}        ({a} calls {b})\n"]
    out.append(f"# Editable gene 1: {a}   [{ga.id}]   called by: {', '.join(a_by) or 'nobody'}\n"
               f"{genes[ga.id].strip()}\n")
    out.append(f"# Editable gene 2: {b}   [{gb.id}]   called by: {', '.join(callers.get(b, []))}\n"
               f"{genes[gb.id].strip()}\n")
    out.append("# Genes these two call (fixed; you may call them, and any other gene listed here)\n"
               + _table(genome, called) + "\n")
    out.append(f"# Other callers of {b} (fixed; they must still type-check)\n" + _table(genome, b_other) + "\n")
    a_call = ("the fixed loop" if a_by == ["the fixed loop"] else _who(a_by)) + f" as {prompts.signature(ga)}"
    b_call = (f"{_who(b_other)} as {prompts.signature(gb)}" if b_other else None)
    rule7 = (f"7. Break a caller: {a} is called by {a_call}" +
             (f", and {b} is called by {b_call}" if b_call else f", and {b} is called only by {a}") +
             f". If you change either signature, those calls must still type-check, so\n"
             f"   keep the old signature for them (for example: keep {b} as it is called and give {a} a new\n"
             f"   gene with the new signature).")
    b_callee = sorted(gb.calls - {a, b})
    rule4 = f"4. Stop calling a gene: {a} may stop calling {b}" + \
        (f", {b} may stop calling {b_callee[0]}, etc." if b_callee else ", etc.")
    entry = {a, b} & {"update", "after"}
    keeps_line = (f"Only update() may assign keeps, so {a}, {b} and new genes may read keeps but not assign them."
                  if not entry else "Only update() and after() may assign keeps; new genes may read keeps but "
                                    "not assign them.")
    out.append(f"""# Task
You are making one mutation of this program. The mutation may touch exactly two existing genes,
{a} and {b}, and may create new genes.

What you may do:
1. Rewrite the body of {a}, of {b}, or both: change conditions, thresholds, arithmetic,
   which genes and primitives they call, the order of tests, add or remove branches.
2. Change the parameters or return type of {a} or {b}.
3. Create new genes. A new gene can be called by {a}, by {b}, or by another new gene. It may
   call any gene listed in this prompt and any primitive.
{rule4}

What you may not do:
5. Change any gene other than {a} and {b} (the listed fixed genes stay exactly as they are).
6. Use a gene or primitive that is not listed in this prompt or in the language reference.
{rule7}

What counts as a mutation (checked automatically; otherwise the reply is rejected):
8. {TYPE_RULES[t].format(A=a, B=b)}
9. Changing only a description, renaming, reformatting, or reordering code without changing what it
   computes does not count as a change.
10. The result must type-check under the language reference. Every gene must return its declared
    type on every path.

# Reply
Reply with exactly one ```python code block and nothing outside it. The block contains:
- Each of {a} and {b} that you changed, in full, with its original id: @gene("{ga.id}", ...) and
  @gene("{gb.id}", ...). Update the description to one plain line saying what the gene now computes.
  Omit a gene you did not change.
- Each new gene, in full, as @gene("new", "<one plain line saying what it computes>",
  parents=["<id of the gene it was derived from, {ga.id} or {gb.id}>"]).
- Any new keep declaration your genes use (NAME: Type = value), above the genes. {keeps_line}
Do not repeat fixed genes. A new gene that nothing calls is deleted.""")
    return "\n".join(out)


# ---------------------------------------------------------------- the type checks

def _names_called(gene_src, gene_names):
    fn = ast.parse(gene_src.strip()).body[0]
    out = set()
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            out.add(n.func.id)
    return out


def _anon(gene_src):
    fn = ast.parse(gene_src.strip()).body[0]
    fn.decorator_list, fn.name = [], "_"
    return ast.dump(fn)


def type_check(t, parent_src, child_src, a_id, b_id):
    """None if the child is a valid mutation of type t on link a -> b (by gene ID), else the reason."""
    pg = lang.parse(parent_src)
    cg = lang.parse(child_src)
    _, _, psrc = edit.segments(parent_src)
    _, _, csrc = edit.segments(child_src)
    pid = {g.id: g for g in pg.genes.values()}
    cid = {g.id: g for g in cg.genes.values()}
    if a_id not in cid or b_id not in cid:
        return "the link's genes must stay in the program"
    A, B = cid[a_id], cid[b_id]
    a0, b0 = pid[a_id].name, pid[b_id].name
    new = [g for i, g in cid.items() if i not in pid]
    a_changed = edit.body_canon(psrc[a_id]) != edit.body_canon(csrc[a_id])
    b_changed = edit.body_canon(psrc[b_id]) != edit.body_canon(csrc[b_id])
    calls_ab = B.name in A.calls
    if t == "T1":
        if new:
            return f"T1 creates no new gene; this reply creates {', '.join(g.name for g in new)}"
        if not (a_changed and b_changed):
            return f"both {a0} and {b0} must compute something different from now; " \
                   f"{'only ' + (a0 if a_changed else b0) + ' changed' if a_changed or b_changed else 'neither changed'}"
        return None
    if not new:
        return "a new gene N must be created and called"
    if t in ("T2", "T4", "T5") and b_changed:
        return f"{b0} must stay exactly as it is"
    if t == "T2":
        if calls_ab:
            return f"{a0} must call the new gene N instead of calling {b0} directly"
        if not any(n.name in A.calls and B.name in n.calls for n in new):
            return f"{a0} must call a new gene N that calls {b0}"
        return None
    if t == "T3":
        before = (_names_called(psrc[a_id], None) | _names_called(psrc[b_id], None))
        used = [n for n in new if n.name in A.calls or n.name in B.calls]
        if not used:
            return f"the new gene N must be called by {a0} or {b0}"
        if not any(_names_called(csrc[n.id], None) - before for n in used):
            return f"the new gene N must compute something {a0} and {b0} do not compute now: it must call at " \
                   f"least one gene or primitive that {a0} and {b0} did not call"
        return None
    if t == "T4":
        if calls_ab:
            return f"{a0} must stop calling {b0}"
        if not any(n.name in A.calls and B.name not in n.calls for n in new):
            return f"{a0} must call a new gene N that does not call {b0}"
        return None
    if t == "T5":
        if calls_ab:
            return f"{a0} must call the new gene N instead of {b0}"
        for n in new:
            if b_id in n.parents and n.name in A.calls and _anon(csrc[n.id]) != _anon(psrc[b_id]):
                return None
        return f"{a0} must call a new gene N derived from {b0} (parents=[\"{b_id}\"]) whose code differs from {b0}'s"
    raise ValueError(t)


# ---------------------------------------------------------------- the experiment

class Exp:
    def __init__(self, a):
        self.a = a
        self.out = Path(a.out)
        (self.out / "genomes").mkdir(parents=True, exist_ok=True)
        self.states = dict(s.split("=", 1) for s in a.state)
        self.lock = threading.Lock()

    def parent(self, name):
        if name == "seed":
            return (ROOT / "genome/seeds/v23.genome").read_text(), None
        job, g = name.split(":")
        d = Path(self.states[job])
        m = json.loads((d / "state.json").read_text())["members"][g]
        return (d / m["path"]).read_text(), m

    def log(self, fname, rec):
        with self.lock, open(self.out / fname, "a") as f:
            f.write(json.dumps({"t": round(time.time()), **rec}) + "\n")

    def records(self, fname):
        p = self.out / fname
        return [json.loads(l) for l in open(p)] if p.exists() else []

    # ---- generation
    def generate(self, cells, texts, meta):
        done = {(r["cell"], r["arm"]) for r in self.records("children.jsonl")}
        claude = Claude(self.a.budget, opus_every=0)
        spent = sum(r.get("cost", 0) for r in self.records("children.jsonl"))
        claude.spent = spent

        def one(job):
            c, arm = job
            try:
                rec = self.child(c, arm, texts[c["parent"]], meta[c["parent"]], claude)
            except BudgetExceeded as e:
                print(f"cell {c['cell']} {arm}: {e}", flush=True)
                return
            self.log("children.jsonl", rec)
            print(f"cell {c['cell']} {arm} {c['type']}: {rec['error'] or 'ok'} ${claude.spent:.3f}", flush=True)

        jobs = [(c, arm) for c in cells for arm in ("A0", "A1") if (c["cell"], arm) not in done]
        with ThreadPoolExecutor(self.a.workers) as ex:
            list(ex.map(one, jobs))

    def child(self, c, arm, ptext, pmeta, claude):
        a, b = c["a"], c["b"]
        genome = lang.parse(ptext)
        a_id, b_id = genome.genes[a].id, genome.genes[b].id
        prefix = f"p{c['cell']}{'z' if arm == 'A0' else 'y'}"
        rec = {"cell": c["cell"], "arm": arm, "parent": c["parent"], "link": [a, b],
               "type": c["type"] if arm == "A1" else None, "model": HAIKU, "cost": 0.0, "calls": 0, "error": None}
        if arm == "A0":
            stats = (f"rating {pmeta['mu']:.1f} ± {pmeta['sigma']:.1f} over {pmeta['games']} games in the arena"
                     if pmeta else None)
            _, _, src_genes = edit.segments(ptext)
            system = [prompts.SYSTEM_BASE, prompts.MUTATE_TASK]
            user = prompts.mutate_user(genome, src_genes, [a, b], [(a, b, "call")], stats)
        else:
            system, user = [A1_SYSTEM], a1_user(ptext, a, b, c["type"])
        tries = 2 if arm == "A1" else 1
        for k in range(tries):
            text, model, cost, info = claude.ask(system, user, model=HAIKU)
            rec["cost"] += cost
            rec["calls"] += 1
            rec.setdefault("llm", []).append(info)
            if text is None:
                rec["error"] = "refusal"
                return rec
            try:
                child, st = operators.apply_mutation(ptext, text, {a_id, b_id}, prefix)
            except (edit.EditError, lang.GenomeError) as e:
                rec["error"] = f"{type(e).__name__}: {e}"
                rec["reply"] = text[-4000:]
                return rec
            if arm == "A1":
                why = type_check(c["type"], ptext, child, a_id, b_id)
                rec.setdefault("check", []).append(why or "ok")
                if why:
                    rec["error"] = f"type check: {why}"
                    rec["reply"] = text[-4000:]
                    user = (f"{user}\n\n# Your previous reply\n{text.strip()}\n\nIt was rejected: {why}.\n"
                            f"Reply again, following the rules above.")
                    continue
            rec["error"] = None
            rec.pop("reply", None)
            fname = f"genomes/c{c['cell']:03d}-{arm}{'-' + c['type'] if arm == 'A1' else ''}.genome"
            (self.out / fname).write_text(child)
            rec.update(file=fname, retried=rec["calls"] > 1, b_changed=b_id in st["genes_changed"], **st)
            return rec
        return rec

    # ---- scoring
    def score(self, cells, texts):
        done = {(r["genome"], r["opponent"]) for r in self.records("scores.jsonl")}
        tasks = []

        def want(gid, text, opp, opp_text, meta):
            if (gid, opp) not in done:
                tasks.append((gid, text, opp, opp_text, meta))

        for p in PARENTS:
            for anc in ANCHORS:
                want(f"parent:{p}", texts[p], Path(anc).stem, anc, {"kind": "parent", "parent": p})
        from . import operators as ops
        for p in NULL_PARENTS:
            for k in range(self.a.null):
                ch = ops.tune(texts[p], random.Random(f"{p}:{k}"), sigma=self.a.null_sigma)
                if ch.source is None:
                    continue
                gid = f"null:{p}:{k}"
                (self.out / "null").mkdir(exist_ok=True)
                (self.out / "null" / f"{gid.replace(':', '_')}.genome").write_text(ch.source)
                meta = {"kind": "null", "parent": p, "cell": k}
                for anc in ANCHORS:
                    want(gid, ch.source, Path(anc).stem, anc, meta)
                want(gid, ch.source, "parent", texts[p], meta)
        for r in self.records("children.jsonl"):
            if r.get("error"):
                continue
            text = (self.out / r["file"]).read_text()
            gid = f"c{r['cell']}:{r['arm']}"
            meta = {"kind": "child", "parent": r["parent"], "cell": r["cell"], "arm": r["arm"], "type": r["type"]}
            for anc in ANCHORS:
                want(gid, text, Path(anc).stem, anc, meta)
            want(gid, text, "parent", texts[r["parent"]], meta)
        print(f"{len(tasks)} matches to play", flush=True)

        def play(t):
            gid, text, opp, opp_text, meta = t
            for attempt in range(6):
                try:
                    w, n = rate(self.a.arena_engine, side(text), side(opp_text), self.a.priority)
                    break
                except Exception as e:
                    print(f"{gid} vs {opp}: {type(e).__name__}: {e}", flush=True)
                    time.sleep(30 * (attempt + 1))
            else:
                return
            self.log("scores.jsonl", {"genome": gid, "opponent": opp, "wins": w, "games": n, **meta})

        with ThreadPoolExecutor(self.a.workers) as ex:
            list(ex.map(play, tasks))

    # ---- report
    def report(self, cells):
        sc = {}
        for r in self.records("scores.jsonl"):
            sc.setdefault(r["genome"], {})[r["opponent"]] = r["wins"]
        stems = [Path(x).stem for x in ANCHORS]

        def anchor_sum(gid):
            s = sc.get(gid, {})
            return sum(s[x] for x in stems) if all(x in s for x in stems) else None

        par = {p: anchor_sum(f"parent:{p}") for p in PARENTS}
        nulls = []
        for gid in sc:
            if gid.startswith("null:"):
                p = gid.split(":")[1]
                v = anchor_sum(gid)
                if v is not None and par[p] is not None:
                    nulls.append(v - par[p])
        nulls.sort()
        p95 = nulls[min(len(nulls) - 1, math.ceil(0.95 * len(nulls)) - 1)] if nulls else None
        kids = {(r["cell"], r["arm"]): r for r in self.records("children.jsonl")}
        better, per = {}, {}
        for c in cells:
            for arm in ("A0", "A1"):
                r = kids.get((c["cell"], arm))
                gid = f"c{c['cell']}:{arm}"
                v = anchor_sum(gid) if r and not r.get("error") else None
                d = v - par[c["parent"]] if v is not None and par[c["parent"]] is not None else None
                twin = d is not None and all(sc[gid][x] == sc[f"parent:{c['parent']}"][x] for x in stems)
                better[(c["cell"], arm)] = d is not None and p95 is not None and d > p95 and not twin
                per.setdefault(arm, []).append({"cell": c["cell"], "type": c["type"], "rec": r, "diff": d,
                                                "twin": twin, "vs_parent": sc.get(gid, {}).get("parent"),
                                                "better": better[(c["cell"], arm)]})
        b = sum(better[(c["cell"], "A1")] and not better[(c["cell"], "A0")] for c in cells)
        cc = sum(better[(c["cell"], "A0")] and not better[(c["cell"], "A1")] for c in cells)
        n = b + cc
        p_mcnemar = sum(math.comb(n, k) for k in range(b, n + 1)) / 2 ** n if n else 1.0

        def summary(rows):
            recs = [x["rec"] for x in rows if x["rec"]]
            ok = [x for x in rows if x["rec"] and not x["rec"].get("error")]
            diffs = sorted(x["diff"] for x in ok if x["diff"] is not None)
            cost = sum(r.get("cost", 0) for r in recs)
            vp = [x["vs_parent"] for x in ok if x["vs_parent"] is not None]
            return {
                "cells": len(rows), "better": sum(x["better"] for x in rows),
                "better_share": round(sum(x["better"] for x in rows) / max(1, len(rows)), 3),
                "valid": len(ok), "invalid": sum(1 for r in recs if r.get("error") and "type check" not in r["error"]),
                "rejected": sum(1 for r in recs if r.get("error") and "type check" in r["error"]),
                "retried": sum(1 for r in recs if r.get("calls", 1) > 1),
                "twins": sum(x["twin"] for x in rows),
                "both_changed": sum(1 for x in ok if len(x["rec"]["genes_changed"]) >= 2),
                "added_gene": sum(1 for x in ok if x["rec"]["genes_added"]),
                "lines_mean": round(sum(x["rec"]["lines_changed"] for x in ok) / max(1, len(ok)), 1),
                "diff_mean": round(sum(diffs) / len(diffs), 2) if diffs else None,
                "diff_p90": diffs[min(len(diffs) - 1, math.ceil(0.9 * len(diffs)) - 1)] if diffs else None,
                "vs_parent_rate": round(sum(vp) / (80 * len(vp)), 3) if vp else None,
                "cost": round(cost, 4), "cost_per_child": round(cost / max(1, len(recs)), 5),
            }

        rep = {"null_n": len(nulls), "null_p95": p95, "null": nulls, "parents_anchor_wins": par,
               "arms": {arm: summary(rows) for arm, rows in per.items()},
               "by_type_A1": {t: summary([x for x in per.get("A1", []) if x["type"] == t]) for t in TYPES},
               "mcnemar": {"A1_only": b, "A0_only": cc, "p_one_sided": round(p_mcnemar, 4)}}
        (self.out / "report.json").write_text(json.dumps(rep, indent=1))
        print(json.dumps({k: v for k, v in rep.items() if k != "null"}, indent=1))
        return rep

    def run(self):
        texts, meta = {}, {}
        for p in PARENTS:
            texts[p], meta[p] = self.parent(p)
        cells = make_cells(texts, self.a.links, self.a.seed_links)
        (self.out / "cells.json").write_text(json.dumps(cells, indent=0))
        if not self.a.report_only:
            self.generate(cells, texts, meta)
            if not self.a.generate_only:
                self.score(cells, texts)
        if not self.a.generate_only:
            self.report(cells)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", action="append", default=[], help="job=dir: arena state holding the parents")
    ap.add_argument("--arena-engine", required=True)
    ap.add_argument("--budget", type=float, default=0.40)
    ap.add_argument("--links", type=int, default=8)
    ap.add_argument("--seed-links", type=int, default=16)
    ap.add_argument("--null", type=int, default=8)
    ap.add_argument("--null-sigma", type=float, default=0.02)
    ap.add_argument("--priority", type=int, default=1)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--generate-only", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    Exp(a).run()


if __name__ == "__main__":
    main()
