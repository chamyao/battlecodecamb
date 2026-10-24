# Handoff: hybrid FunSearch line

Snapshot as of 2026-10-24 ~17:40 UTC. Read `CLAUDE.md`, `docs/STRATEGY.md` and `docs/FUNSEARCH.md`
first. This line reports to the FunSearch lead (session_01YJxccSM2xmnTtoiFjrAzf3).

**Channels (since 17:30 UTC, Cham):** simulator matches, batches and leagues go through the **arena**
(`docs/REMOTE_WORKER.md` on `main` 1983be7; `$ARENA_URL/docs`), with `X-Arena-Client: hybrid` and the
deploy/v0 engine sha `545c7b1e644b1e5c82ba07b3a8aa8945ab2dc190` (not the default). Candidates are registered
under immutable names and join the `main` league (`league add main <name>`) when they would be sent; standings
go on PR #5. The old `remote/hybrid` -> `jobs/hybrid` PR channel and `jobs/hybrid/JOBS.md` are retired for
anything the arena covers. FunSearch runs on the arena need a hybrid token from Cham (never commit or message it).
Verdicts still go on PR #1.

## Goal

Find bot policies that beat the live ladder bot, starting from the strongest policy from any
source: hand-written fixes, the tune line, other FunSearch lines. Edits come from Claude (Haiku 5.5,
with Opus 5.5 every 10th call). Inside the league a candidate becomes the line's best only if it
clearly beats the current best on fresh games. It is worth sending to the coordinator for the
ladder only if it also clears the cambc-exact check (below).

## Base policies

