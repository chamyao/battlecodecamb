"""Token vocabulary, grammar mask, and policy <-> token conversion.

A policy is written as a flat token sequence (pre-order):

    steps   := step* END
    step    := END_TURN | <effect block> expr* | LET:T expr | KEEP:T expr
             | IF expr steps [ELSE steps]
    expr    := <pure block> expr* | VAR:T:i | CONST:T

Numeric/byte constants are CONST tokens whose values live in a side list
(the generator picks structure; constants are tuned separately).

`GrammarState` tracks a partial sequence and answers `allowed()`: the token
ids that keep it a valid, completable policy within the size limits. A
network samples from its logits masked by `allowed()`.
"""
import random
from dataclasses import dataclass

from .blocks import REGISTRY, TYPES, VOID
from .tree import Call, Const, Do, EndTurn, If, Let, Var, type_of

CONST_TYPES = ("Num", "Bytes")
INF = float("inf")


@dataclass(frozen=True)
class Limits:
    max_tokens: int = 400
    max_depth: int = 5   # expression tree height
    max_nest: int = 4    # nested ifs
    max_steps: int = 24  # steps per block
    max_vars: int = 8    # variables per type


# ---- vocabulary -------------------------------------------------------

END, IF, ELSE, END_TURN = "END", "IF", "ELSE", "END_TURN"


def _build_vocab(limits):
    vocab = [END, IF, ELSE, END_TURN]
    vocab += [b.key for b in REGISTRY]
    vocab += [f"LET:{t}" for t in TYPES] + [f"KEEP:{t}" for t in TYPES]
    vocab += [f"CONST:{t}" for t in CONST_TYPES]
    vocab += [f"VAR:{t}:{i}" for t in TYPES for i in range(limits.max_vars)]
    return vocab


def _min_costs():
    """Fewest tokens and smallest tree height that produce each type."""
    tokens = {t: INF for t in TYPES}
    depth = {t: INF for t in TYPES}
    for t in CONST_TYPES:
        tokens[t], depth[t] = 1, 1
    changed = True
    while changed:
        changed = False
        for b in REGISTRY:
            if b.effect:
                continue
            tk = 1 + sum(tokens[a] for a in b.args)
            dp = 1 + max((depth[a] for a in b.args), default=0)
            if tk < tokens[b.ret] or dp < depth[b.ret]:
                tokens[b.ret] = min(tokens[b.ret], tk)
                depth[b.ret] = min(depth[b.ret], dp)
                changed = True
    return tokens, depth


MIN_TOKENS, MIN_DEPTH = _min_costs()


class Vocab:
    def __init__(self, limits=Limits()):
        self.limits = limits
        self.tokens = _build_vocab(limits)
        self.ids = {t: i for i, t in enumerate(self.tokens)}
        self.blocks = {b.key: b for b in REGISTRY}

    def __len__(self):
        return len(self.tokens)


# ---- grammar state (the mask) -----------------------------------------

