# Cambridge Battlecode 2026a: strategy notes

Competition: https://2026a.battlecode.co.uk (handbook at /game/docs; full rules
export via the "Agents.md" page -> GameRules.md).

## CORE PRINCIPLE (do not lose this)

**Fuel is a rule, not a constraint.**

> Everything our submission can affect is an action; everything that limits
> it is a rule of the game. Nothing sits outside the game as a "constraint on
> the policy."

| Piece | Action | Rule |
| --- | --- | --- |
| Compute | spending fuel (instructions, SDK calls) | per-turn fuel budget, suspension on exhaustion |
| Champion select | each pick | uniqueness, simultaneous reveal, random pick on failure |
| Shared memory | each read/write | 8 bytes; turn order decides who sees a write when |
| Draft memory | one-shot broadcast from the full-map draft | 1,024 bytes, read-only after draft |
| Turn order | `set_priority` | team alternation, takes effect next round |
| Other | yield, resign, language choice, even crashing | their engine semantics |

Communication is not designed separately from play. What to write, how to
encode it and when are part of the strategy, optimised jointly with
everything else. All instances run the same program, so the codebook is
shared for free: the team is one strategy split across bodies, linked by an
8-byte channel plus implicit signals (positions, timing, observed behaviour).
"Design a protocol, then a policy" is the same mistake as "train a policy,
then fit it to fuel."

### End-to-end plan (current, supersedes details below where they differ)

- **Single output: one policy.** It covers the draft bot and every champion
  (branching on champion type). The memory scheme is not a separate output:
  writes are policy outputs, reads are policy inputs, and the meaning of the
  bytes is whatever the shared program makes it.
- **A policy is a program composed of building blocks**, e.g. `2x + y*z`
  with blocks as variables. Its configuration = which blocks, how they are
  combined (structure, conditions), and the constants. Blocks are compute
  moves with a fuel price at a fixed setting, e.g. "A* depth 2" (goal and
  scoring fixed; only tool + depth chosen), read/write shared bytes, read
  remaining fuel, visible units, fight outcome, lookahead depth k, move,
  attack/cast.
- **No hard fuel constraint on the policy.** The simulator applies the real
  rule (overrun = suspend, lose tempo); "read remaining fuel" is a block, so
  wasteful policies just lose games.
- **Generator: Deep Symbolic Regression style** (Petersen et al., ICLR 2021).
  An offline network writes policies token by token; invalid tokens are masked
  by the policy grammar; constants are tuned in an inner loop; reward = win
  rate in our simulator; risk-seeking policy gradient (train on the top few %
  of each batch). No model runs on the bots.
- **One policy for all maps, adapting at runtime.** Tournament maps are
  unseen, so no per-map policies offline. Terrain is not discovered: the
  draft sees the whole map and champions can read walls/altars/camps via
  `game_map`; only units are discovered through vision. Map-tailoring happens
  inside the policy: branch on map blocks, and/or the draft picks a
  sub-policy and writes the choice into draft memory.
- **Fuel prices must be reliable**: each block's price is a function of
  inputs (map size, unit count, depth), fitted by measuring against `cambc`.
- **Blocks are split to the smallest manageable unit**, so the policy pays
  only for what it uses. E.g. map reading = separate blocks: walls, holes,
  bushes, altars, spawn regions, camp groups, symmetry. All are readable from
  turn one (and in the draft); live camp state and enemies need vision.
- **Training opponents**: start against the starter bot and other reasonable
  hand-written bots, then self-play.
- **Simulator must compute fuel correctly** (it is a rule of the game).
- Iterate later: building-block set, policy grammar, fuel safety margin.

### Training pipeline (agreed)

1. **FunSearch phase** (Romera-Paredes et al., Nature 2023): a language model
   proposes policies in our grammar (prompted with the best so far), the
   simulator scores them, a database keeps the best. Model mix: mostly
   Claude Haiku 5.5 for volume, occasional Claude Opus 5.5 for bigger
   structural changes. Budget: $100 of Claude credits.
2. **Pre-train** the generator network on the FunSearch library.
3. **Deep Symbolic Regression phase**: risk-seeking policy gradient from there.

