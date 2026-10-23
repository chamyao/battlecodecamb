"""Claude proposer: asks for an improved policy; tracks spend against a hard budget."""
import os
import re
import threading

import anthropic

from .catalog import GAME, GRAMMAR, block_catalog

# $ per million tokens (input, output). Cache reads/writes priced relative to input.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5-5": (4.00, 20.00),
}
CACHE_READ, CACHE_WRITE = 0.1, 1.25

SYSTEM = f"""You improve bot policies for a programming competition, written in a small typed language.

# The game
{GAME}
# The policy language
{GRAMMAR}
# Blocks (signature -> return type)
{block_catalog()}

# Your task
You are shown earlier policy versions, worst first, with their scores (win rate against the
reference bots, plus a small bonus for gem margin; higher is better), its win rate and gems against
each reference bot (weak matchups show where to improve) and, if any, how many turns per game its
champions ran out of fuel (each one is a lost turn). Write one new version that
should score higher. Make a focused, meaningful change: a better rule, a missing behaviour, a
better threshold, or a cheaper way to do the same thing. Keep everything that already works.
Reply with the complete new policy in a single ```policy code block, then nothing else."""


class BudgetExceeded(Exception):
    pass


class Proposer:
    def __init__(self, budget_usd, opus_every=10, max_tokens=16000):
        # The cloud environment reserves ANTHROPIC_API_KEY for Claude Code's own login and does not
        # pass it to processes, so the key is stored as FUNSEARCH_ANTHROPIC_KEY (or FUNSEARCH_API_KEY) there. It may also
        # point ANTHROPIC_BASE_URL at Claude Code's endpoint, so the API URL is pinned.
        self.client = anthropic.Anthropic(
            api_key=(os.environ.get("FUNSEARCH_ANTHROPIC_KEY") or os.environ.get("FUNSEARCH_API_KEY")
                     or os.environ.get("ANTHROPIC_API_KEY")),
            base_url=os.environ.get("FUNSEARCH_BASE_URL", "https://api.anthropic.com"))
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = 0
        self.opus_every = opus_every
        self.max_tokens = max_tokens
        self.lock = threading.Lock()

    def _model(self):
        with self.lock:
            self.calls += 1
            n = self.calls
        return "claude-opus-5-5" if self.opus_every and n % self.opus_every == 0 else "claude-haiku-5-5"

    def _cost(self, model, usage):
        pin, pout = PRICES[model]
        tokens_in = (usage.input_tokens
                     + CACHE_READ * (usage.cache_read_input_tokens or 0)
                     + CACHE_WRITE * (usage.cache_creation_input_tokens or 0))
        return (tokens_in * pin + usage.output_tokens * pout) / 1e6

    def propose(self, parents):
        """parents: list of (text, score, metrics), worst first; metrics holds per-opponent stats. Returns (policy text or None, model, cost, proposals)."""
        with self.lock:
            if self.spent >= self.budget:
                raise BudgetExceeded(f"spent ${self.spent:.2f} of ${self.budget:.2f}")
        model = self._model()
        def header(i, score, metrics):
            per = {k: m for k, m in (metrics or {}).items() if isinstance(m, dict) and "win_rate" in m}
            lines = [f"## Version {i} (score {score:.3f})"]
            if per:
                lines.append("Win rate (your gems - their gems per game): " + ", ".join(
                    f"vs {k} {m['win_rate']:.0%} ({m['a_gems']:.0f}-{m['b_gems']:.0f})" for k, m in per.items()))
                susp = sum(m.get("a_suspensions", 0) for m in per.values()) / len(per)
                if susp >= 1:
                    lines.append(f"Out of fuel {susp:.0f} turns per game.")
            return "\n".join(lines)
        shown = "\n\n".join(
            f"{header(i, score, metrics)}\n```policy\n{text.strip()}\n```"
            for i, (text, score, metrics) in enumerate(parents))
        user = f"{shown}\n\n## Version {len(parents)}\nWrite it."
        kwargs = dict(
            model=model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        if model == "claude-opus-5-5":
            # server-side refusal fallback (opt-in default for this model)
            response = self.client.beta.messages.create(
                **kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            response = self.client.messages.create(**kwargs)
        cost = self._cost(model, response.usage)
        with self.lock:
            self.spent += cost
        if response.stop_reason == "refusal":
            return None, model, cost, []
        text = "".join(b.text for b in response.content if b.type == "text")
        m = re.search(r"```policy\n(.*?)```", text, re.S)
        # block proposals may sit inside or outside the code block
        proposals = [x.strip() for x in re.findall(r"#\s*PROPOSE:\s*(.+)", text)]
        return (m.group(1) if m else None), model, cost, list(dict.fromkeys(proposals))
