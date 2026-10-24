# Handoff: tune line (tuning + draft search)

Written 2026-10-24 by the outgoing tune-line session. Branch: `tune/runs`. Read `CLAUDE.md` and
`docs/STRATEGY.md` first (compute is part of the action space; fuel is a rule, not a constraint).

## Goal

Improve the live line by pure search: draft orders and policy constants, plus small structural
fixes when a diagnosis calls for them. **No LLM calls**: this line has spent $0 of API budget,
only CPU. Never submit to the ladder (the coordinator does that). The coordinator is
`session_01S2SPSVky6e84fDzQLxJKWp`.

## Current base and promotions (all in `policies/` on `tune/runs`)

| Policy | Parent | Change | Fresh-seed result vs parent |
| --- | --- | --- | --- |
| tune-1 | v7zg-cast | draft vendetta, vesper_vale, tavi, ryth, ren | 60.75 / 57.0%, cambc80 50/80 |
| tune-2 | tune-1 | `bag_ready`: gems >= 25 (was 10), hurt at 0.3 (was 0.5) | 60.75 / 61.0%, cambc80 46/80 |
| tune-3 | tune-2 | camp-goal dash only if `fuel_remaining() > 55000` | 41/80 cambc; big-world suspensions 1.06 -> 0.56/game; neutral |
| **tune-5** | tune-3 | dash from distance > 2 (was 4), `jungle_n = floor(rest / 2)` (was / 3) | 53.25 / 53.25% (seeds 9019/9020), cambc80 47/80 |
| tune-6 (map fix) | tune-3 | monolith fallback after round 800 + tribute before a group with `group_threat >= 240` | 52.75 / 50.0% (seeds 9021/9022), cambc80 42/80, no map lost both sides; starvation 80/63/92% vs Icecream/v7zg-cast/metab (tune-3 52/48/50) |

- **tune-5 is the newest tune-line promotion** (commit a9567a8, sent to the coordinator). It was
  not yet built or shipped when this was written; tune-3 v2 is live. Ask the coordinator which is
  the base before starting new work.
- tune-4 is the coordinator's unshipped variant on interp/v0 (monolith fallback limited to
  monolith-only-gem maps). It's bad: 41.75% all-map, collapses on starvation. Don't build on it.
- The hybrid league took tune-1 as its best at one boundary (69.8% vs v7-zerogem); tune-2 was
  queued as a challenger.

## Promotion rules (current)

- **Head-to-head > 52% vs the current base**, on 2 x 400 fresh games (per-game seeds; never the
  seeds used for screening). Cham's rule; the old +5 bar is gone. Also: no gauntlet drop of more
  than 3 points, and report the cambc-exact check (`interp_eval --a cand --b base --games 80
  --bot-seeds` over all 40 maps, seed 1, about 40/80 or better).
- **Map fixes** (arena-driven) use a separate bar: >= 49% over 2 x 400 vs base, >= 40/80 cambc80,
  no map lost on both sides in cambc80 (`lost_both_sides` in `funsearch/altar_bag.py`), and a
  clear gain on the target maps vs the stand-ins.
- Save as `policies/tune-<n>.policy` with a header comment: `line: tune`, parent, scores. Commit
  to `tune/runs`, push, and send the coordinator path + commit + scores.

## Tooling (all on `tune/runs`)

- `funsearch/race.py`: `h2h(a, b, games, seed, bot_seeds=)` on the full map list (game g is
  map (g/2) % 40, sides alternate); `screen()`; `confirm()` (2 x 400 + gauntlet + cambc80);
  `set_draft` / `chain_draft`. `GAUNTLET` = v4, locker, fs-2, starter, v5d-fs2, v7,
  v7-zerogem, v7zg-cast, opp-icecream, opp-odyssey, opp-metab.
