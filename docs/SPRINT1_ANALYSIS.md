# How the top teams play: Sprint 1 and the current ladder

Source: all 225 games of Sprint 1's round of 16 to the final (`data/sprint1/`), replayed
through the official engine to get full state at every step (`analysis/`, see its
README). Teams were matched to replay sides by their per-map draft fingerprints; the
assignment reproduces every series score in the bracket. Full tables:
`analysis/report.md`; regenerate with `analysis/run_all.sh` + `analysis/analyse.py`.

## Read this first: Sprint 1 ran an older ruleset

Every Sprint 1 replay declares engine **v0_0_3** (the visualiser calls its catalogue
"original"). cambc 3.0.5, `docs/GameRules.md` and our simulator are **v1_0_3** ("balance").
Diff from the engines themselves (`analysis/designs.js`, `analysis/rewards.js`):

| | Sprint 1 (v0_0_3) | now (v1_0_3) |
|---|---|---|
| Wolf camp reward | 22 gems, 90 gold | 4 gems, 40 gold |
| Elk | 36 gems, 160 gold | 15 gems, 90 gold |
| Gold cluster | 35 gold, 500 hp | 20 gold, 120 hp |
| Elk x3 group | 216 gems, 960 gold | 90 gems, 540 gold |
| Monolith x2 | 400 gems, 600 gold | 400 gems, 600 gold (unchanged) |
| Golems | none | 5000 hp, 36 gems |
| Kill gold | 50 | 100 |
| Ward recharge | 1 turn | 10 turns |
| Altar lock hits | 3 | 5 |
| Stellar | focus 100 (+10/shard), hp 750 | focus 70 (+7), hp 650 |
| Ren stun | 1.25 x focus, str 40 | 0.75 x focus, str 35 |
| Tavi stun | 2.2 x focus, hp 750, str 35 | 1.4 x focus, hp 900, str 45 |
| Cassi / Issac | hp 700, growth higher | hp 600, growth lower |
| Vesper Vale | hp 900, str 45 | hp 1000, str 55 |
| Vendetta | hp 800 | hp 1000, str growth 6 |
| Heart of Ruin | AoE + stun kit | shield + stunning dash (reworked) |

Consequences: Sprint 1's gem economy came from wolves and elks (gems per capture ~5x
today's for a wolf); today camp gems are scarce, so monoliths, kills (gems stolen, and
2x kill gold) and the gold tiebreak weigh relatively more. The meta champions
(Stellar, Ren, Tavi, Cassi & Issac) were all nerfed. **Behavioural patterns transfer
better than numbers or drafts.** Checked in our simulator: imitations of the top four
teams' policies (below) all lose to our `v1.policy` (27-37% win rate).

## Current ladder (v1_0_3): 285 ranked games among the top 12, 23 Oct 2026

