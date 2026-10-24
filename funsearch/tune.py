"""Constant tuning: (1+1) evolution strategy over a policy's numeric constants.

Structure stays fixed; each CONST:Num is scaled by a random factor, the child is
scored on the same games as the parent (common random numbers), and kept if it
is at least as good. Also serves as an LLM-free proposer for testing the loop.
"""
import random

from policygen.text import format_policy, parse
from policygen.tree import Call, Const, Do, If, Let


# Numeric arguments that are indices, not tunable quantities: (block name, argument position).
_INDEX_ARGS = {("ability_ready", 0), ("cast_at_unit", 0), ("cast_at_tile", 0), ("cast_self", 0),
               ("dash_towards", 0), ("read_shared", 0), ("write_shared", 0)} | {
               (f"slot_is_{k}", 0) for k in ("dash", "damage", "aoe", "stun", "heal", "shield", "reset")}


def _consts(steps):
    """Every tunable numeric Const node in a policy, in order (slot/offset indices excluded)."""
    out = []

    def expr(e):
        if isinstance(e, Const):
            if e.type == "Num":
                out.append(e)
        elif isinstance(e, Call):
            for i, a in enumerate(e.args):
                if (e.block.name, i) in _INDEX_ARGS and isinstance(a, Const):
                    continue
                expr(a)

    def block(steps):
        for s in steps:
            if isinstance(s, Do):
                expr(s.call)
            elif isinstance(s, Let):
                expr(s.expr)
            elif isinstance(s, If):
                expr(s.cond)
                block(s.then)
                block(s.orelse)

    block(steps)
    return out


def mutate_constants(text, rng, sigma=0.3, n_changes=1):
    """Rescale up to n_changes numeric constants; names and structure are kept."""
    steps = parse(text)
    nums = _consts(steps)
    if not nums:
        return text
    for node in rng.sample(nums, min(n_changes, len(nums))):
        c = node.value
        if c == 0:
            node.value = rng.choice([1, -1]) * round(rng.random(), 4)
        elif float(c).is_integer() and abs(c) >= 2:
            node.value = max(0, round(c * rng.lognormvariate(0, sigma)))
        else:
            node.value = round(c * rng.lognormvariate(0, sigma), 4)
    return format_policy(steps)


def tune(text, evaluate, steps=20, seed=0, log=print):
    """Hill-climb constants. `evaluate(text, seed)` returns a score."""
    rng = random.Random(seed)
    best, best_score = text, evaluate(text, seed)
    for step in range(steps):
        child = mutate_constants(best, rng)
        if child == best:
            continue
        s = evaluate(child, seed)
        if s >= best_score:
            best, best_score = child, s
        log(f"tune step {step}: child {s:.3f}, best {best_score:.3f}")
    return best, best_score


# ---- child constant hill-climb (run.py --tune-children): text-level, so comments and headers survive ----
import re as _re

_NUM = _re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
_NAMED = _re.compile(r"^([A-Z][A-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*(#.*)?$")
_INDEX_CALL = _re.compile(r"\b(" + "|".join(sorted({b for b, _ in _INDEX_ARGS})) + r")\(\s*$")
# bit/byte arithmetic on shared memory (e.g. lk_v - 2 * floor(lk_v / 2)): never tuned
_BITWISE = _re.compile(r"read_shared|write_shared|floor\(\s*\(*\s*\w+\s*/\s*\d")


def _code_part(line):
    i = line.find("#")
    return line if i < 0 else line[:i]


def literals(text):
    """Numeric literals in code (comments excluded), as dicts: start/end offsets in text, value string, line
    number, the line with its numbers masked, and the constant's name for NAME = number lines. Slot/offset index
    arguments (ability_ready(0), write_shared(7, ...) ...) and lines doing shared-memory bit arithmetic
    (read_shared / write_shared / floor(x / N)) are left out."""
    out, pos = [], 0
    for ln, line in enumerate(text.split("\n")):
        code = _code_part(line)
        if _BITWISE.search(code):
            pos += len(line) + 1
            continue
        named = _NAMED.match(line.strip())
        masked = _NUM.sub("N", code).strip()
        for m in _NUM.finditer(code):
            if _INDEX_CALL.search(code[: m.start()]):
                continue
            out.append(dict(start=pos + m.start(), end=pos + m.end(), value=m.group(0), line=ln, masked=masked,
                            name=named.group(1) if named else None))
        pos += len(line) + 1
    return out


def changed_constants(parent, child):
    """Literals of `child` that are new or changed relative to `parent`: named constants (NAME = number) that are
    new or differ in value; else numbers on code lines whose masked form or values are not in the parent. Empty when
    the child's constants are the parent's."""
    p, c = literals(parent), literals(child)
    p_named = {x["name"]: x["value"] for x in p if x["name"]}
    named = [x for x in c if x["name"] and p_named.get(x["name"]) != x["value"]]
    if named:
        return named
    p_lines = {}
    for x in p:
        p_lines.setdefault(x["masked"], set()).add(x["value"])
    return [x for x in c if not x["name"] and x["value"] not in p_lines.get(x["masked"], set())]


def mutate_literal(text, lit, rng, sigma=0.3):
    """Rescale one literal in place (integers >= 2 stay integers, 0 becomes a small number)."""
    v = float(lit["value"])
    is_int = "." not in lit["value"]
    if v == 0:
        new = rng.choice([1, -1]) * (1 if is_int else round(rng.random(), 4))
    elif is_int and abs(v) >= 2:
        new = max(0, round(v * rng.lognormvariate(0, sigma)))
        if new == v:
            new = int(v) + rng.choice([1, -1])
    elif is_int:
        new = int(v) + rng.choice([1, -1])
    else:
        new = round(v * rng.lognormvariate(0, sigma), 4)
    s = str(int(new)) if is_int else repr(float(new))
    return text[: lit["start"]] + s + text[lit["end"]:], s


def climb_child(parent, child, evaluate, steps=8, rng=None, margin=0.02, seed0=0):
    """(1+1)-ES on the constants the child added or changed. evaluate(text, seed) -> score or None. Each step scores
    the incumbent and the mutant on the same fresh seed and accepts only a clear gain (> margin). Returns
    (text, info) where info = {steps, before, after, changed: {name or line:col: "old->new"}} or None if no targets."""
    rng = rng or random.Random(0)
    if not changed_constants(parent, child):
        return child, None
    best = child
    before = after = None
    changed = {}
    for k in range(steps):
        targets = changed_constants(parent, best)
        if not targets:
            break
        lit = rng.choice(targets)
        cand, new = mutate_literal(best, lit, rng)
        s_best, s_cand = evaluate(best, seed0 + k), evaluate(cand, seed0 + k)
        if s_best is None or s_cand is None:
            continue
        before = s_best if before is None else before
        if s_cand > s_best + margin:
            key = lit["name"] or f"{lit['line']}:{lit['masked'][:40]}"
            old = changed.get(key, lit["value"]).split("->")[0]
            changed[key] = f"{old}->{new}"
            best = cand
            after = s_cand
    return best, dict(steps=steps, before=before, after=after if after is not None else before, changed=changed)
