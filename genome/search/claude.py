"""Claude client for the operators: Haiku for volume, Opus every Nth call, prompt caching, hard budget cap.

Same prices and cadence as funsearch/llm.py. The key comes from FUNSEARCH_API_KEY (never logged).
"""
import os
import threading
import time

import anthropic

from funsearch.llm import CACHE_READ, CACHE_WRITE, PRICES

HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"


class BudgetExceeded(Exception):
    pass


class Claude:
    def __init__(self, budget_usd, opus_every=10, max_tokens=16000):
        key = os.environ.get("FUNSEARCH_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=key, max_retries=4)
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = 0
        self.opus_every = opus_every
        self.max_tokens = max_tokens
        self.lock = threading.Lock()

    def _model(self):
        with self.lock:
            if self.spent >= self.budget:
                raise BudgetExceeded(f"spent ${self.spent:.2f} of ${self.budget:.2f}")
            self.calls += 1
            n = self.calls
        return OPUS if self.opus_every and n % self.opus_every == 0 else HAIKU

    @staticmethod
    def cost(model, usage):
        pin, pout = PRICES[model]
        tokens_in = (usage.input_tokens
                     + CACHE_READ * (usage.cache_read_input_tokens or 0)
                     + CACHE_WRITE * (usage.cache_creation_input_tokens or 0))
        return (tokens_in * pin + usage.output_tokens * pout) / 1e6

    def ask(self, system, user, model=None):
        """One request. `system` is a list of strings: each becomes a cached block (stable first).
        Returns (reply text or None on refusal, model, cost USD, info dict)."""
        model = model or self._model()
        blocks = [{"type": "text", "text": s} for s in system]
        blocks[-1]["cache_control"] = {"type": "ephemeral"}
        kwargs = dict(model=model, max_tokens=self.max_tokens, system=blocks,
                      messages=[{"role": "user", "content": user}])
        t0 = time.time()
        if model == OPUS:
            # server-side refusal fallback (opt-in default for this model)
            with self.client.beta.messages.stream(**kwargs, betas=["server-side-fallback-2026-07-01"],
                                                  fallbacks="default") as s:
                response = s.get_final_message()
        else:
            with self.client.messages.stream(**kwargs) as s:
                response = s.get_final_message()
        c = self.cost(model, response.usage)
        with self.lock:
            self.spent += c
        u = response.usage
        info = {"in": u.input_tokens, "out": u.output_tokens, "cache_read": u.cache_read_input_tokens or 0,
                "cache_write": u.cache_creation_input_tokens or 0, "seconds": round(time.time() - t0, 1),
                "stop": response.stop_reason}
        if response.stop_reason == "refusal":
            return None, model, c, info
        text = "".join(b.text for b in response.content if b.type == "text")
        return text, model, c, info