Because of the ruleset change, the current ladder is the better guide. Data:
`data/ladder-2026-10-23/` (sides and results straight from platform metadata, all 285
engine results match the platform's); tables in `analysis/ladder_report.md`. Top 4 at fetch
time: prism best girl, Intercontinental Fish, policy wonk, procless.

**Drafts: a new meta.** Vesper Vale 92% pick rate, Heart of Ruin 78% (most first picks, 171),
Marcella 76% (166 first picks), Vendetta 58%, Ryth 55%, Prism 26% (99 first picks), Willow
22%, Tavi 15%, Cassi & Issac 11%, Varg 6%, Stellar 3%, Ren 2%. The Sprint 1 core has gone.
- prism best girl: Prism > Vesper > Marcella/HoR > Vendetta (> Ryth).
- Intercontinental Fish: Vesper > Vendetta > HoR > C&I > Ryth (26 of 50).
- policy wonk (32-13, the best record of the top 4): Marcella > Vesper > Tavi > Willow > HoR.
- procless: HoR > Vesper > Ryth > Marcella > Vendetta (32 of 45).

**Games are long, and comebacks are common.** Median game length is 1,117 rounds (Sprint 1:
~650). Median tributed gems for winners are 44 at round 200, 160 at 400, 335 at 600. The leader
at round 200 wins only 57% (71% in Sprint 1); at round 400, 66%.

**Economy.**
- Gold first: double gold clusters are the most common first capture (295 of the first three
  captures per game; next gold+wolf 165, elk+gem+gold 99).
- Gems come from groups with elks and gem clusters (elk+gem+gold alone is 7.6% of all gems).
- Monoliths are 7% of gems but decisive. On maps with monoliths, the side that captured more
  of them won 45 of 56 games (80%). Median capture round: 1,040, so it is a late-game play.
  prism best girl captured the most (31 in 50 games).
- Gold earned per game is ~6-8.4k (Sprint 1: ~4k), and nearly all of it is spent.
- Tribute: 59% of the top 4's tributes come after one capture, 20% after two, 18% after three
  or more. Other teams: 70% after one. Median bag: top 4 30 gems, others 22. Banking a little
  more than one camp is now normal for the best teams (policy wonk: only 50% after one capture).
  Gem captures are small now (a wolf gives 4).
- Vesper Vale receives 30% of the top teams' capture rewards and makes 31% of their tributes.

**Items: Bruiser and Treasure, not Power.** Vesper: Bruiser Strength 33%, Power Strength 33%.
Marcella: Bruiser Focus/Health/Strength 29/28/20%. HoR: Bruiser Health/Focus 25/25%, Jungle
Focus 11%. Vendetta: Bruiser Strength 39%. Openers: procless buys **Treasure Health first on
every champion**, then Jungle; policy wonk opens Treasure then Jungle; prism best girl opens
Power/Durability Health. Teleport crystals are common (Noobot 8.4 used per game, prism best girl 5.4).

**Fighting.** 11-20% of the top teams' basic attacks hit champions. Winners average 10.0 kills
and 5.0 deaths per game; losers 4.2 and 10.9. Predictors over 280 decided games: more gems
captured 92%, more gold 86%, more kills 79%, fewer deaths 76%, more attacks on champions 65%;
wards 53%, altar locks 45%, teleports 48% (no signal).

**Abilities.** Same habits as Sprint 1, at higher volume (games are longer):
- Dashes as movement: HoR 88, Vendetta 80, Vesper 71, Issac 71 per game, all at ground tiles.
- Resets and shields on cooldown: Varg shield 89 per game, HoR shield 54, Vesper reset 52.
- Damage spells on camps 68-83% of the time (Marcella slot 1: camp 68%; Stellar, Prism, Cassi
  75-83%).
- Prism and Stellar AoE aimed at empty ground 67% of the time.

**Recall.** The top 4's median health when starting a recall is 41-73% (Fish 41%, procless
45%, prism best girl 46%, policy wonk 73%); 12-23% of their recalls start at <=25% health.
11-33% start at >=90% health, usually carrying gems (55-66%) or ~100 gold: going home to shop.
Four teams (:3, Pantheon, Noobot, NEETCoders) re-issue and cancel recall thousands of times
per game, a cheap bot idiom. (Health fractions use current max health, including Health shards.)

### Follow-up: how top teams take monoliths, and how Heart of Ruin plays

`analysis/ladder_followup.py`, output in `analysis/ladder_followup.md`. An attempt is a run of
champion damage on one monolith with no gap over 20 rounds and at least 2,000 damage.
Success means the same team captures it within 30 rounds of the last hit.

**Monoliths** (top 4: 183 attempts, 57 captured, 31%; all 12 teams: 316 and 107, 34%):
- **Never solo.** Top-4 success by attackers: 1: 0% (of 50), 2: 29%, 3: 49%, 4: 69%. Captured
  attempts had 2-4 attackers (median 3); failed attempts are mostly 1-2 champions.
- **Late.** Success rises with the start round: 25% before round 1,000, 37% at 1,000-1,400,
  46% after 1,400. Median start of a captured attempt is round 1,010, and no top-4 attempt
  started before 400.
- **Not gated on items or health.** Shards per attacker were *lower* in successes (11.5)
  than in failures (15.0), and the lowest attacker health at the start was 80% vs 96%. The
  number of champions is what matters.
- **It takes ~27 rounds** and ~20k damage (the monolith's HP). Deaths are rare (0.09 per
  captured attempt), and about 2 recalls per attempt (attackers rotate out and back).
- **Contested about half the time.** Enemies hit the attackers in 42% of captured attempts
  and 25% of failed ones. Fights at monoliths are normal, not a reason to abort.
- Failed attempts stop early (median 17 rounds, ~5k damage): they are mostly lone champions
  poking and leaving.
- The team that captured a monolith won 77% of those games.
- Champions in successful takes: Vesper Vale, Marcella, Vendetta, Heart of Ruin, then Tavi,
  Ryth, Prism.

Rules a policy could follow:
1. Go for a monolith only when >= 3 allies can commit (shared-memory claim); 2 at most as a
   fallback. Never alone.
