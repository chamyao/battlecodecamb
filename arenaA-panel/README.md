# Arena A panel measurements (genome/search, runtime genome/v0 db3f945, fuel 1.0)

- panel-a458-80.jsonl: seed, A458, A352, A462 (arenaA-1) vs style-gconv1, tune-v20-L1, rall2-ca4-lean-g, v7,
  opp-tune5-metadraft, tune-v20-L1c over the 80 distinct games (40 maps x 2 sides, --bot-seeds). Games are fixed by map
  and side, so this is the full information for each pair.
- panel-a458.jsonl: the same pairs, 400 games on seed 31337 without --bot-seeds (policies seeded per game, not as
  deployed); kept for reference.
- panel5-db3f945.jsonl: seed, A659, A711, A662, A734 (arenaA-3) vs the 13 panel-A3 opponents at genome/v0 db3f945
  (80 distinct games, bot seeds), from a clean db3f945 build: the control showing genome/simspeed 4b60b58 is not
  bit-identical to db3f945 for genome-vs-policy games (compare panel-A3/panel.jsonl, 4b60b58).
