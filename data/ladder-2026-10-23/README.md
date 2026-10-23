# Ladder, 23 Oct 2026: ranked games among the top 12

285 finished ranked matches (09:40-14:10 UTC) in which both teams were in the ladder's top 12
at fetch time, fetched with `analysis/fetch_ladder.py` (needs `cambc login`). All use engine
v1_0_3 (current rules) and the 40 public-pool maps.

- `matches.json`: platform metadata (teams, sides, map, result, draft) and the ladder snapshot.
- `replays/<matchId>.zip`: replay bundles (`cambc view` opens them).
- `sides.json`: input for `analysis/analyse.py` (made by `analysis/ladder_prep.py`).

Reproduce the tables in `analysis/ladder_report.md`:

    python3 analysis/ladder_prep.py data/ladder-2026-10-23 OUT > jobs.txt   # (copy the dir first: it writes unpacked/)
    xargs -P 8 -n 3 sh -c 'CAMBC_WASM=$2 node analysis/extract.js $0 $1' < jobs.txt
    TOP4="prism best girl,Intercontinental Fish,policy wonk,procless" python3 analysis/analyse.py OUT data/ladder-2026-10-23/sides.json OUT/results.json