class GrammarState:
    """Incremental parser over a partial token sequence."""

    def __init__(self, vocab):
        self.v = vocab
        self.lim = vocab.limits
        self.n = 0
        self.nvars = {t: 0 for t in TYPES}
        # frames: ["steps", nest, count, scope(, "else")] | ["expr", type, depth]
        #         | ["bind", type] | ["else?"]
        self.stack = [["steps", 0, 0, []]]
        self.done = False

    # -- helpers --
    def _visible_vars(self, t):
        out = []
        for f in self.stack:
            if f[0] == "steps":
                out += [i for (vt, i) in f[3] if vt == t]
        return out

    def _need(self):
        """Fewest tokens still needed to complete the sequence."""
        need = 0
        for f in self.stack:
            if f[0] == "steps":
                need += 2 if len(f) > 4 and f[2] == 0 else 1
            elif f[0] == "expr":
                need += MIN_TOKENS[f[1]]
        return need

    def _steps_frame(self):
        for f in reversed(self.stack):
            if f[0] == "steps":
                return f

    def _expr_options(self, t, d):
        """(token, extra tokens needed beyond the token itself) for type t."""
        opts = []
        for b in REGISTRY:
            if b.effect or b.ret != t:
                continue
            if b.args and d + max(MIN_DEPTH[a] for a in b.args) > self.lim.max_depth:
                continue
            extra = sum(MIN_TOKENS[a] for a in b.args)
            if extra < INF:
                opts.append((b.key, extra))
        for i in self._visible_vars(t):
            opts.append((f"VAR:{t}:{i}", 0))
        if t in CONST_TYPES:
            opts.append((f"CONST:{t}", 0))
        return opts

    def _step_options(self, frame):
        nest, count = frame[1], frame[2]
        is_else = len(frame) > 4
        # an else-block can't be empty, so every policy has one encoding
        opts = [] if is_else and count == 0 else [(END, -1)]
        if count >= self.lim.max_steps:
            return opts
        opts.append((END_TURN, 0))
        for b in REGISTRY:
            if b.effect:
                extra = sum(MIN_TOKENS[a] for a in b.args)
                if extra < INF and all(MIN_DEPTH[a] <= self.lim.max_depth for a in b.args):
                    opts.append((b.key, extra))
        for t in TYPES:
            if MIN_DEPTH[t] <= self.lim.max_depth and self.nvars[t] < self.lim.max_vars:
                opts.append((f"LET:{t}", MIN_TOKENS[t]))
                opts.append((f"KEEP:{t}", MIN_TOKENS[t]))
        if nest < self.lim.max_nest:
            opts.append((IF, MIN_TOKENS["Bool"] + 1))
        if is_else and count == 0:
            # the first step also pays off the empty else-block's extra need
            opts = [(tok, delta - 1) for tok, delta in opts]
        return opts

    def _options(self):
        top = self.stack[-1]
        if top[0] == "expr":
            # replacing this frame's MIN_TOKENS[t] with the chosen option
            return [(tok, extra - MIN_TOKENS[top[1]]) for tok, extra in self._expr_options(top[1], top[2])]
        if top[0] == "else?":
            parent = self.stack[-2]
            return [(ELSE, 2)] + self._step_options(parent)
        return self._step_options(top)

    # -- public API --
    def allowed(self):
        if self.done:
            return []
        budget = self.lim.max_tokens - self.n - 1 - self._need()
        return [self.v.ids[tok] for tok, delta in self._options() if delta <= budget]

    def push(self, tok_id):
        tok = self.v.tokens[tok_id]
        if tok_id not in self.allowed():
            raise ValueError(f"token {tok} not allowed here")
        self.n += 1
        top = self.stack[-1]
        if top[0] == "else?":
            self.stack.pop()
            if tok == ELSE:
                parent = self.stack[-1]
                self.stack.append(["steps", parent[1] + 1, 0, [], "else"])
                return
            top = self.stack[-1]
        if top[0] == "expr":
            self.stack.pop()
            if tok in self.v.blocks:
                for a in reversed(self.v.blocks[tok].args):
                    self.stack.append(["expr", a, top[2] + 1])
            self._settle()
            return
        # steps frame
        if tok == END:
            self.stack.pop()
            if not self.stack:
                self.done = True
                return
            if self.stack[-1][0] == "if":
                self.stack.pop()
                self.stack.append(["else?"])
            return
        top[2] += 1
        if tok == IF:
            self.stack.append(["if"])
            self.stack.append(["steps", top[1] + 1, 0, []])
            self.stack.append(["expr", "Bool", 1])
        elif tok.startswith(("LET:", "KEEP:")):
            t = tok.split(":", 1)[1]
            self.stack.append(["bind", t])
            self.stack.append(["expr", t, 1])
        elif tok in self.v.blocks:
            for a in reversed(self.v.blocks[tok].args):
                self.stack.append(["expr", a, 1])
        self._settle()

    def _settle(self):
        while self.stack[-1][0] == "bind":
            t = self.stack.pop()[1]
            self._steps_frame()[3].append((t, self.nvars[t]))
            self.nvars[t] += 1


