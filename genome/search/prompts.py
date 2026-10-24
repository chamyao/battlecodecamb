"""What Claude is told for genome operators: game facts, the gene language, and the genome at hand."""
from pathlib import Path

from funsearch.catalog import GAME

from .edit import ENTRIES

LANGUAGE = (Path(__file__).resolve().parent.parent / "LANGUAGE.md").read_text()

FACTS = GAME.replace("Every block a bot runs costs fuel", "Every operation and engine call a bot runs costs fuel") + """\
In a genome, compiled gene code is cheap (a few fuel per operation); engine calls (distance fields
via field(), vision queries such as enemies()/camps()) cost more. A turn over budget is suspended.
"""

SYSTEM_BASE = f"""You evolve bot policies for a programming competition. A policy is a genome: a set of genes
(small typed functions) in the gene language below. The fixed loop lists every legal option each turn,
calls score(o) on each, and does the best one while its score is > 0.

# The game
{FACTS}
# The gene language
{LANGUAGE}
Also: `consider(kind: Num) -> Bool` (optional entry gene) is asked once per option kind each pass;
kinds it rejects are neither listed nor scored, which saves the fuel of listing and scoring them.
Expensive sets and distance fields can be computed once per turn into a Tiles/Field keep in update()
instead of in a zero-argument gene (recomputed every pass of the loop). A mutation may add consider()
or update() if the genome has none."""

MUTATE_TASK = """# Your task: mutate one link of the genome
You are shown the genome's genes. Exactly the genes marked EDITABLE (the two ends of one dependency
link, sometimes two links) may be changed, in any way you like: rewrite their bodies, change their
parameters (every other caller must still type-check), call any existing gene, or create new genes
(fresh helpers, a gene inserted between the two, a modified duplicate of an existing gene, a small
new subtree). All other genes are fixed: you may call them, never change them.

Aim for a change that should make the bot win more: a better rule, a missing behaviour, a better
threshold, a cheaper way to compute the same thing. Keep what already works.

Reply with one ```python code block holding:
- the new version of every EDITABLE gene you change (keep its @gene id; you may update its
  description; omit an editable gene to leave it as it is);
- each new gene with @gene("new", "<one-line description>", parents=["<id of the gene it came from>"]);
- any new keep declarations (NAME: Type = value) your genes use.
Do not repeat the fixed genes. A gene nobody calls is deleted. Then write nothing else."""

CROSS_TASK = """# Your task: cross over two genomes by meaning
You are shown two unrelated parent genomes (different lineages), with their scores. Write one child
genome that combines the best ideas of both: e.g. graft one parent's handling of a situation (casting,
fights, banking, shopping, draft...) onto the other's, merging score() so both sets of behaviours are
reachable. Keep each inherited gene's @gene id (and its parent's version where you keep it unchanged);
give genes you write or substantially merge @gene("new", "<description>", parents=[<ids it came from>]).

Reply with the complete child genome (keep declarations and every gene) in one ```python code block,
then nothing else."""


def signature(g):
    params = ", ".join(f"{p}: {t}" for p, t in g.params)
    return f"{g.name}({params}) -> {g.ret}"


def mutate_user(genome, source_genes, editable, edges, stats=None):
    """editable: gene names; edges: [(a, b, kind)]; source_genes: {id: source text}."""
    callers = {}
    for g in genome.genes.values():
        for c in g.calls:
            callers.setdefault(c, []).append(g.name)
    out = []
    if stats:
        out.append(f"Current results: {stats}\n")
    link = "; ".join(f"{a} -> {b} ({kind})" for a, b, kind in edges)
    out.append(f"## Link(s) to mutate: {link}\n")
    if genome.keeps:
        out.append("## Keep declarations\n```python\n" + "\n".join(
            f"{n}: {t}" for n, (t, _) in genome.keeps.items()) + "\n```\n")
    out.append("## Fixed genes (signature, id, description, calls)")
    for g in genome.genes.values():
        if g.name in editable:
            continue
        calls = f"; calls {', '.join(sorted(g.calls))}" if g.calls else ""
        out.append(f"- {signature(g)}  [{g.id}] {g.desc}{calls}")
    out.append("")
    for name in editable:
        g = genome.genes[name]
        who = ", ".join(sorted(callers.get(name, []))) or ("the fixed loop" if name in ENTRIES else "nobody")
        out.append(f"## EDITABLE gene {g.name} (called by {who})\n```python\n{source_genes[g.id].strip()}\n```\n")
    out.append("Write the mutation.")
    return "\n".join(out)


def cross_user(a_src, a_score, b_src, b_score):
    return (f"## Parent A (score {a_score:.3f})\n```python\n{a_src.strip()}\n```\n\n"
            f"## Parent B (score {b_score:.3f})\n```python\n{b_src.strip()}\n```\n\nWrite the child.")
