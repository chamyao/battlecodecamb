"""Constant tuning: (1+1) evolution strategy over a policy's numeric constants.

Structure stays fixed; each CONST:Num is scaled by a random factor, the child is
scored on the same games as the parent (common random numbers), and kept if it
is at least as good. Also serves as an LLM-free proposer for testing the loop.
"""
import random
import re

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


_NAMED = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*$", re.M)


def named_constants(text):
    """Top-level named constants (`NAME = number` lines) as {name: value}."""
    return {m.group(1): float(m.group(2)) for m in _NAMED.finditer(text)}


def set_named(text, values):
    """text with the given named constants rewritten in place (comments and macros untouched)."""
    def sub(m):
        if m.group(1) not in values:
            return m.group(0)
        v = values[m.group(1)]
        return f"{m.group(1)} = {int(v) if float(v).is_integer() else round(v, 4)}"
    return _NAMED.sub(sub, text)


def mutate_named(text, rng, sigma=0.3):
    """Rescale one named constant by a log-normal factor; integers stay integers."""
    consts = named_constants(text)
    if not consts:
        return text
    name = rng.choice(sorted(consts))
    c = consts[name]
    if c == 0:
        v = rng.choice([1, -1]) * round(rng.random(), 4)
    elif c.is_integer() and abs(c) >= 2:
        v = max(0, round(c * rng.lognormvariate(0, sigma)))
    else:
        v = round(c * rng.lognormvariate(0, sigma), 4)
    return set_named(text, {name: v})


def tune_named(text, score, steps=24, seed=0, log=print):
    """(1+1) hill climb over the named constants with common random numbers: `score(text)` must play
    the same games for every call. Returns (best text, its score, the start score)."""
    rng = random.Random(seed)
    best = text
    start = best_score = score(text)
    for step in range(steps):
        child = mutate_named(best, rng)
        if child == best:
            continue
        s = score(child)
        if s > best_score:
            best, best_score = child, s
        log(f"tune step {step}: child {s:.3f}, best {best_score:.3f}")
    return best, best_score, start
