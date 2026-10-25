"""File-queue LLM backend (arenaa/SESSION_MUTATOR.md, variant M2): every Claude call the arena makes becomes a request file
that a long-lived Claude Code session answers.

    request  DIR/req-<seq>.json = {seq, op, child_seq, system, user, parents, created, feedback}
    reply    DIR/rep-<seq>.txt  (the reply text, parsed exactly as an API reply)

ask() blocks until the reply exists (QueueTimeout after --queue-timeout seconds). Model "session", cost 0. The arena
supplies feedback_fn() (outcomes of earlier queued children, top genomes) and context() (op, parents, child seq of the
proposal running in this thread).
"""
import json
import os
import threading
import time
from pathlib import Path

MODEL = "session"


class QueueTimeout(Exception):
    pass


class QueueClaude:
    def __init__(self, qdir, timeout=900, feedback_fn=None, poll=1.0):
        self.dir = Path(qdir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.timeout, self.poll, self.feedback_fn = timeout, poll, feedback_fn
        self.budget, self.spent, self.calls = float("inf"), 0.0, 0
        self.lock = threading.Lock()
        self.local = threading.local()
        done = [int(p.stem.split("-")[1]) for p in self.dir.glob("req-*.json")]
        self.seq = max(done, default=0)

    def context(self, op=None, parents=None, child_seq=None):
        self.local.ctx = {"op": op, "parents": parents or [], "child_seq": child_seq}

    def ask(self, system, user, model=None):
        ctx = getattr(self.local, "ctx", {}) or {}
        with self.lock:
            self.seq += 1
            self.calls += 1
            seq = self.seq
            feedback = self.feedback_fn() if self.feedback_fn else None
        req = {"seq": seq, "op": ctx.get("op"), "child_seq": ctx.get("child_seq"), "parents": ctx.get("parents", []),
               "created": round(time.time(), 1), "system": "\n\n".join(system) if isinstance(system, list) else system,
               "user": user, "feedback": feedback}
        tmp = self.dir / f".req-{seq}.json.tmp"
        tmp.write_text(json.dumps(req))
        os.replace(tmp, self.dir / f"req-{seq}.json")  # atomic: a reader never sees half a request
        rep = self.dir / f"rep-{seq}.txt"
        t0 = time.time()
        while not rep.exists():
            if time.time() - t0 > self.timeout:
                raise QueueTimeout(f"queue timeout (request {seq}, {self.timeout:.0f} s)")
            time.sleep(self.poll)
        time.sleep(0.2)  # let a non-atomic writer finish
        text = rep.read_text()
        info = {"queue_seq": seq, "seconds": round(time.time() - t0, 1), "in": 0, "out": 0, "cache_read": 0,
                "cache_write": 0, "stop": "queue"}
        return text, MODEL, 0.0, info