2. Start after round ~1,000 (or once camps nearby are on cooldown). Don't wait for full health
   or more items.
3. Commit for ~30 rounds. Recall individually at low health and come back; don't abort the
   attempt because enemies show up.
4. Abandon when fewer than 2 attackers remain.

**Heart of Ruin** (top 4, ~50 games):
- **Does not fight at low health**, despite the low-health damage passive: median health 78%
  when attacking champions, 88% when attacking camps; only 5% of its attacks on champions
  come below 30% health (16% below 50%).
- **Recalls around 43% health** (28% of its recalls below 30%, 59% below 50%), earlier than our
  20% rule. Lower-ranked teams spam recall at full health.
- **Shield on cooldown in combat** (median health 87% when cast), not saved for emergencies.
- **Dash is mostly movement**: 61% of dashes hit nothing, 32% land on camps (stunning them),
  7% hit enemy champions.
- Attacks: 82% on camps, 18% on champions.

Rules: treat HoR like the other fighters; shield whenever a target is in range; dash toward
the goal, or onto a camp group to stun it; recall at ~40-45% health. Its passive is not
something top teams play around.

**Policies.** `policies/ladder_meta.policy`, `prism_best_girl.policy`, `policy_wonk.policy`,
`procless.policy` (Heart of Ruin cannot be drafted in our grammar yet). 200 games each in our
simulator:

| policy | vs starter | vs v1 | vs fish (Sprint 1 imitation) |
|---|---|---|---|
| ladder_meta | 0.88 | 0.41 | 0.65 |
| prism_best_girl | 0.84 | 0.35 | 0.71 |
| policy_wonk | 0.92 | 0.48 | 0.68 |
| procless | 0.90 | 0.48 | 0.75 |

These are at parity with v1 (±0.035 standard error), so they are better training opponents
than the Sprint 1 imitations.

## Sprint 1 findings

### 1. Drafts: a two-champion core, then Ren/Varg/Ryth

Across 420 team-games (the locked map in section 6 excluded here and below):

| champion | pick rate | first picks | mean slot | win rate when opponent lacked it |
|---|---|---|---|---|
| Stellar | 99% | 154 | 1.9 | 33% (6 games) |
| Cassi & Issac | 96% | 110 | 2.4 | 41% (17) |
| Ren | 79% | 68 | 3.1 | 66% (64) |
| Varg | 63% | 86 | 3.2 | 53% (92) |
| Ryth | 51% | 0 | 3.7 | 53% (109) |
| Tavi | 34% | 0 | 3.5 | 50% (105) |
| Vendetta | 8% | 0 | 2.4 | 31% (35) |
| Prism | 8% | 2 | 2.7 | 50% (30) |
| Vesper Vale | 3% | 0 | 4.6 | 14% (14) |
| Willow | 2% | 0 | 5.0 | 12% (8) |

Marcella and Heart of Ruin were never picked. Raw per-champion win rates are ~50%
because most games are near-mirrors; the informative column is "opponent lacked it":
Ren was the one pick that clearly paid (66%), Vendetta/Vesper/Willow lost.

Top-4 drafts (order as picked; maps had 3, 4 or 5 champions per team):
- Intercontinental Fish: Stellar > Ren > C&I > Ryth > Varg (48 of 56 games, truncated to
  team size); on the two largest maps (100x100, 61x71) C&I > Vendetta > Varg > Stellar >
  Ren, which went **3-5**, and 0-4 in the semifinal and final.
- Nyx: Ren > Stellar > C&I > Ryth > Varg (48 of 56); Varg > Vendetta > C&I on some 3- and 4-champion maps.
- Univardisty of Shingtonwash: C&I > Stellar > Varg > Tavi > Ren or Stellar > C&I > Tavi > Ren > Varg.
- hello: Stellar > Tavi > Prism > C&I > Ren, or C&I > Stellar > Ren.

Drafts are map-dependent (same team, different map, different draft) but stable per map
across opponents: that is how sides were identified.

### 2. Economy: capture, walk to the altar, tribute, repeat

| team | W-L | gems tributed/game | gold earned | captures | gems/capture | tributes | median 1st tribute |
|---|---|---|---|---|---|---|---|
| Intercontinental Fish | 37-19 | 866 | 3821 | 23.4 | 38 | 14.2 | round 80 |
| Nyx | 37-19 | 838 | 4946 | 31.6 | 29 | 17.0 | 117 |
| Univardisty of Shingtonwash | 27-15 | 814 | 4104 | 23.0 | 41 | 13.0 | 120 |
| hello | 19-23 | 781 | 3812 | 23.4 | 36 | 14.4 | 93 |
| (16-team range) | | 477-917 | 2800-4950 | 18-32 | 23-41 | 7-20 | 67-136 |

