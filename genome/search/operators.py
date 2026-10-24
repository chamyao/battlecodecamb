"""Genome operators (docs/GENOME.md, Identity/crossover and Mutation):

- mutate():      edge-scoped Claude mutation: only the genes on the chosen edge(s) may change; new genes
                 get fresh IDs and parents; uncalled genes are removed; every other gene is verified unchanged.
- crossover():   mechanical crossover by gene ID with dependency closure (no LLM).
- llm_cross():   Claude crossover by meaning, for unrelated parents.
- tune():        evolution-strategy step on numeric constants (no LLM).

Each returns a Child: source (or None) + error + a log dict (edges, genes/lines changed, added genes).
"""
import ast
import math
from dataclasses import dataclass, field

from .. import lang
from . import edit, prompts


@dataclass
class Child:
    source: str | None
    op: str
    error: str | None = None
    log: dict = field(default_factory=dict)
    model: str = ""
    cost: float = 0.0


# ---------------------------------------------------------------- edge-scoped mutation

def pick_edges(genome, rng, two_prob=0.25):
    """One edge, sometimes two (distinct). A genome without edges mutates score alone."""
    edges = genome.edges()
    # the fixed loop links the entry genes: consider() gates what score() sees; update() runs before and
    # after() after the scoring passes, so they are targetable even when no call or data link reaches them
    for entry in ("consider", "update", "after"):
        if entry in genome.genes and not any(entry in (a, b) for a, b, _ in edges):
            edges.append(("score", entry, "loop"))
    if not edges:
        return [("score", "score", "self")]
    n = 2 if len(edges) > 1 and rng.random() < two_prob else 1
    return rng.sample(edges, n)


def apply_mutation(parent_src, reply, editable_ids, prefix):
    """Merge a mutation reply into the parent. Returns (child source, log). Raises EditError/GenomeError."""
    block = edit.extract_genome_block(reply or "")
    if block is None:
        raise edit.EditError("no code block in reply")
    r_keeps, r_genes = edit.reply_parts(block)
    header, keeps, genes = edit.segments(parent_src)
    keeps, genes = dict(keeps), dict(genes)
    for name, text in r_keeps:
        if name in keeps:
            if edit.canon(keeps[name]) != edit.canon(text):
                raise edit.EditError(f"changed existing keep {name}")
        else:
            keeps[name] = text
    new_id = edit.IdMaker(prefix, genes)
    replaced, added = {}, []
    for gid, name, text in r_genes:
        if gid in editable_ids:
            if gid in replaced:
                raise edit.EditError(f"gene {gid} given twice")
            replaced[gid] = text
        elif gid in genes:
            if edit.body_canon(genes[gid]) != edit.body_canon(text):
                raise edit.EditError(f"modified fixed gene {gid} ({name})")
        else:
            added.append(text)
    for gid, text in replaced.items():
        # a mutated gene keeps its identity: same ID and parents (its description may change)
        fn = ast.parse(genes[gid]).body[0]
        ps = [kw for kw in fn.decorator_list[0].keywords if kw.arg == "parents"]
        genes[gid] = edit.set_header(text, gid=gid, parents=[e.value for e in ps[0].value.elts] if ps else [])
    # new genes: fresh IDs; parents must name existing genes (default: the edge's genes)
    anchor = max((list(genes).index(g) for g in editable_ids if g in genes), default=len(genes) - 1)
    items = list(genes.items())
    fresh = []
    for text in added:
        fn = ast.parse(text).body[0]
        ps = [kw for kw in fn.decorator_list[0].keywords if kw.arg == "parents"]
        parents = [e.value for e in ps[0].value.elts if isinstance(e, ast.Constant)] if ps else []
        parents = [p for p in parents if p in genes] or sorted(editable_ids)
        nid = new_id()
        fresh.append((nid, edit.set_header(text, gid=nid, parents=parents)))
    items[anchor + 1:anchor + 1] = fresh  # tandem: new genes sit next to the genes they came from
    child = edit.assemble(header, keeps, dict(items))
    lang.parse(child)  # type check before pruning (errors name the real problem)
    child, removed = edit.prune(child)
    lang.parse(child)
    stats = edit.diff_stats(parent_src, child)
    outside = [g for g in stats["genes_changed"] if g not in editable_ids]
    if outside:  # cannot happen through the merge above; the diff is the contract
        raise edit.EditError(f"genes outside the edge changed: {outside}")
    if not stats["genes_changed"] and not stats["genes_added"] and not stats["genes_removed"]:
        raise edit.EditError("no change")
    stats["pruned"] = removed
    return child, stats