| policy | what it is | status |
|---|---|---|
| `policies/tune-3.policy` | tune-2 + dash to a camp goal only if `fuel_remaining() > 55000` | live ladder v15 ("tune-3 v2"; v2 is the bot build where fuel_remaining() works). Real cambc 39/80 vs tune-2 (even), zero 100k-cap turns |
| `policies/tune-2.policy` | tune-1 with `bag_ready = gems() >= 25 ... or health() < 0.3*max_health()` (was 10 / 0.5) | tune line: +10.9 vs tune-1 on 800 fresh games; cambc-exact 57.5% (my run: 46/80 vs tune-1) |
| `policies/tune-1.policy` | v7zg-cast with draft vendetta, vesper_vale, tavi, ryth, ren | **current best of the hybrid league (hyb4 state)**. Real cambc 49/80 vs v7zg-cast |
| `policies/v7zg-cast.policy` | v7-zerogem + ability-type-aware casting (from hybrid FS program #14, an Opus edit) | cambc-exact 49/80 vs v7-zerogem; 61.3% on 800 fresh games |

Lineage of the hybrid line: fs-1 (pilot) -> fs-2 (league3) -> v5d-fs2 (hand merge) -> v7 ->
v7-zerogem -> v7zg-cast (#14 graft) -> tune-1 -> tune-2 -> tune-3.

## What's running, and where

- **hyb5** (league `--name hyb5`, exploration mode) runs on **EC2** (session_01Knzq5vzttJNCCzc9dRHHkQ, state
  pushed to `remote/hybrid/runs/` every ~5 min). It stays there until Cham issues an arena token for FS runs.
  Changes reach EC2 by send_message; it applies them at round boundaries (hold + SIGTERM by PID, merge
  funsearch/runs, rebuild, pytest, relaunch). Jobs H1-H24 are logged in `jobs/hybrid/JOBS.md` (history).
- **Current hyb5 setup** (after H21b/H23/H24): best/bar v21 (`policies/pool/v21.policy`, live ladder
  v22/v24); islands v21, style-gconv1 (v23, diversity), v20, v21; `--fixed` includes style-gconv1;
  `--axes conversion:5,disengage:2,...,fuel:1`; `--yield-weight 0.25` (gems submitted per game vs v21 in
  the same screen games, scale 50; gems per capture is report-only: it can be raised by giving up volume);
  `--screen-maps cover --rescreen-top 3` (screens cover every map; the old with-replacement draw covered ~29
  of 40 and overstated map-specific lines by ~20 points); `--no-tune-children` (climb measured as noise:
  +0.001 over 21 accepted climbs); `--helpers-runs` (shared helper library); new-vocabulary variant 20%
  (16 sensors); exec blocks vs builtin:starter; novelty lambda.
- **Candidate checks** (any FLAG or promotion): the 80-game all-maps fights.py check vs v21 (win, gems
  submitted, gems/capture, captures, tributes, camp deaths, out/out2 shares), `funsearch.evaluate.fuel_check`
  (big-world + ambush, --enforce --bot-seeds), the required pool league, conversion. From now on run the
  matches/leagues on the arena (engine 545c7b1).
- **Measured dead ends tonight:** the #82/#76 line (teleport + altar dashes: +2.9 gems/capture but 64 vs 82
  captures, submitted gems level with v21); per-child constant climb (noise); island-3 fuel fitness (fixed
  fuel, kept the low volume).

## Promotion rules (funsearch/league.py)

- At each round boundary (every `--round` programs in the run; it survives restarts) the run's top
  3 distinct programs plus queued challengers are validated on fresh seeds (5000011, 6000011;
  400 games per opponent per seed).
- Promote when the head-to-head win rate vs the best is 2 SE above 50%: >= 53.5% over 800 games;
  a 50-53.5% result gets 800 more (seeds 7000011, 8000011) and needs >= 52.5% over 1600. It must
  also drop no more than 3 points vs any older or fixed member.
- cambc-exact: `cambc_check()` plays all 40 maps x 2 sides with `--bot-seeds`, which reproduces
  real cambc games exactly (v7 vs v5d-fs2 = 0.5875 = the real 47/80). It's logged for each
  promotion; >= 0.55 marks it ladder-ready, the bar for sending a candidate to the coordinator. It
  is not a gate inside the league.
- Challengers: append policy paths to `runs/hyb4.challengers`. They're judged at the next
  boundary, injected as parents, and become fixed opponents in the next generation. A winning
  challenger becomes the best as-is.
- `runs/hyb4.hold`: the league waits at the next boundary; merge or rebuild, then remove the file.
- Opponent pool in the run: starter@0.25, best@3, members, fixed. It was trimmed from 12 to 8
  opponents; v4, v5d, fs-2 and fs-p1 were dropped as far below the best.

## Budget

- Hybrid line cap **$40** (raised from $30 by the FunSearch lead, 16:40 UTC). Spent $23.26: hyb/hyb2/hyb3
  $0.18, hyb4 on the old remote-server $9.91, hyb4 on EC2 $1.26, xc/xp exploration test $3.21, hyb5 $8.70
  (to 16:40). hyb5 keeps its remaining ~$16.30 (`--budget 25` from its start). Lines recorded in
  `remote/hybrid/runs/SPEND.md` (H22). Arena runs are capped at $10 per run, $40 in total.
- Cost per call: Haiku ~$0.0016, Opus ~$0.072.

## What worked (with numbers)

- **Pilot** (seed v1): 150 programs for $0.66 gave fs-1, 97% vs starter and 80% vs v1 on 800 fresh
  games (old prices). All 6 lineage edits were Haiku.
- **League3** (best v3) promoted **fs-2**: Treasure/Jungle shards and tribute at >= 10 gems, 62.5%
  vs v3. Grafted onto v5d -> **v5d-fs2**: 61.3% vs v5d, 71.6% vs v5, 72.6% vs v4.
- **hyb2 #14** (Opus): ability-type-aware casting (shield/heal on self, dash kept for
  escape/travel). Alone it was 53.75% cambc-exact vs v7 (too noisy to promote). Grafted onto
  v7-zerogem -> **v7zg-cast**: 49/80 cambc-exact, 61.3% on 800 fresh games, and it went live.
  Lesson: a search find built on an older base can stack with later hand fixes, so try grafting
  before dropping it.
