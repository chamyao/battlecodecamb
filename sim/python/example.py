"""Example: a Python policy against the built-in starter, plus a batched C++-only run.

Run from sim/:  PYTHONPATH=build python3 python/example.py
"""
import os, random, sys, time
import cambsim

MAPS = os.path.join(os.path.dirname(__file__), "..", "..", "maps")


class Wanderer(cambsim.Player):
    """Drafts randomly, then walks randomly and hits whatever is in range."""

    def __init__(self, seed=0):
        super().__init__()
        self.rng = random.Random(seed)

    def turn(self, api):
        if api.champ < 0:  # draft bot
            api.draft_champion(self.rng.randrange(11))
            return
        me = api.my_champion()
        err, info = api.champion(me)
        if err or not info.state & 1:
            return
        err, enemies = api.enemies()
        for e in enemies:
            err, ci = api.champion(e)
            if err == 0 and max(abs(ci.x - info.x), abs(ci.y - info.y)) <= info.attack_range:
                api.attack(1, e)
                break
        dx, dy = self.rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)])
        api.move_to(info.x + dx, info.y + dy)


def main():
    m = cambsim.load_map(os.path.join(MAPS, "00elkring.map26a"))
    print(f"map {m.name}: {m.width}x{m.height}, {m.num_camps} camps, walls {m.walls.sum()}")
    t = time.time()
    r = cambsim.Match(m, Wanderer(1), cambsim.builtin_player("starter", 2), seed=3).run()
    print(f"python vs starter: {r} ({time.time() - t:.2f}s)")

    threads = os.cpu_count() or 1
    games = 4 * threads
    t = time.time()
    rs = cambsim.run_matches([os.path.join(MAPS, "00elkring.map26a")], "starter", "starter", games=games, threads=threads)
    dt = time.time() - t
    wins = sum(x["winner"] == 0 for x in rs)
    print(f"{games} starter games on {threads} threads: {games / dt:.1f} games/s, team A won {wins}")


if __name__ == "__main__":
    sys.exit(main())