def mutate(parent_src, claude, rng, prefix, stats_line=None, two_prob=0.25, notes_fn=None, variant="default"):
    """notes_fn(names of the editable genes) -> extra text for the prompt (e.g. ladder evidence)."""
    genome = lang.parse(parent_src)
    edges = pick_edges(genome, rng, two_prob)
    names = []
    for a, b, _ in edges:
        for n in (a, b):
            if n not in names:
                names.append(n)
    editable_ids = {genome.genes[n].id for n in names}
    _, _, src_genes = edit.segments(parent_src)
    if notes_fn:
        stats_line = (stats_line or "") + notes_fn(names)
    user = prompts.mutate_user(genome, src_genes, names, edges, stats_line)
    text, model, cost, info = claude.ask([prompts.SYSTEM_BASE, prompts.MUTATE_TASKS[variant]], user)
    log = {"edges": [list(e) for e in edges], "n_edges": len(edges), "editable": sorted(editable_ids), "llm": info,
           "prompt": variant}
    if text is None:
        return Child(None, "mutate", "refusal", log, model, cost)
    try:
        child, stats = apply_mutation(parent_src, text, editable_ids, prefix)
    except (edit.EditError, lang.GenomeError) as e:
        log["reply"] = text[-6000:]
        return Child(None, "mutate", f"{type(e).__name__}: {e}", log, model, cost)
    log.update(stats)
    return Child(child, "mutate", None, log, model, cost)


# ---------------------------------------------------------------- crossover by gene ID

def relatedness(a_src, b_src):
    """Share of gene IDs the two genomes have in common (Jaccard)."""
    a, b = set(edit.segments(a_src)[2]), set(edit.segments(b_src)[2])
    return len(a & b) / max(1, len(a | b))


def crossover(a_src, b_src, rng, tries=20):
    """For each gene ID pick either parent's version, then keep the dependency closure from the entry
    genes (calls resolve through the caller's parent, by ID). Retries if the result does not type-check
    or equals a parent."""
    ga, gb = lang.parse(a_src), lang.parse(b_src)
    sa, sb = edit.segments(a_src), edit.segments(b_src)
    by = {"A": (ga, sa[2]), "B": (gb, sb[2])}
    shared = sorted(set(sa[2]) & set(sb[2]))
    differ = [i for i in shared if edit.body_canon(sa[2][i]) != edit.body_canon(sb[2][i])]
    last_err = "parents identical where they share genes"
    for _ in range(tries if differ or set(sa[2]) ^ set(sb[2]) else 0):
        coin = {i: rng.choice("AB") for i in set(sa[2]) | set(sb[2])}
        chosen = {}  # id -> side

        def pick(gid, default_side):
            side = coin[gid] if gid in by[coin[gid]][1] else default_side
            return side

        todo = []
        for entry in edit.ENTRIES:
            for side in ("A", "B"):
                g = by[side][0].genes.get(entry)
                if g is not None:
                    todo.append((g.id, pick(g.id, side)))
                    break
        while todo:
            gid, side = todo.pop()
            if gid in chosen:
                continue
            chosen[gid] = side
            gn = by[side][0]
            g = next(x for x in gn.genes.values() if x.id == gid)
            for c in g.calls:
                cid = gn.genes[c].id
                todo.append((cid, pick(cid, side)))
        upd_side = next((s for i, s in chosen.items() if by[s][0].ids().get(i) == "update"), "A")
        keeps = dict(sb[1] if upd_side == "B" else sa[1])
        for k, v in (sa[1] if upd_side == "B" else sb[1]).items():
            keeps.setdefault(k, v)
        order = list(sa[2]) + [i for i in sb[2] if i not in sa[2]]
        genes = {i: by[chosen[i]][1][i] for i in order if i in chosen}
        child = edit.assemble(sa[0], keeps, genes)
        try:
            lang.parse(child)
            child, removed = edit.prune(child)
        except lang.GenomeError as e:
            last_err = f"GenomeError: {e}"
            continue
        if edit.body_canon_genome(child) in (edit.body_canon_genome(a_src), edit.body_canon_genome(b_src)):
            last_err = "child equals a parent"
            continue
        from_b = sorted(i for i, s in chosen.items() if s == "B" and i in shared and i in differ)
        log = {"relatedness": round(relatedness(a_src, b_src), 3), "differing_genes": len(differ),
               "from_b": from_b, "genes": len(genes)}
        log.update({k: v for k, v in edit.diff_stats(a_src, child).items()})
        return Child(child, "cross", None, log)
    return Child(None, "cross", last_err, {"relatedness": round(relatedness(a_src, b_src), 3),
                                            "differing_genes": len(differ)})