- **Tribute immediately.** 79% of the top-4 teams' tributes come right after a single
  capture (82% for game winners, 79% for losers); 12% after two, 3% after three. The bag
  at tribute is just one camp's gems (median 44 = two wolves' worth; never under 22,
  because a wolf already gave 22). Nobody banked gems. This matches our experiment that
  delaying tribute hurts.
- **Captures are solo.** Only 0-5% of the top teams' captures were shared between allies
  (Tartarus and Sneaky Bush Campers 11%). Champions spread over different camps.
- **Every champion captures and tributes**: no carry/ferry split. Shares of captures /
  tributes (top 4): Stellar 21/23%, Ren 20/21%, Issac 19/16%, Cassi 17/16%, Varg 9/10%,
  Ryth 8/6%.
- **Camps farmed**: single wolves 28% of captures, gold clusters 23%, wolf pairs 11%,
  elk 10%, elk pairs 5%. First three captures of a game: wolf 357, wolf pair 170, gold
  168, elk 144. Monoliths: essentially never. Nyx farmed the most (31.6 captures, 26% of
  them gold clusters), Fish fewer but bigger camps (38 gems/capture).
- **Tempo decides**: median tributed gems by round, winners vs losers: 36 vs 0 at 100,
  153 vs 107 at 200, 324 vs 190 at 300, 499 vs 290 at 400. The leader at round 200 wins
  71% of decided games, at round 400 79%. Fish's first tribute came earliest of the top
  teams (median round 80).

### 3. Items: Power shards, emblem after emblem

Top-4 teams, share of all shards bought per champion:
- Stellar: Power Focus 65%, Durability Health 10%, Durability/Jungle Focus 6% each.
- Ren: Power Focus 51%, Bruiser Health 18%, Durability Health 16%, Treasure Health 8%.
- Cassi: Power Focus 46%, Bruiser Health 18%, Durability Focus 16%.
- Issac: Power Strength 60%, Durability Health 17%, Treasure Strength 8%.
- Varg: Power Strength 55%, Durability Health 14%, Jungle Health 12%.
- Ryth: Power Strength 40%, Bruiser Health 24%, Durability Health 17%, Treasure Health 14%.
- Tavi: Power Focus 21%, Power Strength 21%, Treasure Focus 18%, Monster Focus 14%.