- **hyb4-g1 boundary** (best v7-zerogem; 800 fresh games each): tune-1 69.8% (cambc-exact 70.0%,
  promoted); v7zg-cast 62.0%; v7zg-monozone 59.1%; league #27 53.6% (the first pure-FS program to
  clear the statistical bar); #36 49.4%/1600; #38 47.0%; fs-p1 37.1%; v8 failed transiently.
- **Infrastructure:** behavioural-twin reuse (identical screening means identical play), two-stage
  confirmation (the first quarter of the same games is a prefix; verified game by game), a
  validation cache, restart-safe rounds and pending challengers.

## What didn't

- **#27's team focus fire** (team_target / set_team_target) grafted onto tune-2 (=
  `policies/tune2-focus.policy`): 39/80 vs tune-2 cambc-exact, i.e. neutral. Still queued.
- **v6 / ability casting by hand** (coordinator): failed real cambc, 38/80 vs v5d-fs2.
- **Ladder tactic rules as constants** (coordinator tests): strict rich-group preference 33-38/80;
  local_strength thresholds 20-53% vs a 51% mirror. They're in the prompt as "directions, not
  rules".
- **Constant tuning** around tune-2/3 finds nothing better (tune line); structural changes are
  needed.
- **The cloud container:** reclaimed whenever the session is idle (uptime 0 at every idle
  check-in, 20 min while active). That's why compute moved to remote-server.

## Open leads / next steps

1. Get the hyb4-g2 verdict. Expected: tune-2 or tune-3 becomes the best (they're even; prefer tune-3
   for its fuel safety if neither clears the other). After that set `--round 30`.
2. Structural camp choice is the main open lever (the v7 loss analysis says scoring rate: ~15 gems
   per capture vs 21-60 for winners, 27% gold-only captures, bag 14 vs 30-39). The prompt has the
   KEY TOOL note: group_gems / group_threat / group_hp / rich_spawns / group_tiles and the skip
   formula with strength(). Watch whether children use it and what it scores.
3. Team monolith takes with 3+ champions (claim_count). The analysis says one winner's whole
   margin came from both monoliths.
4. fuel_remaining() gates now work on the bot; that's in the prompt.
5. Trim the stale "What our ladder losses taught us" section in funsearch/llm.py: it's the
   fs-1-era list (retreat, items, draft), all done since v3.
6. Graft good FS programs onto the newest base (as with #14 -> v7zg-cast) rather than dropping
   them when the base moves.

## Things only I know

- `pgrep -f <pattern>` / `pkill -f` match your own shell when the pattern is in its command line.
  Use `pgrep -a -x python3 | grep ...`. Stop thread-pool runs with SIGTERM; SIGINT can hang them.
- Checking out a branch that tracks runs/ files (funsearch/league-state) and switching back
  deletes them from the working tree; read them back with `git show <commit>:path`.
- The prompt has two owners: catalog.py's "Observations" paragraphs and block DOCS also come from
  the coordinator's interp/v0 commits; my notes are the ladder observations and the KEY TOOL note.
  Before restarting a run, check that every name the prompt calls is a real block. The strength()
  docs bug cost ~20 children across lines.
- interp_eval game g uses seed `seed*1000003+g` and map `chosen[g//2]`, so shorter runs are exact
  prefixes. Two-stage confirmation relies on that.
- v8 once failed validation without a logged reason; skipped candidates are logged now.
- Opus vs Haiku so far: Opus 30% of children beat their parent (12/40) vs Haiku 21% (89/416);
  Opus is ~45x the cost per call. One of three winning lineages ended in an Opus edit (#14).
- Useful tools: `python3 -m funsearch.validate --run <name> --top 3`, `python3 -m
  funsearch.proposals <run>` (block wishes; none so far), and `funsearch.league.cambc_check` and
  `win_rates` for ad-hoc checks. docs/results/ has the v7zg-cast per-map table and an example of
  the exact prompt sent.
