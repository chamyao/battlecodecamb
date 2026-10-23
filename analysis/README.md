# Sprint 1 replay analysis tools

The tournament replays (`data/sprint1/replays`) store only actions; full state comes
from replaying them through the official engine. `cambc summary` needs a CAMSTAT file
that requires a login, so instead we run the engine's WASM build (shipped inside the
`cambc` visualiser; `cambc view` serves it) under Node:

- `engine/v0_0_3.wasm`: the engine version every Sprint 1 replay declares (bytes 8-10 of
  the `.repl26a` header). Note: this is the visualiser's "original" ruleset, older than
  the current v1_0_3 "balance" engine in cambc 3.0.5 that `docs/GameRules.md` describes.
  `engine/v1_0_3.wasm` is the current one, kept for comparison.
- `engine.js`: loads a replay, walks its timeline step by step, decodes the visualiser's
  timeline snapshot (layout copied from the visualiser bundle).
- `extract.js`: one replay -> compact JSON (draft, per-round curves, events with state
  diffs: gold/gems/kills/alive/items per champion, attack targets and damage).
- `run_all.sh OUT`: unpack all bundles and extract all 225 games (~1 min, 8 cores).
- `mapinfo.py` / `map26a.py` (from `sim/engine`): decode the map embedded in a replay.
- `sides.py OUT sides.json`: which team played side A/B in each game (by draft
  fingerprints per map; reproduces every series score in the bracket).
- `analyse.py`: the numbers in `docs/SPRINT1_ANALYSIS.md`.