- `funsearch/draft_screen.py`, `draft_screen2.py` (BASE TAG SEED): draft screens.
- `funsearch/const_screen.py` + `const_screen_grid.py` (exact-snippet grid: treasure, jungle,
  strength, retreat, gemret, bag, baground, baghp, dash, monolith). Re-centre the grid when a
  constant changes (bag and baghp are centred on tune-2's 25 / 0.3).
- `funsearch/confirm_screen.py BASE SCREEN.json TAG draft|const TOP`: confirm the top of a screen.
- `funsearch/combo_confirm.py BASE TAG S1 S2 'old=>new' ...`: confirm a combination.
- `funsearch/map_diag.py MAP`: per-map ablation with `GAME_EVENTS=1` (deaths, gems lost on death,
  captures).
- Fix screens: `fuel_guard*.py`, `waypoint.py`, `skip_screen.py`, `bank_fix.py`, `mono_fix.py`,
  `threat_bank.py`, `altar_bag.py`, `starv_confirm.py`.
- Test opponents: `policies/opp-icecream.policy`, `opp-odyssey.policy` (v7zg-cast with ladder
  drafts), `opp-hunter.policy` (too weak), `opp-metab.policy` (arena house bot stand-in; see below).
- Rebuild after every interp/v0 merge: `cd interp/build && cmake .. && make -j4 interp_eval
  fuel_turns`. Never compare numbers across simulator builds. Current build: interp/v0 c92239d.
- Speed: about 25-35 s per 200 games on 4 threads (big maps are slower).

## What's running and where

- **Here (cloud container):** nothing running. `r800+T240` finished and is `policies/tune-6.policy`.
- **remote-server:** two jobs were sent by session message *before* the GitHub channel existed,
  with no confirmation back yet. Treat them as not done.
  - The jobs: clone `tune/runs` into `~/bc/tune`, build, run tests, then
    `funsearch/combo_confirm.py ... combo-t3-dash2-jungle2-b 9025 9026` (third 2 x 400 for
    tune-5) and `funsearch/altar_bag.py`.
  - `jobs/tune/JOBS.md` is still the placeholder and `remote/tune` has no STATUS yet.
  - To talk to remote-server, use the protocol in `docs/REMOTE_WORKER.md` on main and the channel
    PR **#4** (`remote/tune` -> `jobs/tune`). Write the jobs above (rebased on tune-5 as needed)
    into `jobs/tune/JOBS.md`, comment on #4, and subscribe to it.
  - Run at `nice -n 15`, about 4 threads, so the three FunSearch lines get the CPU first.

## What worked and what didn't (numbers are fresh-seed confirms unless marked "screen")

Draft (the biggest lever):
- Random-draft regression over 8000 games (v5d): vesper_vale and tavi strongest; ren and marcella
  negative as additive effects; draft order beyond the top 3 matters less.
- 233-order screen on v7zg-cast: mean 50.3%, so most screen leaders are noise. The winner held up
  (60.5 screened -> 58.9 confirmed). That's tune-1.
- Draft pass 2 around tune-1's order (91 orders, on tune-3): the top neighbours confirmed at
  45-48%. **The tune-1 order is locally best.**
- Counter-picks can't be expressed: `unpicked_champions()` only covers our own picks, and both
  teams may pick the same champion. It would need a new block.

Constants:
- On tune-1: every single change confirmed within noise (best 53.8 / 53.5). But **bag 25 + hurt 0.3
  together gave +10.9** (tune-2). Near-miss pairs can interact, so always test the best pair.
- On tune-3: the best single changes were dash > 2 at 54.4 and jungle 1/2 at 53.4; together
  53.25 = tune-5. Bag 30 / 35 is flat (50-51); treasure 1/3 is 47.8; strength 1/3 is 49.6.
- Strong negatives (screen): never dash 36%; all-Treasure shards 17.5%; all-strength 36.5%;
  retreat at 0.5 health 34%; dash > 12 41.5%.

- On tune-5 (grid seed 9311, confirm seeds 9331/9332): the grid is flat (best 53.0 screen). Confirms: jungle /3
  50.75 (cambc 41/80), jungle 0 50.75 (33/80), baground 1000 47.9, jungle/3 + baground1000 47.25. **tune-5's
  constants are locally optimal; no more grid work on this base.**

Fuel (tune-3 work):
- Goal-dash gate F, 600 big-world games + cambc80 + 400 all-map:
  - F <= 45k never fires (identical to tune-2).
  - F = 55-65k halves suspensions (1.02 -> 0.45-0.50) with an unchanged win rate.
  - F >= 70k collapses big maps (28%).
  - The sim reads about 53-56k at the gate on ordinary turns, so it really thins dashes on
    already-heavy turns. That's fine because the 55-65k range is flat.
- Suspension costs about one champion turn (the bot resumes next round), so about 1/game is noise.
- **Waypoints for long moves fail**: about 15 suspensions/game. A moving target misses the
  distance-field memo every turn; a fixed far target misses only once.
- The camp-skip formula (`group_threat * group_hp / (K * (1 + allies))`) is shelved. There's no
  `strength()` block in my build (the coordinator says one is now calibrated on interp/v0), and
  the alternative-goal move caused 10-34 suspensions/game.

Arena house bot metab-v3 (tune-3 scored 33 on 01hooks both sides and 0 on 01starvation):
- Diagnosis: **bag 25 is the culprit**.
  - Carried gems go to the killer, or are destroyed by camp deaths.
  - A 25-gem tribute channels 3 turns (stun, death or a lock interrupts it).
  - In the real arena, tune-1 (bag 10) won hooks 1001-110 and 1001-220.
  - On starvation, our carriers die to an effectively unkillable elk x4 group at (39,16), and the
    `team_score == 0 after round 300 -> monoliths` fallback misfires (about 360 monolith hits).
- `opp-metab` reproduces starvation (tune-3 40-50% vs it, tune-1 95%) but **not hooks** (it only
  scores about 100 gems there; its zone farming is wrong). Hooks fixes can't be validated against
  it.
- Generic early banking (cash in >= 10 when hurt or threatened) costs elsewhere: the best (hp < 0.5)
  was 49.75% all-map but 34/80 cambc. `in_danger` banking is 15%.
- Monolith fallback only after round 800 (`r800`) is **confirmed**:
  - 51.4% (52.75 / 50.0, seeds 9021/9022), cambc80 43/80, every gauntlet opponent up.
  - Starvation vs Icecream / v7zg-cast / metab: 73 / 53 / 75% (tune-3: 52 / 48 / 50).
  - Stampede and shortcut improve; pilgrimage vs v7zg-cast 25% (tune-3 35%, 60 games).
  - It fails the "lost both sides" check: it loses 00pilgrimage on both sides in cambc80.
- Threat banking (tribute first if gems >= 10 and `group_threat(goal) >= T`), screen only:
  - T240: 53.75% all-map, 41/80, starvation +13..+32.
  - T180 is similar. T60/T120 cost about 5 points.
  - `r800+T240` confirmed and passes the full map-fix bar (no map lost on both sides): that's tune-6.

opp-metab on hooks (funsearch/metab_hooks.py, 40 games as A vs tune-5 on 01hooks + 20 on starvation vs tune-3):
- Current stand-in: 0% on hooks, 110 gems vs 1016, 14 deaths, 20 captures; starvation vs tune-3 45%.
- Cohesion (walk to the nearest ally when none within 3 / 6), earlier recall (0.55), wider defend zone (8, chase 7)
  and their combos: all 0% on hooks and worse gems; cohesion also wrecks starvation (0-10%). Radius 9 is a no-op.
- So the policy language's farming bot can't reproduce metab-v3's hooks win: tune-5 farms 1000+ gems there whatever
  the stand-in does. Hooks fixes need the arena (or a stand-in with real combat micro). **Lead 4 is closed.**

## Open leads / next steps (in order)

1. Agree the base with the coordinator (tune-5 vs tune-3 live).
2. tune-6 = tune-3 + the two starvation fixes (sent as a map fix). Re-base the same two edits on tune-5
   (`mono_fix.mono` + `threat_bank.threat_bank`) and confirm under the map-fix bar.
3. Altar-count bag for hooks (`funsearch/altar_bag.py`): `keep bag_n = 25 - 15 * floor(k /
   (count(altars()) + 1))` gives bag 10 on 1-altar (k=2) or <= 2-altar (k=3) maps. Screen it alone
   and with the starvation fixes. The real evidence is the arena, not opp-metab.
4. Improve `opp-metab` so it reproduces hooks: farm elk+gem pairs in the zone; move as a group of
   4; per `docs/ARENA_METAB_V3.md` on analysis/sprint1. Then test "regroup before entering a held
   altar zone".
5. Re-run the constant grid on tune-5. Try the best near-miss pairs together.
6. Hand the hybrid league any promotion (it grafts drafts and constants onto its candidates).


## Session 2 (2026-10-24, session_01Ja9BznSBEpiUKCjkDru5e5): state at 07:20 UTC

Reporting to the FunSearch lead (session_01YJxccSM2xmnTtoiFjrAzf3); the coordinator is session_01SkG4y5RPLyyXmaTsxytUHH.
**Upload bar now**: league rating (tools/league.py, copied here with the tune/runs build path) above the live bot's beyond
the 90% interval, with a pool that includes the live bot, opp-hunter2a/b/c and the ladder stand-ins (opp-icecream,
opp-odyssey, opp-metab, opp-metadraft); post the pool list with the rating. Head to head is information only. The bot
session runs the real-cambc safety checks (crashes, 100k-cap turns, first turn < 200k).

- Live: tune5-campreset (v17) = tune5-reset (coordinator's reset fix) + camp reset (ours: attack, cast_self the reset,
  attack again, on camps; 60% vs tune5-reset).
- **Candidate: policies/candidates/tune-r-all-v2.policy**, with the lead / bot session. It is tune5-campreset + map fixes
  (r800 monolith fallback, T240 threat bank, monolith-group goal exclusion `minus(..., mono_groups)`) + safe recall
  (no recall with an enemy within 8; retreat home first; threshold 0.3). League (19 policies): v2 1725 [1712-1737],
  campreset 1672 [1659-1683]. tune-r-all (no fuel fixes) failed the bot session's fuel check (100k caps on 01starvation):
  fixed by `keep mono_groups` and gating the threat branch on fuel_remaining() > 65000 (55k does nothing).
- Fuel checks: funsearch/fuel_check.py (fuel_turns --enforce --bot-seeds vs tune5-campreset). Without --enforce,
  fuel_remaining() never drops, so gates look inert.
- Results (all in commit messages on tune/runs):
  - tune-5 constant grid flat; opp-metab can't reproduce hooks;
  - risk bank rules negative; shard stacking strongly negative (23-28%); Focus shards negative; Durability flat;
  - early disengage (retreat at 0.5-0.8 HP with an enemy near) strongly negative (12-32%);
  - 00lost-world: monolith-group exclusion fixes it (0% -> 37.5% vs metab, 32.5% -> 100% vs v7zg-cast).
- fight_metrics.py: TOP_TEAMS metrics from GAME_EVENTS (sim now logs recall / recallcut events, logging only).
- EC2 (runner/lines/tune.sh on ec2/runner; logs to remote/tune every 5 min):
  - C t5_mapfix: t5-starv 52.4%, t5-alt1 48.6%, ...
  - D2 draft_meta on tune5-reset
  - E random-draft regression over all 12 champions
  - F switch-ons, all negative: lock 32%, ward 46%, hunter 47.5%
- Never `pkill -f <pattern>` where the pattern appears in your own command: use pgrep -f "[x]yz" and kill by PID.

### Session 2, later (to 11:50 UTC)

- **Live: v20 = policies/tune-v20.policy (= policies/candidates/tune-fight-2s.policy)**: v19 (coordinator's
  rall2-ca4-lean-g: v18 + cast-ahead + lean queries + retreat-dash gate > 60000) + one rule: standing in a bush with no
  enemy visible, ward our own tile. Found by the fight-block FunSearch (tune/fs, $5 spent in total), which warded a
  bush within 2 via filter(bushes(), ...) every turn; that broke the 100k cap, and contains(bushes(), position()) fixed it.
  League (required pool): 2s 1710 [1698-1725] vs v19 1670 [1657-1685]; vs hunter3 champion deaths 6.30 -> 4.44.
  Real cambc peak 93.9k.
- Required league pool for upload evidence: the live bot (now v20), opp-hunter3, opp-hunter2a/b/c, opp-icecream,
  opp-odyssey, opp-metab, opp-metadraft (I also include v18/v19 and tune5-campreset). Sim fuel target: peak <= 90k
  on big-world/ambush/starvation, both sides (funsearch/fuel_check.py; real cambc adds up to ~5k).
- The canonical base is deploy/v0 (merged into tune/runs 7c47221). The lockfix (tune/lockfix: locked_altars() =
  enemy locks only) is being merged there by the coordinator.
- Negative on v19/v20 (required pool or 2 x 400):
  - G's first winner (stun opener + heal + AoE) ~ v19; v19 + opener/heal neutral;
  - target choice (team target / carrier / VV-HoR-Vendetta first) noise;
  - pre-empting camp fights with an enemy within 5: loses;
  - other wards (anywhere, altar when carrying, camp goal, bush with enemies) all <= v20.
- Tools: funsearch/fight_metrics.py, fuel_check.py, hand_fight.py, vision.py, explore.py (drafts/switches),
  tools/league.py.

## Things only I know

- `--bot-seeds` with a single map replays the same two games; use per-game seeds for one-map
  stats.
- `fuel_turns` per-turn index doesn't line up reliably with `INTERP_TRACE` lines. Use
  `FUEL_TURN_DETAIL=ROUND:CHAMP` to inspect a specific turn.
- In this policy language `let` can't be rebound and there's no ternary. Use
  `floor(k / (x + 1))`-style arithmetic, and `within(R, tile)` with R = -1 for an empty set, to
  switch sets. Macros (`def`) inline and may contain `let`.
- Never use `pkill -f <script>`: it matches and kills the calling shell. Kill by PID.
- `runs/` is gitignored; logs there don't survive the container. Copy key numbers into commit
  messages or policy headers.