Power (6 shards' worth per emblem) is the default; teams differ in the opener. Fish:
Durability first for Cassi/Ren, then Power. Nyx: **Treasure first** (Ren, Ryth, Issac;
+20% gold), then Bruiser/Durability, then Power; Stellar opens Jungle. Spending: 2.6k-4.5k
gold per game, i.e. almost everything earned. Focus on casters made sense under v0_0_3
(Stellar focus 100); with today's numbers our experiments favour Strength.

Consumables: Nyx and Fish never bought altar locks; UoS placed 3.2 per game, Mite 4.1,
E=mc^2 5.5. Fish bought ~4 teleport crystals per game (3.6 used), Sloppy Joe ~8.

### 4. Fighting: little, but decisive

| team | basic attacks on champions (share) | kills | deaths | deaths to camps | gems stolen | gems lost dying | wards |
|---|---|---|---|---|---|---|---|
| Intercontinental Fish | 76 (14%) | 8.6 | 6.4 | 1.1 | 164 | 62 | 211 |
| Nyx | 60 (9%) | 8.1 | 11.4 | 2.2 | 135 | 117 | 115 |
| Univardisty of Shingtonwash | 65 (14%) | 8.1 | 8.3 | 1.9 | 130 | 156 | 652 |
| hello | 116 (20%) | 9.2 | 9.9 | 1.7 | 154 | 95 | 299 |

- 80-91% of the top teams' basic attacks hit camps. Champion fights are a minority of
  actions, but **kills and deaths decide games**: the side with more kills won 81% of
  decided games (85% from the quarterfinals on), the side with fewer deaths won 75%
  (78%). The *volume* of attacks on champions predicts nothing (51%).
- Winners vs losers per game: 10.2 vs 4.5 kills, 5.9 vs 11.7 deaths, 167 vs 88 gems
  stolen, 73 vs 130 gems lost on death. Deaths to camps are similar (1.4 vs 1.5).
- Fish had the best kill/death ratio (8.6/6.4) and lost the fewest gems dying (62/game).
- Wards were placed constantly (v0_0_3 recharge was 1 turn; 115-650 per game) and are
  not predictive (61%). Altar locks are not predictive either (52%).
- Recall: median health at recall start 34-55% for the top teams (Fish 34%); 12-33% of their
  recalls start at <=25% health and 12-19% at >=90% (going home to shop or after a tribute).
  Fewer recall starts go with winning (91 vs 155 per game, inflated by one team that
  re-issues recall every turn).

### 5. Abilities: on camps, on cooldown; dashes as movement

Casts per champion-game, all 16 teams:

| champion | slot 0 | slot 1 |
|---|---|---|
| Stellar | single target 24.7: camp 75%, enemy 25% | AoE 25.0: ground 47%, camp 41%, enemy 9% |
| Cassi | damage 23.9: camp 78%, enemy 22% | stun 15.5: camp 63%, enemy 37% |
| Issac | attack reset 18.7 (self) | dash 42.3 (ground) |
| Ren | damage+stun 26.4: camp 65%, enemy 35% | dash 45.1 (ground) |
| Ryth | AoE stun 25.7: ground 44%, camp 37%, enemy 16% | attack reset 17.7 (self) |
| Varg | attack reset 17.1 (self) | shield 20.5 (self) |
| Tavi | attack reset 18.1 (self) | damage+stun 26.0: camp 65%, enemy 35% |
| Prism | damage+stun 28.3: camp 58%, enemy 42% | AoE 28.9: camp 47%, enemy 27%, ground 25% |

- Damage and stun spells go mostly on **camps** (60-80%); stuns on camps stop the camp's
  damage too.
- AoE spells (Stellar slot 1, Ryth slot 0) are aimed at an **empty tile** about half the
  time: centred between camps to hit several.
- **Dashes are movement**: ~40-45 per game for Issac/Ren/Vendetta/Vesper (about 60% of
  the maximum an 8-turn cooldown allows in a ~650-round game), all at ground tiles.
- Self-casts (resets, shields) fire on cooldown when in combat.

### 6. Maps, robustness and the tiebreak

- One map (`1b8ddaecdb`, 50x41) has a single central altar walled in behind two
  monoliths. 14 of its 15 games reached round 2000, 12 at 0-0, decided by lifetime gold
  (Tung won one with 66k gold earned vs 8.6k). Only UoS (w9-0/07, 646 gems, beating Fish)
  and procless broke through. Excluded from the averages above.
- **Fish's bot froze on map `42afe633c7`** (crash or fuel overrun; the replay does not
  say which): in three games its champions never left spawn; in the final it sat idle for 67 rounds and never captured. Fish went 0-4 on that
  map: 4 of its 20 losses in these rounds (a fifth of them) came from one map failure, not
  from strategy. (print dont int froze once too.)
- Fish also went 0-4 on the 3-champion map `b468f6febc` and 3-5 with its Vendetta draft.

### 7. What separated winners in the close series

**Final, Fish 10-5 Nyx.** Mostly the same five champions in a different order; Fish won 10
of the 13 games it opened Stellar > Ren. Its 5 losses: two Vendetta-draft maps, the
frozen map, `b468f6febc` and `e255b6ae99`. In its wins Fish out-killed Nyx heavily
(30-6, 27-5, 19-9, 13-6) while capturing as much or more. Fish lost about half as many gems
on death per game as Nyx (62 vs 117 across these rounds).

**Semifinal, Fish 8-7 UoS.** Fish's 7 losses: two Vendetta-draft maps, the frozen map, the
locked map (UoS killed the monoliths and tributed 646 vs 384; Fish had 53 kills but could
not tribute), `b468f6febc`, `cef5107e3c`, `e255b6ae99`. The map failure and the big-map
draft account for 3 of the 7 losses in an 8-7 series: robustness and per-map draft
selection decided it as much as in-game play.

Across all decided games: the winner had more gems captured (88%), more gold earned (88%),
more kills (81%), fewer deaths (75%); more basic attacks on champions (51%), more wards
(61%) or altar locks (52%) did not matter.

## Recommendations for our policy