# "if" frames sit between a steps frame and the then-block; they count as
# nothing for _need/_visible_vars and are popped when the then-block ends.


# ---- encode / decode --------------------------------------------------

def encode(steps, vocab):
    """Policy steps -> (token ids, constants)."""
    toks, consts = [], []
    names = {}  # variable name -> token
    counts = {t: 0 for t in TYPES}

    def expr(e):
        if isinstance(e, Const):
            toks.append(f"CONST:{e.type}")
            consts.append(e.value)
        elif isinstance(e, Var):
            toks.append(names[e.name])
        else:
            toks.append(e.block.key)
            for a in e.args:
                expr(a)

    def block(steps):
        for s in steps:
            if isinstance(s, EndTurn):
                toks.append(END_TURN)
            elif isinstance(s, Do):
                expr(s.call)
            elif isinstance(s, Let):
                t = type_of(s.expr)
                toks.append(f"{'KEEP' if s.keep else 'LET'}:{t}")
                expr(s.expr)
                names[s.name] = f"VAR:{t}:{counts[t]}"
                counts[t] += 1
            elif isinstance(s, If):
                toks.append(IF)
                expr(s.cond)
                block(s.then)
                if s.orelse:
                    toks.append(ELSE)
                    block(s.orelse)
        toks.append(END)

    block(steps)
    return [vocab.ids[t] for t in toks], consts


def decode(ids, consts, vocab):
    """(token ids, constants) -> policy steps."""
    toks = [vocab.tokens[i] for i in ids]
    pos = 0
    ci = 0
    counts = {t: 0 for t in TYPES}

    def take():
        nonlocal pos
        tok = toks[pos]
        pos += 1
        return tok

    def expr():
        nonlocal ci
        tok = take()
        if tok.startswith("CONST:"):
            ci += 1
            return Const(tok.split(":")[1], consts[ci - 1])
        if tok.startswith("VAR:"):
            _, t, i = tok.split(":")
            return Var(f"{t.lower()}{i}", t)
        blk = vocab.blocks[tok]
        return Call(blk, [expr() for _ in blk.args])

    def block():
        steps = []
        while True:
            tok = take()
            if tok == END:
                return steps
            if tok == END_TURN:
                steps.append(EndTurn())
            elif tok == IF:
                node = If(expr(), block())
                if pos < len(toks) and toks[pos] == ELSE:
                    take()
                    node.orelse = block()
                steps.append(node)
            elif tok.startswith(("LET:", "KEEP:")):
                kind, t = tok.split(":")
                e = expr()
                steps.append(Let(f"{t.lower()}{counts[t]}", e, kind == "KEEP"))
                counts[t] += 1
            else:
                pos_blk = vocab.blocks[tok]
                steps.append(Do(Call(pos_blk, [expr() for _ in pos_blk.args])))

    return block()


# ---- sampling ---------------------------------------------------------

def sample(vocab, rng=None, end_bias=4.0):
    """A uniformly-ish random valid policy (stand-in for the network)."""
    rng = rng or random.Random()
    state = GrammarState(vocab)
    ids, consts = [], []
    end_id = vocab.ids[END]
    while not state.done:
        allowed = state.allowed()
        weights = [end_bias if a == end_id else 1.0 for a in allowed]
        tok_id = rng.choices(allowed, weights)[0]
        tok = vocab.tokens[tok_id]
        if tok == "CONST:Num":
            consts.append(rng.choice([0, 1, 2, 3, 5, 10, 30, 100, 0.35, 0.5]))
        elif tok == "CONST:Bytes":
            consts.append(b"")
        state.push(tok_id)
        ids.append(tok_id)
    return ids, consts
