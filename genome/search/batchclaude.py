"""Batched edit mutations (arenaZ-15): mutate() calls are held and sent as ONE call per batch.

A batch goes out when `size` mutation requests are pending, or `wait` seconds after the oldest pending one arrived. The
call carries the shared system blocks (SYSTEM_BASE + MUTATE_TASK) once and every request's user prompt (as mutate_user
renders it) as a numbered section; the reply has one "## Request <n>" section per request, each holding that request's
```python block. Each caller gets its own section back as its reply and parses it exactly as a single reply, so a missing
or malformed section fails only that child. Every other call (crossover by meaning, splits, ...) goes straight through.

Per child the info dict adds batch id, batch size and position (cost = batch cost / size); per batch, a row in
`log_path`: size, latency, tokens, cost, sections found.
"""
import json
import re
import threading
import time

from . import prompts
from .claude import Claude

BATCH_HEAD = """The genomes below are {k} INDEPENDENT mutation requests, each for a different genome. Handle each one on its own,
exactly as if it were the only request: its own editable genes, link and fixed genes; nothing carries over between requests.

Answer every request, in order. For request n write a line "## Request n" and then exactly one ```python block with that
request's edited genes, in the format the task asks for. Nothing else is needed between sections."""

SECTION = re.compile(r"^#{1,3}\s*Request\s+(\d+)\b.*$", re.M)


def split_reply(text, k):
    """{n: section text} for n in 1..k (missing sections are absent)."""
    marks = list(SECTION.finditer(text or ""))
    out = {}
    for i, m in enumerate(marks):
        n = int(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        if 1 <= n <= k and n not in out:
            out[n] = text[m.end():end]
    return out


class _Item:
    def __init__(self, user):
        self.user, self.t = user, time.time()
        self.done = threading.Event()
        self.result = self.error = None


class BatchClaude(Claude):
    def __init__(self, budget_usd, opus_every=10, size=8, wait=20.0, log_path=None, max_tokens=64000):
        super().__init__(budget_usd, opus_every=opus_every, max_tokens=max_tokens)  # a cap only: room for k replies
        self.size, self.wait, self.log_path = size, wait, log_path
        self.pending, self.batches = [], 0
        self.cv = threading.Condition()
        threading.Thread(target=self._loop, daemon=True).start()

    def ask(self, system, user, model=None):
        if list(system) != [prompts.SYSTEM_BASE, prompts.MUTATE_TASK] or model is not None:
            return super().ask(system, user, model)
        it = _Item(user)
        with self.cv:
            self.pending.append(it)
            self.cv.notify_all()
        it.done.wait()
        if it.error is not None:
            raise it.error
        return it.result

    def _loop(self):
        while True:
            with self.cv:
                while not (len(self.pending) >= self.size
                           or (self.pending and time.time() - self.pending[0].t >= self.wait)):
                    self.cv.wait(timeout=1.0)
                batch, self.pending = self.pending[:self.size], self.pending[self.size:]
                self.batches += 1
                bid = self.batches
            threading.Thread(target=self._send, args=(bid, batch), daemon=True).start()

    def _send(self, bid, batch):
        k = len(batch)
        user = BATCH_HEAD.format(k=k) + "".join(f"\n\n======== Request {n} ========\n\n{it.user}"
                                                 for n, it in enumerate(batch, 1))
        row = {"batch": bid, "size": k, "t": round(time.time(), 1),
               "waited": [round(time.time() - it.t, 1) for it in batch]}
        try:
            text, model, cost, info = super().ask([prompts.SYSTEM_BASE, prompts.MUTATE_TASK], user)
        except Exception as e:  # BudgetExceeded or an API error: every child in the batch gets it
            row["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            self._log(row)
            for it in batch:
                it.error = e
                it.done.set()
            return
        parts = split_reply(text, k) if text is not None else {}
        row.update({"model": model, "cost": round(cost, 5), "sections": len(parts), **info})
        self._log(row)
        for n, it in enumerate(batch, 1):
            child_info = {**info, "batch": bid, "batch_size": k, "batch_pos": n, "batch_cost": round(cost, 5)}
            reply = None if text is None else parts.get(n, "")
            it.result = (reply, model, cost / k, child_info)
            it.done.set()

    def _log(self, row):
        if self.log_path:
            with self.cv:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(row) + "\n")
