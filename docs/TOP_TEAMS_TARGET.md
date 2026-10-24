# Top-team fitting target

## Goal

Build an opponent whose sim games against our five versions reproduce what the real top teams did to those versions. It is an objective to fit, not a win rate to maximise.

Why: in the sim, v21 wins 63-82% of fights against every stand-in and hunter. On the ladder the top teams kill us about 13 times per game and die 1.6 times. So the league bar measures progress against weak fighters.

## Data and files

- **Games.** 250 real games: 10 top teams × 25 maps and sides, each played by our 5 versions. The versions are tune-5 (v16), v17, v19, v20 and v21, all on 24 Oct, with the same unranked groups, maps and sides.
- **Replays.** `data/top-teams-2026-10-24/` (tune-5), `data/top-teams-v17-…`, `-v19-…`, `-v20-…`, `-v21-…`. Each holds `sides.json`, which gives side A/B per match.
- **Machine-readable target:** `data/top-teams-target.json`. All pairs in it are `[us, them]`.
  - `games`: one row per (version, team, map, our side). Each row holds:
    - result, rounds, gems, kills, deaths, champion damage (official summaries), tributes, captures, gems per capture, gold and gems lost dying;
    - our deaths to champions, and `share_2v1` (the share of those with 2+ of theirs within 5 tiles);
    - `first_kill_round` (ours, theirs), the drafts, and the match id.
  - `by_version_team`: the same, averaged per (version, team).
  - `fights[team][champion]`: their engagement statistics, pooled over the 5 versions. They cover:
    - distance at the first hit and 5/10 rounds before;
    - own and target HP at the first hit, and allies/ours within 5 tiles;
    - targeting: closest, lowest HP, carrier, from a bush;
    - opener and first-three-action distributions, rounds to the first cast, and basic-attack range kept;
    - duration, chase, HP at the end of the engagement (disengage HP), and recall within 10 rounds.
    - An engagement starts at their first damage on one of ours after 10 quiet rounds, and ends after 6 rounds without damage (`analysis/fight_rules.py`).
  - `decisive[team]`: our deaths with no kill back within 10 rounds (`analysis/fight_dump.py`). They cover who hit first, 2+ hitters, hit-back, stuns, range, vision, and the item gap after round 400.
- **Builder:** `analysis/target_build.py OUT.json LABEL=EXDIR,FETCHDIR ...`. It needs the extracted replays (`analysis/extract.js`) and each group's `sides.json` and `summaries/`.

## Which team to clone

| team | bot changed during the day? (games where their action diverged first, consecutive-version reruns) | notes |
|---|---|---|
| **Intercontinental Fish** | **never (0)** | the most consistent; highest 2v1 share (0.83) |
| :3, Univardisty, policy wonk, prism best girl | never (0) | |
| Claudus Maximus, procless | 1 game | |
| willow best girl | 5 games | |
| Mite | 7 games | |
| vc? | 9 games (between v17 and v19, v19 and v20, v20 and v21) | its wins aren't comparable across versions |

The engine is deterministic, so a rerun of the same game diverges only when one side's behaviour changed.

**Fish is the one to clone.** Its bot stayed identical across all 5 dates, so its 25 games per version are a clean before/after for our changes. It is also the most ladder-like killer: 18.6 deaths for us per game, and 83% of our deaths come against 2+ of theirs.

## Per team (all five versions pooled, 25 games each)

