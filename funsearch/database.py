"""Program database with islands (FunSearch): programs evolve in separate
populations; the weakest islands are periodically re-seeded from the best."""
import json
import math
import random
import re
import threading
from dataclasses import asdict, dataclass, field

# exploration (--explore): behaviour features of a program, for the quality-diversity archive
MACRO_FEATURES = (("ward", ("place_ward", "bushes")), ("teleport", ("teleport_to", "buy_teleport")),
                  ("shared", ("write_shared", "read_shared", "write_draft")), ("tileaoe", ("cast_at_tile",)),
                  ("claims", ("claim(", "claim_count")))


def draft_core(text):
    """First two champions of the draft's pick order, or 'random'."""
    picks = re.findall(r"pick\(\s*champ_(\w+)\(\)\s*\)", text)
    return "+".join(list(dict.fromkeys(picks))[:2]) or "random"


def fight_style(metrics):
    """Kills and deaths per game (mean over opponents; deaths include camps), each bucketed low/mid/high;
    'na' without the data."""
    per = [m for m in (metrics or {}).values() if isinstance(m, dict) and "kills" in m and "deaths" in m]
    if not per:
        return "na"
    kills = sum(m["kills"][0] for m in per) / len(per)
    deaths = sum(m["deaths"][0] for m in per) / len(per)
    k = "k-lo" if kills < 5 else "k-mid" if kills < 8 else "k-hi"
    d = "d-lo" if deaths < 10 else "d-mid" if deaths < 13 else "d-hi"
    return f"{k},{d}"


def macro_kind(text):
    return "+".join(name for name, keys in MACRO_FEATURES if any(k in text for k in keys)) or "plain"


def cell_of(text, metrics):
    return f"{draft_core(text)}|{fight_style(metrics)}|{macro_kind(text)}"


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
        # quality-diversity archive (exploration): the best program per behaviour cell (cell_of)
        self.archive = {}
        # executed-block novelty (exploration): n_b = programs that execute block b; a program's novelty
        # is sum over its executed blocks of log(N / (1 + n_b)). Used only in parent selection
        # (weight exp(score/T + lambda * novelty)) and in a second archive keyed by the program's
        # rarest executed block; never in the score, confirmation or promotion.
        self.novelty_lambda = 0.0
        self.block_counts = {}
        self.n_exec = 0
        self.rare_archive = {}

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
            if p.score > float("-inf"):
                c = cell_of(p.text, p.metrics)
                q = self.archive.get(c)
                if q is None or p.score > q.score:
                    self.archive[c] = p
                blocks = p.metrics.get("exec_blocks")
                if blocks and p.model != "reset":
                    rare = min(blocks, key=lambda b: (self.block_counts.get(b, 0), b))
                    self.n_exec += 1
                    for b in blocks:
                        self.block_counts[b] = self.block_counts.get(b, 0) + 1
                    q = self.rare_archive.get(rare)
                    if q is None or p.score > q.score:
                        self.rare_archive[rare] = p
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

    def seed(self, text, score, metrics=None, islands=None):
        for i in (range(self.n_islands) if islands is None else islands):
            self.add(Program(0, i, text, score, model="seed", metrics=metrics or {}))

    def novelty(self, p):
        blocks = p.metrics.get("exec_blocks")
        if not blocks or not self.n_exec:
            return 0.0
        return sum(math.log(self.n_exec / (1 + self.block_counts.get(b, 0))) for b in blocks)

    def sample_archive(self, k=2):
        """Exploration: k elites of distinct, uniformly chosen archive cells (behaviour cells, plus
        rarest-block cells when the novelty term is on), worst first; the child goes to the best one's
        island. None while there are fewer than two cells."""
        with self.lock:
            cells = {("cell", c): p for c, p in self.archive.items()}
            if self.novelty_lambda:
                cells.update({("rare", b): p for b, p in self.rare_archive.items()})
            # distinct programs only
            uniq = {}
            for key, p in sorted(cells.items()):
                # one key type (sorted() below): seeds are per island, others per program
                uniq.setdefault((p.id, p.island if p.model == "seed" else -1), (key, p))
            if len(uniq) < 2:
                return None
            picks = self.rng.sample(sorted(uniq), min(k, len(uniq)))
            chosen = sorted((uniq[x][1] for x in picks), key=lambda p: p.score)
            return chosen[-1].island, chosen

    def sample(self, k=2):
        """Pick an island and k of its programs (softmax on score), worst first."""
        with self.lock:
            island = self.rng.randrange(self.n_islands)
            pop = self.islands[island]
            if not pop:
                return island, []
            # keep one version of each distinct behaviour (screening fingerprint, else text): the
            # best-scoring, then the shortest, so parent slots are not spent on look-alikes
            best = {}
            for p in pop:
                key = p.metrics.get("screen_fp") or p.text
                q = best.get(key)
                if q is None or (p.score, -len(p.text)) > (q.score, -len(q.text)):
                    best[key] = p
            pop = list(best.values())
            top = max(p.score for p in pop)
            if self.novelty_lambda:
                nov = [self.novelty_lambda * self.novelty(p) for p in pop]
                top_nov = max(nov)
                weights = [math.exp((p.score - top) / self.temperature + n - top_nov) for p, n in zip(pop, nov)]
            else:
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