1. **Never freeze.** A fifth of the champion's losses in these rounds came from one map
   where its bot did nothing. Fuel is a rule: every block must stay within budget on any
   map size (100x100 included), and the interpreter needs a cheap fallback (e.g. starter
   behaviour) whenever a step fails or fuel runs low.
2. **Tribute after every capture or two.** Sprint 1 teams never banked; today's top 4 tribute
   after one capture 59% of the time and after two 20% (camp gems are small now). Our own
   experiment says delaying hurts, so keep bags small.
3. **Spells on camps, self-casts on cooldown, dashes as movement.** Damage/stun spells
   should target camps when no enemy is in range; attack resets and shields fire whenever
   a target is in range; dash slots (Issac, Ren, Vendetta, Vesper) should be spent
   moving toward the goal every time they are ready.
4. **Trade kills, don't chase fights.** Kill/death difference predicts the winner (81%),
   attack volume does not. Engage when the fight calculator says we win it, and protect
   gem carriers: recall at low health (our 20% result) and avoid dying with a bag.
5. **Draft the current meta, from the map.** Ladder: Vesper Vale 92%, Heart of Ruin 78%,
   Marcella 76%, Vendetta 58%, Ryth 55%; Stellar/Ren/C&I have nearly vanished. In Sprint 1 the
   same team won or lost depending on its per-map draft, so the draft should read map
   features (team size, map size, camp mix, monoliths) and pick a sub-policy.
6. **Take monoliths late; mind the gold tiebreak.** On ladder maps with monoliths, the side
   that captured more of them won 80% (45 of 56), typically around round 1,040 once
   champions are itemised. 400 gems is worth 100 wolves today. When altars are unreachable,
   maximise gold earned: 0-0 games go to gold.
7. **Shards: gold first, then Bruiser.** The ladder's top teams open double gold clusters and
   Treasure shards (procless: Treasure Health on every champion), then build Bruiser (Vesper,
   Marcella, HoR, Vendetta) or Power Strength (Vesper). Our interpreter can only buy Power:
   the shard-family block is the most obvious missing piece.

## Policies written

`policies/fish.policy`, `nyx.policy`, `uos.policy`, `hello.policy`: each team's draft order,
shard stats, recall threshold, spell/self-cast/dash use, tribute-after-capture; hello also
chases visible enemies. Win rates in our simulator (200 games each, v1_0_3 rules):

| policy | vs starter | vs v1 | vs fish |
|---|---|---|---|
| v1 (reference) | 0.91 | 0.47 | |
| fish | 0.81 | 0.27 | |
| nyx | 0.79 | 0.27 | 0.40 |
| uos | 0.89 | 0.37 | 0.58 |
| hello | 0.73 | 0.27 | 0.39 |

Single-change ablations of fish (vs starter / vs v1): recall at 20% instead of 30%:
0.86 / 0.38 (helps, as in our experiments); Vesper Vale instead of Stellar first:
0.86 / 0.30; strength shards for casters: 0.81 / 0.23; no Ren dash: 0.77 / 0.27; no
self-casts: 0.81 / 0.29. ±0.035 is one standard error at 200 games.

### Behaviour the language cannot express yet (missing blocks)

- **Shard family**: `shard(stat)` always buys Power. Needed: `shard(family, stat)`
  (Treasure-first openers, Bruiser builds that dominate the current ladder, Durability/Jungle).
- **Heart of Ruin pick**: no `champ_heart_of_ruin()` block, yet it is the ladder's most common
  first pick (also Marcella/Willow/Tavi branches lack kit-specific handling).
- **Monolith targeting**: camp-type filters (e.g. `camps_of_type(monolith)`) and a
  "strong enough to take it" condition.
- **Cassi vs Issac**: `i_am(champ_cassi_issac())` matches both bodies; they want different
  stats and spells.
- **Consumables**: buy/use altar lock and teleport crystal (UoS 3.2 locks/game; Fish ~4
  crystals/game).
- **Dash along the path**: a "tile k steps along the shortest path to X" block, so dashes
  can be used as movement. The policies approximate it with
  `ring(goals, d - 2) within 2 of me`, which ignores walls.
- **AoE aiming**: "tile in range that hits the most camps/enemies" (Stellar/Ryth/Prism
  aim at empty tiles half the time).
- **Map features in the draft**: team size, map size, camp mix, altar reachability (for
  per-map drafts and the gold-tiebreak switch).
- **Ward readiness/placement**: `ward_ready()` and a target rule (less important now that
  wards recharge in 10 turns).
- **Enemy gem count**: to target carriers (kills steal the bag).
