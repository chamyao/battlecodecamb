"""Genome source surgery shared by the operators: gene segments, re-assembly, fresh IDs, pruning, diff stats.

A genome is handled as text so unchanged genes keep their exact source (comments included); `lang.parse`
is the validity check for every result.
"""
import ast
import difflib
import re

from .. import lang


ENTRIES = ("score", "update", "consider")  # genes the fixed loop calls


class EditError(Exception):
    """An operator result that breaks a rule (not a type error: those are lang.GenomeError)."""


def segments(source):
    """Split genome source into (header, keeps, genes): header = module docstring text (or ""),
    keeps = {name: source line(s)}, genes = {id: source text of the decorated function}. Order kept."""
    mod = ast.parse(source)
    lines = source.splitlines()
    header, keeps, genes = "", {}, {}
    for st in mod.body:
        start = (st.decorator_list[0].lineno if isinstance(st, ast.FunctionDef) and st.decorator_list
                 else st.lineno) - 1
        text = "\n".join(lines[start:st.end_lineno])
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
            header = text if not header else header
        elif isinstance(st, ast.AnnAssign):
            keeps[st.target.id] = text
        elif isinstance(st, ast.FunctionDef):
            genes[gene_id(st)] = text
    return header, keeps, genes


def reply_parts(text):
    """Keeps and genes in a model reply, as lists (IDs may repeat, e.g. several "new").
    Returns (keeps [(name, text)], genes [(id, name, text)]). Raises EditError on non-genome content."""
    try:
        mod = ast.parse(text)
    except SyntaxError as e:
        raise EditError(f"syntax error line {e.lineno}: {e.msg}")
    lines = text.splitlines()
    keeps, genes = [], []
    for st in mod.body:
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
            continue
        if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
            keeps.append((st.target.id, "\n".join(lines[st.lineno - 1:st.end_lineno])))
        elif isinstance(st, ast.FunctionDef):
            d = st.decorator_list[0] if len(st.decorator_list) == 1 else None
            if not (isinstance(d, ast.Call) and getattr(d.func, "id", None) == "gene" and d.args
                    and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str)):
                raise EditError(f"line {st.lineno}: {st.name} needs @gene(id, description, parents=[...])")
            genes.append((d.args[0].value, st.name, "\n".join(lines[d.lineno - 1:st.end_lineno])))
        else:
            raise EditError(f"line {st.lineno}: only keep declarations and @gene functions")
    return keeps, genes


def gene_id(fn):
    d = fn.decorator_list[0]
    return d.args[0].value


def assemble(header, keeps, genes):
    parts = [header] if header else []
    if keeps:
        parts.append("\n".join(keeps.values()))
    parts += list(genes.values())
    return "\n\n".join(p.strip("\n") for p in parts) + "\n"


def canon(gene_text):
    """Canonical form of one gene (whitespace and comments ignored) for 'unchanged' checks."""
    return ast.dump(ast.parse(gene_text.strip()).body[0])


def body_canon(gene_text):
    """Canonical form without the decorator (description/parents edits do not count as body changes)."""
    fn = ast.parse(gene_text.strip()).body[0]
    fn.decorator_list = []
    return ast.dump(fn)


def set_header(gene_text, gid=None, desc=None, parents=None):
    """Rewrite the @gene(...) decorator of one gene's source, keeping the rest verbatim."""
    fn = ast.parse(gene_text.strip()).body[0]
    d = fn.decorator_list[0]
    old_parents = []
    for kw in d.keywords:
        if kw.arg == "parents":
            old_parents = [e.value for e in kw.value.elts]
    gid = gid if gid is not None else d.args[0].value
    desc = desc if desc is not None else d.args[1].value
    parents = old_parents if parents is None else parents
    new = f"@gene({gid!r}, {desc!r}" + (f", parents={parents!r})" if parents else ")")
    text = gene_text.strip()
    lines = text.splitlines()
    # the decorator is the first statement; replace its full span
    first, last = d.lineno - 1, d.end_lineno - 1
    lines[first:last + 1] = [new]
    return "\n".join(lines)


def reachable(genome):
    """Gene names reachable by calls from the entry genes."""
    seen, todo = set(), [n for n in ENTRIES if n in genome.genes]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        todo.extend(genome.genes[n].calls)
    return seen


def prune(source):
    """Drop genes nobody calls (repeatedly) and keeps nobody uses. Returns (source, removed gene ids)."""
    removed = []
    while True:
        g = lang.parse(source)
        live = reachable(g)
        dead = [x for x in g.genes.values() if x.name not in live]
        header, keeps, genes = segments(source)
        used = set().union(*[x.keep_reads | x.keep_writes for x in g.genes.values() if x.name in live]) if live else set()
        dead_keeps = [k for k in keeps if k not in used]
        if not dead and not dead_keeps:
            return source, removed
        for x in dead:
            removed.append(x.id)
            del genes[x.id]
        for k in dead_keeps:
            del keeps[k]
        source = assemble(header, keeps, genes)


def line_diff(a, b):
    """Changed lines between two texts (added + removed, ignoring blank lines)."""
    al = [l for l in a.splitlines() if l.strip()]
    bl = [l for l in b.splitlines() if l.strip()]
    n = 0
    for op in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes():
        if op[0] != "equal":
            n += max(op[2] - op[1], op[4] - op[3])
    return n


def gene_count_lines(text):
    return sum(1 for l in text.splitlines() if l.strip() and not l.strip().startswith("#"))


def diff_stats(parent_src, child_src):
    """What changed between a parent and a child genome, by gene ID."""
    _, pk, pg = segments(parent_src)
    _, ck, cg = segments(child_src)
    changed = [i for i in pg if i in cg and body_canon(pg[i]) != body_canon(cg[i])]
    added = [i for i in cg if i not in pg]
    removed = [i for i in pg if i not in cg]
    lines = sum(line_diff(pg[i], cg[i]) for i in changed) + sum(gene_count_lines(cg[i]) for i in added)
    return {"genes_changed": changed, "genes_added": added, "genes_removed": removed,
            "added_sizes": [gene_count_lines(cg[i]) for i in added], "lines_changed": lines,
            "keeps_added": [k for k in ck if k not in pk]}


class IdMaker:
    """Fresh gene IDs for one child: prefix + a, b, ..., skipping any in `taken`."""

    def __init__(self, prefix, taken):
        self.prefix, self.taken, self.k = prefix, set(taken), 0

    def __call__(self):
        while True:
            nid = f"{self.prefix}{_letters(self.k)}"
            self.k += 1
            if nid not in self.taken:
                self.taken.add(nid)
                return nid


def _letters(k):
    s = ""
    k += 1
    while k:
        k, r = divmod(k - 1, 26)
        s = chr(97 + r) + s
    return s


def extract_genome_block(reply):
    """The last ```python / ```genome code block in a model reply, or None."""
    blocks = re.findall(r"```(?:python|genome|py)?\s*\n(.*?)```", reply, re.S)
    return blocks[-1] if blocks else None


def body_canon_genome(source):
    """Canonical form of a whole genome: gene bodies by ID plus keep declarations."""
    _, keeps, genes = segments(source)
    return (tuple(sorted((i, body_canon(t)) for i, t in genes.items())),
            tuple(sorted((k, canon(t)) for k, t in keeps.items())))