| team | games | W-L (ours) | deaths us / them | kills us / them | gems us / them | champ dmg us / them | 2v1 share | first kill on us (median rd) | their draft (most common) |
|---|---|---|---|---|---|---|---|---|---|
| :3 | 25 | 0-25 | 14.0 / 0.3 | 0.1 / 8.8 | 295 / 1038 | 4.3k / 14.8k | 0.55 | 276 | Heart Prism Vendetta Vesper Marcella |
| Claudus Maximus | 25 | 0-25 | 22.0 / 1.6 | 0.6 / 20.7 | 141 / 1043 | 10.3k / 35.6k | 0.72 | 132 | Vesper Heart Vendetta Tavi Marcella |
| Intercontinental Fish | 25 | 0-25 | 18.6 / 1.3 | 0.6 / 16.8 | 161 / 1016 | 8.2k / 23.0k | 0.83 | 105 | Vesper Vendetta Heart Cassi Ryth |
| Mite | 25 | 0-25 | 15.0 / 3.1 | 0.5 / 10.5 | 92 / 1026 | 5.0k / 15.8k | 0.65 | 145.0 | Vesper Vendetta Ryth Tavi Marcella |
| Univardisty of Shingtonwash | 25 | 0-25 | 15.1 / 0.6 | 0.1 / 14.8 | 213 / 1019 | 13.0k / 33.5k | 0.66 | 107 | Varg Vesper Willow |
| policy wonk | 25 | 0-25 | 14.8 / 2.4 | 0.4 / 5.8 | 260 / 1070 | 4.0k / 10.4k | 0.46 | 278 | Marcella Vesper Tavi Willow Heart |
| prism best girl | 25 | 1-24 | 14.2 / 1.0 | 0.3 / 7.4 | 165 / 1059 | 3.9k / 11.7k | 0.62 | 169 | Prism Vesper Marcella Vendetta Ryth |
| procless | 25 | 0-25 | 15.9 / 0.4 | 0.1 / 14.0 | 299 / 1018 | 12.6k / 28.7k | 0.46 | 109.0 | Heart Vesper Ryth Marcella |
| vc? | 25 | 4-21 | 29.7 / 4.7 | 2.5 / 25.4 | 376 / 971 | 26.0k / 49.9k | 0.67 | 104.5 | Vesper Vendetta Marcella Heart Ryth |
| willow best girl | 25 | 0-25 | 12.6 / 0.6 | 0.4 / 10.4 | 124 / 1024 | 3.6k / 16.7k | 0.53 | 252 | Prism Vesper Marcella Willow Heart |

| team | decisive fights | they hit first | 2+ hitters | victim hit back | stun on victim | hits from outside victim range | killer unseen 3 rds | item points after r400 killer/victim |
|---|---|---|---|---|---|---|---|---|
| :3 | 219 | 73% | 56% | 68% | 53% | 50% | 24% | [56.5, 16.0] |
| Claudus Maximus | 507 | 75% | 74% | 70% | 62% | 45% | 27% | [78, 10] |
| Intercontinental Fish | 407 | 72% | 82% | 80% | 57% | 40% | 27% | [72, 11] |
| Mite | 251 | 70% | 64% | 76% | 59% | 44% | 39% | [44, 9] |
| Univardisty of Shingtonwash | 368 | 74% | 66% | 76% | 38% | 38% | 19% | [85, 11] |
| policy wonk | 142 | 63% | 46% | 63% | 51% | 54% | 37% | [81, 7] |
| prism best girl | 180 | 78% | 68% | 64% | 80% | 43% | 34% | [27.5, 9.5] |
| procless | 350 | 71% | 56% | 72% | 59% | 31% | 32% | [64.5, 12.0] |
| vc? | 599 | 61% | 72% | 78% | 51% | 30% | 29% | [49.0, 15.0] |
| willow best girl | 258 | 90% | 47% | 44% | 81% | 47% | 23% | [39.5, 9.0] |

## Fish per version (the fitting target for a Fish clone)

| our version | W-L | deaths us / them | kills us / them | gems us / them | champ dmg us / them | 2v1 share | first kill on us (median round) |
|---|---|---|---|---|---|---|---|
| tune-5 | 0-5 | 18.4 / 1.6 | 0.4 / 15.8 | 140 / 1014 | 6.0k / 21.7k | 0.85 | 78 |
| v17 | 0-5 | 19.2 / 1.8 | 0.8 / 16.4 | 178 / 1014 | 8.4k / 22.8k | 0.67 | 105 |
| v19 | 0-5 | 18.8 / 1.2 | 0.4 / 17.6 | 146 / 1018 | 9.7k / 23.7k | 0.85 | 105 |
| v20 | 0-5 | 18.8 / 1.0 | 0.8 / 17.6 | 167 / 1019 | 9.8k / 24.6k | 0.88 | 74 |
| v21 | 0-5 | 18.0 / 1.0 | 0.4 / 16.6 | 174 / 1014 | 7.3k / 22.0k | 0.92 | 106 |

Fish's maps and sides (the same 5 in every version) are listed in `games`.

## How Fish plays (for a hand-built clone)

**Draft:** Vesper Vale, Vendetta, Heart of Ruin, Cassi & Issac, then Ryth (15 of 25 games) or Varg. In 3v3 it takes VV, HoR and Vendetta.

**Economy:**
- First capture at round 26, first tribute at round 138.
- 25 tributes per game, median bag 22 [15-51].
- Altar lock bought by round 200 in about 0.85 of games.

