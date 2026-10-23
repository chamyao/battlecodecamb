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
