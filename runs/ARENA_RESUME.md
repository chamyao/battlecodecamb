# hyb5 arena resume

State: EC2 hyb5 stopped at the hyb5-g3 round boundary (hold 17:40 UTC, 186 programs, g3 boundary validation not yet
run: the resumed league validates it first). Code: funsearch/runs 5627bd8 (contains deploy/v0 2e1ff7e, the arena
engine). runs/ is committed here (it is gitignored on funsearch/runs).

Start: POST $ARENA_URL/runs with the body in runs/arena_resume.json (X-Arena-Client: hybrid).

Budget: the league's --budget is cumulative over generations (funsearch.league.spent sums the costs in
runs/hyb5-g*/programs.jsonl: $9.61 so far). --budget 16 (the arena per-run cap) therefore leaves $6.39 of new spend;
--budget 25.0 (the original) leaves $15.39 and needs the per-run cap raised to 25 (actual new spend <= 15.39).

Changes vs EC2's last command line (runs/hyb5.cmdline), per the FunSearch lead (H21b/H23/H24):
- island 3 seed v21 (was hyb5-g3-76); --protect-islands, --fuel-islands, --island-axes dropped; fuel:1 in --axes
- --no-tune-children (climb measured as noise); yield term = gems submitted vs v21 (default --yield-metric)
- --helpers-runs runs (arena args take relative paths only: the helper library is rebuilt from hybrid's own runs;
  pure/style/tune runs are not on this server path)
- --tune-opponents dropped (unused without the climb)
