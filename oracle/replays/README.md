# Differential replay of official games (.repl26a) through the simulator

Replays store only actions. `dump.js` walks one through the official engine (the visualiser's
WASM build, `analysis/engine.js` + `analysis/engine/v1_0_3.wasm` on the `analysis/sprint1`
branch; the version cambc 3.0.5 runs) and writes one JSON line per champion turn: the full
state just before its first input (positions, HP, alive, gold, gems, kills; camp HP;
submitted gems) and its input actions. `rereplay.py` feeds both teams' actions to cambsim
(drafts included) and compares the simulator's full state (`Api.truth()`) with the engine's
at every champion turn start; it stops after `--max` differences.

    git archive origin/analysis/sprint1 analysis | tar -x -C /tmp/an
    CAMBC_ENGINE_JS=/tmp/an/analysis/engine.js node oracle/replays/dump.js GAME/replay.repl26a /tmp/g.jsonl
    PYTHONPATH=sim/build python3 oracle/replays/rereplay.py maps/MAP.map26a /tmp/g.jsonl

The map is embedded in the replay (`analysis/mapinfo.py` names it from our pool).
Replay conventions the replayer handles: only steps that consume an input are actions (a
recall completing shows up as an automatic Move); "Movement blocked" is any rejected move
input (must fail here too); 5 shards bought at once show up as +1 emblem; ground-targeted
abilities are cast at the tile, self-cast at oneself; attacks on altar tiles hit the lock.

`wardmoves.js` lists every 1-tile move onto a tile holding a ward that is not the mover's own,
with the engine's ward table (`Game_Visualiser_ReadState`, omniscient perspective {2, -1}:
wards at +133436, stride 40: owner +12, team +16, x +20, y +24, disabled +36).

Results: docs/ENGINE_FINDINGS.md, "Real ladder games".

## Engine 2.0.0 (cambc 4.0.0)

`rereplay_v2.sh BUNDLE MAP [MAX]` does the same for 2.0.0 games: it sets up intel's port of `engine.js` (84 items,
the 2.0.0 snapshot layout; origin/genome/intel `genome/intel/tools/extract_v2`) with the `v2_0_0` visualiser wasm
from the cambc 4.0.0 asset cache, and takes the bundle `cambc run -o` writes. Needs `sim/build/cambsim*.so` (pip
install pybind11, rebuild `sim/build`). Oct 30: real games replayed with 0 divergences (00lost-world 4152 turns,
00reverse-spiral 18000, 00quarry 15284).
