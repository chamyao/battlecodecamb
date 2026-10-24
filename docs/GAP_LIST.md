# Gap list: what our bot does wrong against teams rated ~+100 above us

## Data

- **Opponents.** The band is the teams rated 1644-1744 on the ladder (we are 1600, rank 268). I used the 10 unranked groups that the coordinator queued for v21 at 13:32 UTC: Quantom, Gem_alert, Ding, Mommy Shogun, Kingstonks, Memory?, WHIM, NotSoLonely, Monarch and vc?. That is **50 games, v21 15-35**.
- **No ranked band games exist.** Our ranked games from v17 to v21 (205) were all against teams rated below 1644, so the band data is these 50 unranked games.
- **Tools:** `analysis/gaps.py`, which writes the full table to `analysis/gaps_band_v21.md`, plus `analysis/low_hp.py` and `analysis/fight_dump.py`.
- **Uncertainty.** Every number is ± one bootstrap SE over games. With 50 games, the win-rate SE is about 0.065.
- **Cost.** It is in gems, because these games are decided by the gem race:
  - In our losses they reach 1,000 (1000 ± 18) while we have 469 ± 52.
  - In our wins we have 963 ± 54 and they have 623 ± 68.
  - The win-probability proxy is the gap between wins and losses.

## Ranked gaps (cost × frequency)

| # | gap: our behaviour | frequency (all games) | cost | in wins / in losses | sim metric to search on |
|---|---|---|---|---|---|
| 1 | **Gems lost on death.** 54% ± 7 of our champion deaths happen while carrying, at a median of 7 tiles from the nearest altar (46% at 8+, 16% within 3). | 184 ± 23 gems lost per game (144 to champions, the rest to camps). We submit 76% ± 4 of what we capture; they submit 99% ± 4, which includes picking up our drops. | ~185 gems per game, about 20% of a win | 122 ± 27 / 211 ± 30 lost; 91% / 66% of captures submitted | `interp_eval --details` `gems_lost_to_champs` (ours). In the sim v21 loses 20-81 per game, 51 against hunter3, so the sim underestimates this gap by about 3x. |
| 2 | **Low capture yield.** Our captures pay 10.9 ± 1.1 gems; theirs 14.9 ± 1.6. They take richer groups. | Every capture: 75 per game | We capture 815 ± 58 per game, they capture 895 ± 47 | 1056 / 712 captured (theirs 712 / 973) | Gems captured per capture. Not in `interp_eval` yet: add captured gems and capture count per side to `--details`, or count captures from `GAME_EVENTS`. Proxy for now: `a_gems`. |
| 3 | **Too few bank trips.** 18.0 ± 1.6 tributes per game against their 26.2 ± 2.5, with bags of 30 against 34. | Every game | It feeds gap 1: gems held longer get lost | 26.4 / 14.4 tributes (theirs 17.9 / 29.7) | Tributes per game, and the mean bag at death (gems lost to champions ÷ deaths while carrying). |
| 4 | **Deaths to camps.** | 4.2 ± 0.7 per game, on top of 11.1 ± 1.5 deaths to champions | ~40 gems per game, plus 60 rounds of absence each | 5.1 / 3.9 (not a separator) | `deaths[us] − kills[them]` from `interp_eval`. |
| 5 | **Dying after dropping to half HP.** A crossing is dropping below half HP with an enemy within 5 tiles. | 23.9 ± 2.6 crossings per game; 45% ± 3 die within 15 rounds. Band teams: 19%. | About 10.8 deaths per game start this way | 39% / 48% die | `low_hp.py`'s death rate after a crossing. The sim needs per-round HP: `@@EV chit` lines give damage events, but positions only for the hitter and the target. |
| 6 | **Item spread vs carry stacking.** Team-mean stats are level through round 600, but the champions that kill us are their stacked carries. | Decisive fights after round 400: killer vs victim item points 49 vs 20; killer strength +90 over the victim. | Feeds gaps 1 and 5 | — | Max strength and max item points over our champions at rounds 400/600. Needs a per-champion stat dump in `--details`. |
| 7 | **Dying outnumbered.** | 62% ± 3 of our deaths have 2+ of theirs within 5 tiles; 46% ± 3 are outnumbered by 2+ | Not a separator here: 74% in our wins, 58% in losses | — | Share of deaths with 2+ enemies within 5. Not computable from `@@EV` alone; needs champion positions at death. |
| 8 | **Farming camps with enemies near.** | 15% ± 2 of deaths come within 5 rounds of hitting a camp; 29% of decisive victims were hitting a camp | Small | 15% / 15% | Deaths within 5 rounds of a camp attack. |

Gaps 1-3 are the gem conversion chain: capture less, bank less often, lose more on death. Together they separate wins from losses:
- **Losses:** we capture 712 gems and submit 469.
- **Wins:** we capture 1,056 and submit 963.

The fight-side gaps (5-8) are smaller at this tier than against the top 9.

## What happens around our low-HP crossings (the follow-up requests)

