"""Program database with islands (FunSearch): programs evolve in separate
populations; the weakest islands are periodically re-seeded from the best."""
import json
import math
import random
import threading
from dataclasses import asdict, dataclass, field


@dataclass
class Program:
    id: int
    island: int
    text: str
    score: float
    parents: list = field(default_factory=list)
    model: str = ""
    error: str | None = None
    metrics: dict = field(default_factory=dict)


class Database:
    def __init__(self, path, islands=4, temperature=0.05, reset_every=200, rng=None):
        self.path = path
        self.n_islands = islands
        self.temperature = temperature
        self.reset_every = reset_every
        self.rng = rng or random.Random(0)
        self.islands = [[] for _ in range(islands)]
        self.all = []
        self.lock = threading.Lock()
        self.since_reset = 0

    # ---- persistence ----
    def load(self):
        try:
            with open(self.path) as f:
                for line in f:
                    p = Program(**json.loads(line))
                    self._insert(p, log=False)
        except FileNotFoundError:
            pass

    def _insert(self, p, log=True):
        self.all.append(p)
        if p.error is None:
            self.islands[p.island].append(p)
        if log:
            with open(self.path, "a") as f:
                f.write(json.dumps(asdict(p)) + "\n")

    # ---- API ----
    def next_id(self):
        return len(self.all)

    def add(self, p):
        with self.lock:
            p.id = len(self.all)
            self._insert(p)
            self.since_reset += 1
            if self.since_reset >= self.reset_every:
                self._reset_islands()
                self.since_reset = 0
            return p.id

    def seed(self, text, score, metrics=None):
        for i in range(self.n_islands):
            self.add(Program(0, i, text, score, model="seed", metrics=metrics or {}))

    def sample(self, k=2):
        """Pick an island and k of its programs (softmax on score), worst first."""
        with self.lock:
            island = self.rng.randrange(self.n_islands)
            pop = self.islands[island]
            if not pop:
                return island, []
            # keep the best version of each distinct text
            best = {}
            for p in pop:
                if p.text not in best or p.score > best[p.text].score:
                    best[p.text] = p
            pop = list(best.values())
            top = max(p.score for p in pop)
            weights = [math.exp((p.score - top) / self.temperature) for p in pop]
            chosen = []
            for _ in range(min(k, len(pop))):
                i = self.rng.choices(range(len(pop)), weights)[0]
                chosen.append(pop.pop(i))
                weights.pop(i)
            chosen.sort(key=lambda p: p.score)
            return island, chosen

    def best(self, n=1):
        ok = [p for p in self.all if p.error is None]
        return sorted(ok, key=lambda p: p.score, reverse=True)[:n]

    def _reset_islands(self):
        """Re-seed the worse half of the islands with the best program of a better one."""
        def island_best(i):
            return max((p.score for p in self.islands[i]), default=float("-inf"))
        order = sorted(range(self.n_islands), key=island_best)
        keep = order[self.n_islands // 2:]
        for i in order[: self.n_islands // 2]:
            donor = max(self.islands[self.rng.choice(keep)], key=lambda p: p.score)
            self.islands[i] = [Program(donor.id, i, donor.text, donor.score, [donor.id], "reset", None, donor.metrics)]