Shared by both phases: simulator, interpreter, fuel accounting, grammar
check, constant tuning (inner loop: best constants per structure; method
open). Opponents: starter bot and hand-written bots first, then self-play.
Grammar code: `policygen/` (branch `grammar/v0`).

### Status and findings (Oct 23)

- **Simulator** (`sim/`, branch `sim/engine`): exact vs cambc on all 40 pool maps;
  measured fuel prices (`docs/FUEL.md`). Host calls cost 1-30 fuel; guest code ~1
  fuel/instruction; host geometry is 30-200x cheaper than doing it in the bot; SDK
  wrappers can cost ~10x the raw import. Instances survive death; 256 MiB memory;
  source limit 5 MB zipped / 64 MB unzipped.
- **Interpreter** (`interp/`, branch `interp/v0`): runs `.policy` files in the
  simulator. Translated starter = builtin starter (53% over 400 games).
- **FunSearch** (`funsearch/`): built; needs `ANTHROPIC_API_KEY` in the
  environment to run with Claude. Two-stage scoring (16-game screens are too
  noisy; confirmed on 160 fresh games).
- **v1** (`policies/v1.policy`): 89% vs starter. Single changes measured over 400
  games: strength shards +0.22, abilities on camps +0.20, recall at 20% (not 35%)
  +0.11; delaying tribute for a bigger bag *hurts*. Champion choice barely matters
  at this level (Stellar worst).
- **Sprint 1**: winner Intercontinental Fish, runner-up Nyx; top-16 replays on
  branch `analysis/sprint1`, analysed by its own session.

### Training opponents (revised Oct 23, after the first ladder games)

- First ranked games: fs-1 went 2-13 against mid-table teams (team "Master",
  437th, ~1,465), although it beats everything in our sim pool. Hand-written
  imitations of real teams are not faithful opponents.
- Decision: **train against ourselves.** FunSearch scores against a self-play
  league (current best plus previous validated bests; starter only as a sanity
  floor). A new best must beat the current best head to head and not regress
  against older league members.
- **Real matches are a source of ideas, not opponents to copy:** policy styles,
  tactics and missing blocks extracted from replays go into the prompt and the
  language. Recreating other teams' bots is out of scope.