**After the crossing (15 rounds), as a share of all crossings:**
- 11% ± 1 died within 2 rounds (burst).
- 5% ± 1 died mid-recall (recall started after the crossing, then cancelled by damage).
- 13% ± 2 died while heading home, walking or dashing.
- 16% ± 2 died otherwise: they stayed in the fight.
- 55% survived.

Burst alone doesn't dominate (it is 24% of the deaths that follow a crossing), so this is not only an item gap. On the other hand, a flee rule was negative in the sim, and 13% already die while heading home. So the lever is before the fight, not during it.

**Before the crossing**, at the first hit of that engagement: 1,088 crossings had a first hit within 20 rounds. Death rate after the crossing:

| condition at the first hit | frequency | death rate if true | if false |
|---|---|---|---|
| outnumbered within 5 tiles (theirs > ours) | 20% ± 1 | **57% ± 3** | 44% ± 2 |
| their champion's max HP 200+ above ours | 45% ± 2 | **53% ± 2** | 41% ± 2 |
| first hit from range 3+ (their ranged poke or ours) | 80% ± 1 | 48% ± 2 | 41% ± 3 |
| they hit first | 49% ± 2 | 44% ± 2 | 50% ± 2 |
| we were carrying | 57% ± 2 | 44% ± 2 | 51% ± 2 |
| we were hitting a camp | 26% ± 1 | 40% ± 3 | 49% ± 2 |
| an ally within 5 that joined | 32% ± 1 | 42% ± 3 | 49% ± 2 |
| an ally within 5 that did not join | 23% ± 1 | 43% ± 3 | 48% ± 2 |
| channelling (recall or tribute in the 5 rounds before) | 2% | 46% ± 10 | 47% ± 2 |

At the first hit, both sides are near full HP (0.94 and 0.95), with 2 of ours to 1 of theirs (medians).

Two pre-fight conditions carry the risk: **being outnumbered at the first hit** (+13 points) and **facing a bigger champion** (max HP +200; +12 points). That matches gap 6: the champions that kill us are stacked carries.

Candidate pre-fight rule for the lines to search: don't take or stay in a fight when the enemies within 5 outnumber us, or when the nearest enemy's max HP is 200+ above ours. `local_strength()` covers both (HP × damage). Sim metric for the rule: the death rate after a crossing, plus deaths per game and gems lost to champions, holding win rate against v21.

**Stats (the snowball check)**, mean per champion, us / band:

| | r200 | r400 | r600 |
|---|---|---|---|
| max HP | 1151 / 1133 | 1418 / 1351 | 1762 / 1591 |
| strength | 58 / 57 | 74 / 76 | 95 / 104 |
| focus | 102 / 97 | 102 / 105 | 102 / 118 |
| item points | 3 / 4 | 9 / 11 | 16 / 20 |

There is no team-level snowball against the band; we are level or ahead on HP. The gap is concentration: their killers carry 49 item points against our victims' 20. **So it is not an economy gap in the snowball sense.** Their gold goes into one carry, and that carry wins its fights.

## Calibration: does the sim league predict this tier?

**No.** Here is v21 against the sim league (`interp_eval --bot-seeds`, 80 games per pair, all 40 maps), next to v21 against the real band:

| | real band (50) | sim: hunter3 | sim: hunter2a-c | sim: icecream / metab / metadraft / odyssey | sim: v18-v20, lean-g65 |
|---|---|---|---|---|---|
| v21 win rate | **30% ± 6** | 75% | 84-90% | 91-93% | 59-63% |
| gems us / them | 617 / 887 | 905 / 587 | 909-938 / 513-531 | 928-960 / 276-506 | 824-854 / 703-741 |
| our kills / deaths per game | **2.9 / 15.4** | 7.6 / 9.5 | 9.0-9.7 / 7.9-8.4 | 8.8-13.0 / 5.8-6.9 | 6.1-7.8 / 9.6-11.0 |
| gems lost to champions, us | **144** | 51 | 39-48 | 21-28 | 67-81 |
| champion damage us / them (post-shield) | 22k / 35k | 45k / 35k | 43-46k / 27-28k | 35-46k / 14-21k | 42-47k / 41-46k |

- Every stand-in is weaker than the band on every axis.
- The sim overestimates our kills by 2-4x and underestimates our gems lost on death by about 3x.
- The closest sim opponents are our own previous versions (v18-v20). Even they lose 37-41% to v21; the band beats v21 70%.
- **A league bar that v21 clears at 59-93% says little about this tier.** The sim metrics that differ most from reality are kills per game and gems lost to champions. A stand-in that matched those two would be a better bar.

## Against the top 9 (for reference; `docs/TOP_TEAMS*.md`)

Our versions go 5-245 against the top 9. The same gaps appear, larger:
- Deaths 16-18 against their 1.6.
- Gems lost dying 132-148 against their 11-28.
- 69% of our deaths outnumbered.
- An item gap of 59 vs 11 points after round 400.
- Low-HP death rate 88% against Fish's 6%.

The per-(version, team, map, side) table is in `data/top-teams-target.json`, built by `analysis/target_build.py`. It is now a progress tracker for our versions, not a fitting target; see `docs/TOP_TEAMS_TARGET.md`.
