# Replay extractor port to engine 2.0.0 (cambc 4.0.0)

These are drop-in replacements for `analysis/engine.js` and `analysis/analyse.py`
on branch `analysis/sprint1` (base commit 5c90c61). They are kept here because
intel does not push to the analysis branch. The `*.diff` files show the change
against those originals.

## Install

From a checkout or worktree of `origin/analysis/sprint1`:

    cp genome/intel/tools/extract_v2/engine.js genome/intel/tools/extract_v2/analyse.py <analysis>/
    cp ~/.cache/cambc/assets/*/visualiser/assets/v2_0_0-*.wasm <analysis>/engine/v2_0_0.wasm

The wasm comes with cambc 4.0.0 (`cambc` downloads the visualiser assets on first use).
Run the extractor as before, with `CAMBC_WASM=<analysis>/engine/v2_0_0.wasm` for 2.0.0
replays and the default (v1_0_3.wasm) for older ones. One engine per run: split
mixed batches by `engine` version first.

## What changed in the snapshot

`Game_Visualiser_TimelineSnapshotSize()` is 42840 in v2 (40152 in v1). engine.js
picks the layout from the size:

- 84 items (v1: 42). `ci = 168` bytes are added to each champion record
  (stride 252 + ci). The fields after the item block move by ci:
  - consumables at o+ci+216
  - abilityTargets at o+ci+232/236
  - stun at o+ci+248/240
- Everything after the champion list moves by `ca = 2688`: camps, groups, wards
  and spells.
- ITEMS and analyse.py's FAM list are extended with the 7 new families
  (Tribute, Capture, Prospector, Hunter, Skirmish, Greed, Collectors; ids 42-83).

## Validation

All 50 batch-13 replays (engine 2.0.0) extracted. Compared with the official
match summaries, team gems, per-champion kills and the champion picks match on
every game. The final round is off by one (1013 vs 1012), the same convention as
the v1 extractor.

`design_v2_0_0.json`: settings, champions and camps dumped with analysis/designs.js and the v2_0_0 wasm. The item records are left out: designs.js reads them with the v1 layout, which gave garbled names for v2. The item stats are in ENGINE2.md (from the in-game probe).