- **Ladder versions:** 1 = fs-1 (2-13). 2 = v3 (Oct 23; `deploy/v0` a3d1f0b,
  `dist/deploy-v3.zip` sha256 d14dc314...): fs-1 plus retreat when hurt and in
  danger, hold only capturable spawns, skip monoliths and golems. Sim: 87% vs v2,
  81.5% vs fs-1; real cambc: 66/80 vs fs-1.
  v3 went 13-22 in its first 35 games; losses traced to altar locks freezing
  our carriers, fights lost at even numbers, and small bags (`analysis/sprint1`,
  `docs/LADDER_LOSSES_V3.md`). 3 = v4 (Oct 23; `deploy/v0` c06711d, sha256
  8381086a...): v3 + tribute through locked altars, prefer altars out of monolith
  reach. Real cambc: 39/80 vs v3, 71/80 vs locker (v3 66/80).
  4 = v5d (Oct 23; `deploy/v0` 6ed2435, sha256 480bd75d...): v4 + focus fire on
  the weakest enemy in range + fixed draft order (Vesper Vale, Tavi, Marcella,
  Stellar, Ren). Real cambc 51/80 vs v4. The draft is a large lever: the bot's
  fixed RNG seeds had been drafting one composition every game (see
  `docs/ENGINE_FINDINGS.md`, "Match seeding", on `deploy/v0`).
  5 = v5d rebuilt with the policy pre-parsed (`deploy/v0` ee76a6e; same play,
  first turn <= 136k of 200k). 6 = v5d-fs2 (`deploy/v0` c902789, sha256
  97f7d5f6...): v5d + fs-2's Treasure/Jungle shards and tribute at 10+ gems,
  the first ladder version with FunSearch-found changes (hybrid line). Sim
  61.3% vs v5d; real cambc 50/80 vs v5d.
  7 = v7 (`deploy/v0` b2eef11, sha256 2bca208d...): v5d-fs2 + idle fix (on a
  dead camp of an uncleared group, walk to a living camp; `docs/FARM_DIAGNOSIS.md`
  on `deploy/v0`). Real cambc 47/80 vs v5d-fs2, exactly as `interp_eval
  --bot-seeds` predicted. v6 (freeze fixes) was not uploaded: 38/80 in cambc
  despite 54.5% in the per-game-seed sim. Use `--bot-seeds` (all 40 maps x 2
  sides) as the pre-build check for the ladder bar.
  8 = v7-zerogem (`deploy/v0` 8913cb8, sha256 c9826988...): v7 + fixes for the
  three maps where our mirror scored 0 gems (`docs/ZERO_GEM_MAPS.md` on
  `deploy/v0`). Real cambc 43/80 vs v7: wins both sides on 00reverse-spiral,
  01elk-arena, 01shortcut, loses both sides on none (bar for concentrated
  fixes: >= 52% and no map lost on both sides). Next builds include the
  fog-camps pathing fix (interp/v0 6297d62; neutral head to head, +3-5% gems).
  9 = v7zg-cast (`deploy/v0` af6ef1b, sha256 e869299c...): v7-zerogem + the
  hybrid line's ability-type-aware casting (shield/heal on self, dash saved
  for travel/escape) + fog-camps pathing. Real cambc 49/80 vs live
  v7-zerogem; 76/80 vs locker; 79/80 vs starter. Dash turns peak at ~100k fuel
  on 100x100 maps (none over; an overrun only suspends one turn); the bot
  session is cutting that cost without changing play.
  10 = v7zg-cast rebuilt (`deploy/v0` cfcbbbb): same play, peak fuel 88k.
  11 = tune-1 (`deploy/v0` 3730b2e, sha256 b09cd179...): v7zg-cast with the tune
  line's draft vendetta, vesper_vale, tavi, ryth, ren (frontliner first; 233
  orders screened, top 8 confirmed on fresh seeds). Real cambc 49/80 vs v10;
  sim 58.9% on 800 fresh games. Peak fuel ~96k on 01big-world.
  12 = tune-1 v2 (`deploy/v0` 3c05bbf): + dash never crosses the enemy spawn
  (cambc rejects it); 42/80 vs tune-1, a correctness fix. 13 = tune-2
  (`deploy/v0` fd02a8f, sha256 8aece2da...): bag >= 25 and tribute-when-hurt at
  0.3 (each alone was noise; together +11). Real cambc 45/80 vs tune-1 v2.
  Hits the 100k cap on 4 of 240 test turns (01big-world as A, long tribute
  trips); the fix goes in the policy (a fuel_remaining() guard on optional
  searches, tuned by the tune line), not in the bot.
  14 = tune-3 (`deploy/v0` 0812ad5): tune-2 + camp-goal dash only if
  fuel_remaining() > 55000. **But in the cambc bot fuel_remaining() returned
  2^40 until `deploy/v0` 756d052** (an inline 'unlimited' branch the bot always
  took), so version 14 plays exactly like tune-2, and no earlier ladder policy
  could ever read its real fuel. The core principle's main self-aware block was
  inert on the ladder; the sim applied it. Fixed; a rebuilt tune-3 follows.
  Lesson: every block that reads game/host state needs a cambc-vs-sim check.
  15 = tune-3 v2 (`deploy/v0` 61a88d6): tune-3 with fuel_remaining() fixed. 16 = tune-5 (`deploy/v0`
  aec1e76, sha256 cbd8405c...; live Oct 24 03:44 UTC): camp-goal dash from > 2, jungle shards rest/2. Real cambc
  46/80 vs tune-3 v2, but 11-19 ranked and 0-50 in unranked games vs ladder #1-#9 and vc?: it doesn't fight back
  (deaths 17.8 vs 1.6, kills 0.3 vs 12.9 per game; `docs/TOP_TEAMS*.md` on analysis/sprint1). Sim and deployed
  bot were both verified exact in fights, so the gap is behaviour.
  17 = tune5-campreset (`deploy/v0` 0f49154, sha256 433aa2bd...; submitted Oct 24 ~07:08 UTC, first upload under
  the league bar): tune-5 casting attack-reset abilities after the first basic attack and attacking again, vs
  champions and camps (tune-5 cast them at the target first, where they fail). Real cambc 65/80 vs tune-5,
  kills ~7.8 vs ~4.1; league 1729 [1715-1743] vs tune-5 1603 [1591-1616] (14-bot pool with hunters).
  Still 0-50 in the same unranked groups vs the top 9 + vc? (tune-5 was 0-50 too).
  18 = tune-r-all-v2 (`deploy/v0` c0024c8, sha256 46ce4da6...; ~07:27 UTC): campreset + monolith-group and
  starvation fixes (T240 gated at fuel > 65000) + no recall with an enemy within 8. Tune line's league 1725
  [1712-1737] vs campreset 1672 [1659-1683]; real cambc 40/80 vs campreset (information only), 0 capped turns.
  19 = rall2-ca4-lean-g (`deploy/v0` 7ef15b2, sha256 a77fa4e3...; ~08:26 UTC): v18 + hybrid's cast-ahead (cheap
  version) + low-health retreat dashes gated at fuel_remaining() > 60000 (the bot session traced the 100k caps of the
  ungated versions to a long retreat on 01big-world; v18 has the same ungated retreat). League (hybrid, lean):
  1711 [1694-1725] vs v18 1661; real cambc 51/80 vs v18, kills 8.2 vs 6.9, 0 capped turns, peak 89.8k.
  v18 ranked: 10-10 in its first 20.
  v19: 4-46 in the unranked top-team groups (first wins: vc? 3-2, prism 1-4); ~51-39 ranked.
  20 = tune-fight-2s (`deploy/v0` 6d50156, sha256 ec50970b...; ~11:35 UTC): v19 + an FS-found rule: with no enemy
  visible and standing in a bush, ward our own tile. Tune line's league 1710 [1698-1725] vs v19 1670 (re-run 1691);
  real cambc 45/80 vs v19, 0 capped turns, peak 93.9k; sim-vs-cambc agreement 60/80 (baseline v19 vs v18: 58/80),
  so the allied-ward move rule the sim doesn't model shows no effect.
  v20: 0-50 vs the top-team groups (vc?, Mite, willow had updated their bots; prism's 00quadrants win flipped at our
  first ward); 15-5 in its first 20 ranked. Sim: the ward doesn't cost gems vs hunters/stand-ins.
  21 = tune-v20-L1c (`deploy/v0` d9d2897, sha256 c8ea639c...; ~12:40 UTC): v20 + one altar lock per team (one buy
  claimed in shared byte 7 bit 1, placed bit 0, placement gated at fuel > 60000). League 1716 [1703-1731] vs v20
  1676 (v19-L1c 1690); real cambc 44/80 vs v20, 0 capped turns, peak 93.0k, 1 buy/team/game, placed 79/80.
  v21: 1-49 vs the top groups, 15-35 vs the +100 band (GAP_LIST.md), ~30-35 ranked.
  22 = v21b (`deploy/v0` ee85727, sha256 d86fbda6...; ~15:05 UTC): v21's policy unchanged on bot code with the
  dead-camp fix (cambc's camp() reports dead camps as not-in-vision, so group_threat/group_hp counted seen-dead
  camps as alive in the deployed bot; policies were tuned on seen-dead = 0; deploy/v0 59d9e3a). Bug-fix bar (no
  regression): real cambc 40/80 vs v21, 0 caps; sim vs v7zg-cast gems/capture 11.03 vs 10.93, tributes 27.4 vs 27.1.
  v22: 17-33 on the same 50 band games as v21 (15-35): the fix is neutral at that tier.
  23 = style-gconv1 (`deploy/v0` 84bc6a6, sha256 ade608f2...; ~16:10 UTC): v21's policy + sensor-driven banking found
  by the style line's FunSearch (threat_eta, altar_eta). INFORMATIONAL upload approved by Cham: league not required;
  sim vs v21 51.4%, conversion 0.946 vs 0.896, tributes 38 vs 23, gems lost 51 vs 64; real cambc 46/80 vs v22, 0 caps
  (heavier: 188 turns > 80k, peak 96.5k). Judged on the same 50 band groups; revert to v22 if not better.
  Result: 14-36 on the band (v22 17-33). The banking worked (tributes 18 -> 28, gems lost on death 164 -> 89,
  conversion 77% -> 82%) but cost farming (captured -108 per game, median bag 30 -> 18): net submitted 626 -> 578.
  24 = revert to v22's ZIP (d86fbda6, ~16:50 UTC). Lesson: bank early only when a threat is near; a small-bag
  bank rule costs more capture time than it saves.
  25 = genome B318 (genome line, genome/v0 2013533, B318.genome sha256 00e1711a..., bundle genome-b318.zip
  sha256 548bb21d...; submitted by the genome line's intel session ~20:40 UTC with Cham's go). Gate vs live v22:
  sim 0.589 over 800, real cambc 46/80, 0 crashes; runs capped turns by design (Cham accepted turns for compute).
  Revert target: v22's ZIP (d86fbda6). FunSearch candidate style-gsub2-11k33 (cleared the main3r bar) not uploaded.
  First 50 unranked vs the band: 18-32 (v24 on the same teams/maps 2-8, B318 1-9); loss causes yield 50%,
  fights 44%; ~9 fuel-out turns per game, same in wins and losses.
  26 = genome B792 (genome line Arena B, genome/v0 b5d606b, genome sha256 fa178e51..., bundle sha256 f03df323...;
  submitted by the genome line's intel session 21:24:48 UTC). Gate vs v25: sim 47/80, real cambc 43/80, 0 crashes;
  11 first turns at the 200k cap (B318 110), 279 capped normal turns (B318 692). Revert target: v25 (548bb21d).
  B792 ranked 51-59 after 110 (v24 67-53); same lock-stall as v24 (01broken_curve 0-1015); genome runtime had
  no lock-attack action (being added by the genome line).
  27 = genome A61188 (genome line Arena A, genome/v0 0372259, genome sha256 9abfbc94..., bundle sha256
  8f44d04a...; submitted 01:54:54 UTC Oct 25 under Cham's "upload first, validate later" per the genome lead).
  Pre-upload: real cambc smoke vs B792 3/3, sim vs B792 49/80. Revert target: v26 (B792, f03df323).
  A61188 ranked 30-20 after 50 (60%); first version to bank on 01shortcut (r~215) but 16-22 monolith deaths there.
  28 = genome a61188-mono (A61188 + Arena B's farmable-camps edit for monolith deaths; genome/v0 568cbf5, genome
  sha256 54e1275a..., bundle sha256 8a921761...; submitted 03:43:47 UTC Oct 25). Smoke vs A61188: great-wall 2-0
  (monolith deaths ~halved), shortcut 1-1, 0 crashes. Revert target: v27 (A61188, 8f44d04a).
  v28 vs A61188, 50 paired unranked: monolith deaths 1.86 -> 0.58/game, 13-37 -> 18-32; ranked 14-11 early.
  A61188 final ranked 33-22.
  29 = genome v28-emblem (v28 + Treasure shards concentrated on one carrier until its emblem; genome/v0 97194bf,
  genome sha256 781ad53e..., bundle sha256 61743fda...; submitted 05:11:34 UTC Oct 25). Real vs v28 45/80,
  0 crashes. Revert target: v28 (a61188-mono, 8a921761).
  v28 final ranked 25-20; v29 unranked batch 20-30.
  30 = genome A81582-ringheal (Arena A's A81582 + ring and heal bug fixes; genome/v0 69db2f6, genome sha256
  9620bbfb..., bundle sha256 90450da2...; submitted 06:39:47 UTC Oct 25). Real vs v29 57/80 and 55/80, 0 crashes;
  450 capped turns vs v29's 301 in that h2h. Revert target: v29 (61743fda).
  v29 final ranked 18-22. v30 early: ranked 10-5, but monolith deaths back to 2.3-3.5/game (lacked v28's edit).
  31 = genome A81582-rh-mono-all (v30 + v28's monolith fix + contest rule + gem-first after 6 buys; genome/v0
  adeb971, genome sha256 f54246b1..., bundle sha256 e4932580...; submitted 07:16:11 UTC Oct 25). Real 51/80 vs
  v30, 62/80 vs v29, 0 crashes. Revert target: v30 (90450da2).
  v31 band batch 8: 27-23 vs v30's 21-29 on the same games (p ~0.03): the first winning band batch of any version.
  32 = genome B1873 (Arena B relay: B-line + monolith fix + ring/heal + gem-first after 6 buys + kill-shot priority
  + boss-battle altar exemption; genome/v0 0483238, genome sha256 20a329ce..., bundle sha256 52a3fb56...;
  submitted 07:50:23 UTC Oct 25). Real vs v31 47/80, 0 crashes. Revert target: v31 (e4932580).
  v32 band batch 9: 31-19 (v31 27-23, v30 21-29 on the same games), gems +87 +/- 40 vs v31; gain is economy.
  33 = genome B1873-bossbush (v32 + no bush move bonus on the boss-battle altar layout; identical elsewhere;
  genome/v0 1842b9c, genome sha256 7ff741cb..., bundle sha256 37e7be1a...; submitted 08:36:16 UTC Oct 25).
  Real vs v32: boss-battle 2-0, other maps mirrored. Revert target: v32 (52a3fb56).
  v33: band batch 32-18 (48/50 games identical to v32; its boss-battle gate fired on starvation instead);
  ranked 78-67 by 13:30 UTC, drifting down; losses mostly economy, starvation 0-5, elk_arena 0-1008 x3.
  34 = genome v33-cash3-ahead4 (v33 with cast-ahead range 5 -> 4, cash-out threshold 5 -> 3 gems; genome/v0
  c9dddf3, genome sha256 6ca9e9e6..., bundle sha256 9842ac5c...; submitted 14:18:21 UTC Oct 25). Real vs v33
  44/80 (three runs), 0 crashes, fewer capped turns. Revert target: v33 (37e7be1a).
  v34 band batch 11: 28-22 vs v33's 32-18 on the same games, gems -41.
  35 = revert to v33's bundle (37e7be1a; genome line, ~14:54 UTC Oct 25).
  (v34 paired vs v33: gems -33, 4 L->W / 8 W->L; gems lost on death 105 vs 80; cash-at-3 put carriers in fights.)
  36 = genome v33-ahead4 (v34 without the cash3 edit; live 14:56:30 UTC Oct 25). Real vs v33 44/80, 0 crashes.
  Revert target: v33 (37e7be1a).
  v36 band batch 12: 31-19 vs v33's 32-18, gems -40.
  37 = v33's bundle again (37e7be1a, 15:28:27 UTC Oct 25). Genome line's new bar: constant-only tweaks need >=46/80
  real vs live. Next lever: champion fights (deaths to champions 6/game in wins vs 16 in losses).
  38 = genome A93635-v33port (A-9's A93635 with v33's fixes grafted; bundle sha256 d54619f2...; 02:06:53 UTC
  Oct 30). Real cambc 47/80 vs v33, 0 crashes; sim 46/80, anchors clean; solo-farm worse on 01boss-battle
  (sim tribute lock) and 00contest. Validation: band batch 13. Revert target: v33 (37e7be1a).
  39 = v39a (04:11 UTC Oct 30): v38 plus a one-gene fix for a freeze on 00quarry (camp spawn hidden in a bush
  under engine 2.0.0 vision). 72/140 vs v38 on cambc 4.0.0. Ladder engine is 2.0.0 (cambc 4.0.0, 70 maps) since
  Oct 25 23:42 UTC; genome sim ported and exact vs 4.0.0 (genome/v0 671ac45b). New maps weak: 5-15 in b14.
  v39 b15: 31-29 (v38 30-30). 40 = exploit-6 x6-83 (06:08 UTC Oct 30, bundle 7317ef88...): contests gem groups
  an enemy farms, healthiest fighter first; holds contested captures. 79/140 vs v39 on 4.0.0 (old maps 46/80,
  new 33/60), 0 crashes. Validation: b16. Revert target v39 (97492ba3...). Queued next: v40m (79/140 vs v40).
  v40 b16: 31-29, same as v39 on the same games (kept). 41 = v40m (06:33 UTC Oct 30, bundle 7cd1e540...): v40
  with cheaper monolith-group lookup (turn-1 fuel cap maps 14 -> 4); 79/140 vs v40. Validation: b17. Revert target v40.
  v41 b17: 28-32 (v40 31-29). 42 = v40's bundle again (7317ef88...). Lesson: local self-play edges (79/140) twice
  failed to show on the band; the ladder band now decides. Genome 2.0.0 sim now unbiased vs real (mean sim-real +0.6).
  43 = exploit-8 x8-140 (09:57 UTC Oct 30, bundle ed994fd9...; multi-opponent fitness): 81/140 vs v40 (old 48,
  new 33). Validation: b18 paired with b18base (v40 re-run). Known bug: solo stall on 00quarry side A (1699 rounds
  vs v40's 861); fix in progress. Revert target v40 (7317ef88...).
  v43 b18: 30-30 vs v40's same-hour re-run 33-27. 44 = v40's bundle again (10:32 UTC Oct 30). Candidates now go
  through short ladder screens (30 games each) before an upload.
  45-51 = screens (A11501, A11696, A11599, A11791, v43-fix3, x6-61, x7-125): none beat v40 on the same games
  (v40 13-17; best x6-61 level, x7-125 7-23). 52 = v40 again (drift control 13-17). Fight-seekers die +1.2 to +3.1
  more per game vs ladder teams; no local metric ranks the screens. Next lever: ladder-like local opponents.
  53-55: more screens and v40 controls (v40 live as v55). 56 = d-out2b (v40 + retreat to spawn when outnumbered by
  2+ enemy champions within 6; idea from the Fish low-HP study). Screen 12-18 vs v40's 10-20; band b19 31-29 vs
  v40's same-hour 30-30, fewer gems lost on death: adopted.
- **Arena (Oct 23):** Jerry's private arena, v7zg-cast vs house bot metab-v3:
  13-7 (Elo ~1600); lost both sides of contest (monoliths) and quadrants.
- **Search lines (Oct 23):** hybrid FunSearch (builds on the best from any
  source), pure FunSearch (only its own outputs, from fs-1), tuning + draft (no
  LLM), style FunSearch (lockdown / team fights / late monolith). Each runs in
  its own session; all share one opponent pool and promotion rule.

### Deployment shape (agreed so far)

- No model runs on the bots. The network lives offline and outputs
  **configurations** (data, not code). The bot is a fixed interpreter of a
  configuration.
- Configuration expressiveness is a spectrum (pure numbers ... structure as
  data). Decisions: weighted rules (weights change effective rule order,
  so structure stays differentiable).
- **Storing/reading must be configured, not hand-designed**, so the bot can
  reach the optimal memory use. Bot = memory' = f(memory, obs),
  action = g(memory, obs), with f set by the configuration: what to store, how
  to encode it, when to write, what to read. Matters most for the 8 shared
  bytes and the 1,024 draft bytes.
- **Compute is configured too.** Configuration = compute schedule + weights +
  codebooks. The schedule is an ordered list of compute steps (features at a
  chosen cost/precision tier, action scoring, lookahead), each with a cheap
  gate and an early-stop margin; plus cache/recompute policy and deliberate
  multi-turn computation. The fixed interpreter only walks the schedule and
  must stay negligibly cheap: any real compute left in the fixed part is
  compute outside the game.
- **Building blocks**: the interpreter ships a library of parameterised
  algorithms; the configuration chooses which run, when and with what
  settings (each run is a priced step in the compute schedule). Candidates:
  search/lookahead (depth, beam, move ordering, leaf eval, opponent model,
  fuel cap, anytime; depth 0 = plain scoring), pathfinding (engine distance
  fields or cheap estimates, weighted tile costs), fight calculator
  (closed-form, deterministic), belief tracker (where unseen enemies can be),
  timers (camp respawns, enemy cooldowns/deaths), task assignment via
  shared-memory claims, codebooks, draft map analysis. Start with search,
  pathfinding, fight calculator, belief tracker. The library is now the
  expressiveness ceiling.
- **Why the compute space is manageable.** Raw space = every program within
  fuel (unbounded). But a computation matters only through its outputs (board
  actions, memory writes, whether it overruns). Programs with the same outputs
  are the same move: hash-mining within budget == doing nothing (unused fuel
  doesn't carry over); over budget == skipping a turn. So we choose a
  *decision function* (info -> outputs); compute only decides which decision
  functions are reachable. Per turn, fuel is a knapsack: spend it on
  computations whose information changes decisions (rational metareasoning,
  Russell & Wefald). Keep only the cheapest computation at each precision
  level for each decision-relevant quantity. The block library is this
  pruning. Grow it from evidence: run an unlimited-fuel version of the bot in our
  simulator, find costly decision differences, add the block that closes the
  gap.
- Train encodings DIAL-style (Foerster et al. 2016): relax messages to
  continuous values through a noisy channel during training, discretise at
  execution. The learned encoding ships as lookup tables.

**Compute is part of the action space.**

The rules describe a game of moves. What we actually submit is a program
running under a per-turn fuel budget, so the real game is the *expanded* game:

- State = board state + every bot instance's machine state (its persistent
  memory and where it is in its program) + 8-byte team shared memory +
  1,024-byte draft memory.
- The atomic actions are instructions. Game actions are just the side effects
  of certain SDK calls. API queries (vision, masks, distance fields) cost fuel,
  so what a champion *knows* is also something it chooses to spend on.
- Running out of fuel suspends the bot and resumes it next round, so thinking
  trades directly against tempo (lost turns). Shared-memory writes are actions.
  The draft is the one big-compute, full-information action.

Analogy: a knight moving two forward and one sideways is part of chess's
action space; nobody treats the L-shape as an outside constraint on the policy.
The fuel limit is the same kind of rule, just with more nuance. An action is a
pair (x compute, x board action), and the budget is a legality rule on that
pair, exactly like the knight's move pattern.

Consequence: if we model the expanded game correctly and optimise in it, the
optimum is *by construction* a program that runs within budget. There is no
separate "train an unrestricted policy, then compress/distil it to fit fuel"
step. Any such fitting layer is a sign the game model is incomplete.

Requirements for this to hold:
- Fuel costs in our model must match the real engine exactly (measure them
  against the `cambc` binary).
- Bot memory must be part of the state.
- Code/module size must be a constraint too: fuel alone does not stop the
  optimiser from producing a huge zero-fuel lookup table. Submission size limit
  is undocumented; still to be determined.

## Plan so far

- Policy is trained/optimised offline and hardcoded into the bot, with a little
  room for runtime computation inside the policy. No network is loaded onto the
  champion.
- Gradient ascent is over continuous parameters of a stochastic policy
  (expected score is smooth in action probabilities; discreteness of the game
  itself is not the obstacle). Two-player, so the target is an equilibrium.
- Write our own fast simulator in a low-level language. The `cambc` engine
  (closed ~99 MB binary, pip package `cambc`) is deterministic and serves as
  the reference: differential-test our simulator against it round by round.

## Facts that constrain the design

- One bot instance per champion (Cassi & Issac = two), plus a draft instance.
  Fuel is per instance per turn: 100k (C++/Rust), 5x OCaml, 25x Python; unused
  fuel does not carry over; draft's first turn 10x, first play turn 2x.
- Instances share only 8 bytes (read/write all match) and 1,024 bytes of draft
  memory (read-only after draft). Vision is not shared.
- No randomness in play; the only randomness is auto-picks for a failed draft.
- `debug_block` is fuel-free only in local debug builds; measure fuel with
  `--release`.
- Sprint tournaments use only unseen maps, so per-map hardcoding is out:
  map-specific planning belongs in the draft.
- Rule details still ambiguous (resolve against the binary): monster target
  tie-breaks, damage modifier ordering, dash path legality, vision edge cases.