**Items** (shards per game by round 200 → by round 600):
- Vesper Vale: all strength.
  - By round 200: Power shard Str 2.1 + Power Emblem Str 1.8.
  - By round 600: Power Emblem Str 17 + Power shard Str 9.9.
  - This is the 235-strength VV of `docs/TOP_TEAMS_FIGHTS.md`.
- Heart of Ruin: Jungle shard Focus and Treasure HP by round 200, then Bruiser HP.
- Vendetta: Jungle Str and Treasure HP, then Bruiser Str.
- Ryth: Bruiser HP and Power Str.
- Cassi: focus (Durability and Power Focus).

**Fights, per champion** (median [25th-75th percentile] over 5 versions × 25 games):

| champion | engagements | kill rate | distance 10 / 5 / 0 rounds before the first hit | own / target HP at the first hit | allies / ours within 5 | opener | basic range | chase (tiles) | HP at the end | recall within 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Vesper Vale | 175 | 66% | 11 / 8 / 4 | 0.96 / 0.78 | 2 / 1 | reset > B > B 24%, B > reset > B 22%, dash > B > B 21% | 3 (56%), 4 (18%), 2 (16%) | 1 | 0.89 | 24% |
| Heart of Ruin | 149 | 26% | 10 / 6 / 2 | 0.95 / 0.79 | 2 / 2 | dash > B > B 38%, B > B > B 26%, B > shield > B 11% | 1 (64%), 2 (25%) | 3 | 0.80 | 27% |
| Cassi | 143 | 22% | 13 / 8 / 5 | 0.90 / 0.79 | 2 / 1 | cc (S1) > damage (S0) 41%, cc > B > B 12% | 3 (72%) | 0 | 0.78 | 18% |
| Ryth | 140 | 34% | 13 / 9 / 5 | 0.84 / 0.88 | 2 / 1 | AoE (S0) > B > reset (S1) 44%, AoE alone 31% | 1 (55%), 2 (42%) | 3 | 0.60 | 28% |
| Vendetta | 126 | 52% | 10 / 7 / 2 | 0.88 / 0.78 | 2 / 1 | B > reset > B 71%, dash > B > B 18% | 1 (54%), 2 (37%) | 2 | 0.75 | 40% |
| Issac | 94 | 37% | 11 / 6 / 2 | 0.85 / 0.80 | 2 / 1 | B > reset > B 51%, dash > B > B 28% | 1 (54%), 2 (36%) | 1 | 0.59 | 33% |

Patterns common to all Fish champions:
- **Group.** Two allies are within 5 tiles at the first hit, against one of ours.
- **Target.** The closest visible enemy, in 86-95% of engagements; that is also the lowest-HP one in 68-87%.
- **Approach.** They close in from 10-13 tiles over about 10 rounds.
- **From a bush:** 17-29% of first hits.
- **Short engagements:** 3-6 rounds.
- **Leave while healthy:** HP 0.6-0.9 at the end of an engagement.

## Using the target

Suggested objective for a stand-in X, fitted in the sim against our five versions (exact replicas) on Fish's 25 maps and sides:
- **Outcome error.** For each (version, map, side): (deaths_us, kills_us, gems_us, gems_them, champ_dmg_us, champ_dmg_them, share_2v1, first_kill_round_them), each normalised by its spread across the 25 real games. Sum the squared errors.
- **Behaviour error.** For each Fish champion: the distance between X's and Fish's distributions of distance at the first hit, opener, basic range, allies within 5 and HP at the end of an engagement.
- **The main check:** does v21 die about 18 times per game against X (17-19), with about 85-90% of those deaths against 2+ of X's champions, and does X submit about 1,015 gems against v21's ~170?
- **Version ordering:** X should preserve the ordering across our versions. For example, Fish's first kill came later against v17/v19/v21 (about round 105) than against tune-5 and v20 (74-78).

Running the clone in the sim (exact replicas of our versions) is the sim session's domain. A first Fish clone can start from `policies/opp-hunter3.policy` (on `funsearch/style`), changed to:
1. Fish's draft.
2. Fish's item build: VV all strength (Power family); HoR focus, then HP; Vendetta strength.
3. Engage only with 2 allies within 5 tiles, start closing on a visible enemy at 10-13 tiles, and hit the closest.
4. The per-champion openers above.
5. Leave at HP 0.8 (VV 0.9).
6. Bank at a median bag of 22.