def llm_cross(a_src, a_score, b_src, b_score, claude, prefix):
    user = prompts.cross_user(a_src, a_score, b_src, b_score)
    text, model, cost, info = claude.ask([prompts.SYSTEM_BASE, prompts.CROSS_TASK], user)
    log = {"relatedness": round(relatedness(a_src, b_src), 3), "llm": info}
    if text is None:
        return Child(None, "llm_cross", "refusal", log, model, cost)
    try:
        block = edit.extract_genome_block(text)
        if block is None:
            raise edit.EditError("no code block in reply")
        r_keeps, r_genes = edit.reply_parts(block)
        known = set(edit.segments(a_src)[2]) | set(edit.segments(b_src)[2])
        new_id = edit.IdMaker(prefix, known)
        seen, genes = set(), {}
        for gid, name, t in r_genes:
            if gid in known and gid not in seen:
                seen.add(gid)
                genes[gid] = t
            else:
                fn = ast.parse(t).body[0]
                ps = [kw for kw in fn.decorator_list[0].keywords if kw.arg == "parents"]
                parents = [e.value for e in ps[0].value.elts if isinstance(e, ast.Constant)] if ps else []
                nid = new_id()
                genes[nid] = edit.set_header(t, gid=nid, parents=[p for p in parents if p in known])
        child = edit.assemble(edit.segments(a_src)[0], dict(r_keeps), genes)
        lang.parse(child)
        child, removed = edit.prune(child)
    except (edit.EditError, lang.GenomeError, SyntaxError) as e:
        log["reply"] = text[-6000:]
        return Child(None, "llm_cross", f"{type(e).__name__}: {e}", log, model, cost)
    log.update(edit.diff_stats(a_src, child))
    return Child(child, "llm_cross", None, log, model, cost)


# ---------------------------------------------------------------- constant tuning (ES)

# primitives whose numeric arguments are indices or ids, not quantities
_INDEX_PRIMS = {"slot_kind", "slot_ready", "slot_range", "slot_radius", "slot_targets", "slot_moveless",
                "item_cost", "item_strength", "item_focus", "item_health", "item_passive", "items_owned",
                "read_shared", "write_shared", "picked_by_us", "picked_by_them", "group_gems", "group_gold",
                "group_respawning", "group_tiles", "tile", "range"}


def tunable_constants(source):
    """Numeric literals worth tuning: (line, col, end_col, value) in source coordinates (UTF-8 columns).
    Skips zeros, indices (slot/item/offset/group/tile args), ==/!= comparisons, and @gene headers."""
    mod = ast.parse(source)
    skip = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.FunctionDef):
            for d in node.decorator_list:
                skip.update(id(n) for n in ast.walk(d))
        elif isinstance(node, ast.Call) and getattr(node.func, "id", None) in _INDEX_PRIMS:
            for a in node.args:
                skip.update(id(n) for n in ast.walk(a) if isinstance(n, ast.Constant))
        elif isinstance(node, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops):
            skip.update(id(n) for n in ast.walk(node) if isinstance(n, ast.Constant))
    out = []
    for node in ast.walk(mod):
        if (isinstance(node, ast.Constant) and type(node.value) in (int, float) and id(node) not in skip
                and node.value != 0 and node.lineno == node.end_lineno):  # 0 means "off": not a scale
            out.append((node.lineno, node.col_offset, node.end_col_offset, node.value))
    return sorted(out)


def _fmt(v):
    if isinstance(v, int) or float(v).is_integer() and abs(v) >= 2:
        return str(int(round(v)))
    return repr(round(float(v), 4))


def tune(parent_src, rng, sigma=0.3, n_changes=None):
    """Rescale 1-3 numeric constants by a log-normal factor (integers stay integers)."""
    consts = tunable_constants(parent_src)
    if not consts:
        return Child(None, "tune", "no tunable constants")
    n = n_changes or rng.choice([1, 1, 2, 3])
    picks = rng.sample(consts, min(n, len(consts)))
    lines = parent_src.splitlines(keepends=True)
    changes = []
    for ln, c0, c1, v in sorted(picks, key=lambda p: (p[0], -p[1])):
        if float(v).is_integer() and abs(v) >= 2:
            nv = max(0, int(round(v * rng.lognormvariate(0, sigma))))
            if nv == v:
                nv = v + rng.choice([-1, 1])
        else:
            nv = round(v * rng.lognormvariate(0, sigma), 4)
        b = lines[ln - 1].encode()
        lines[ln - 1] = (b[:c0] + _fmt(nv).encode() + b[c1:]).decode()
        changes.append((ln, v, nv))
    child = "".join(lines)
    try:
        lang.parse(child)
    except lang.GenomeError as e:
        return Child(None, "tune", f"GenomeError: {e}", {"changes": changes})
    log = {"changes": changes}
    log.update(edit.diff_stats(parent_src, child))
    return Child(child, "tune", None, log)
