# How the top teams win fights: 7 decisive fights turn by turn

Source: the 50 unranked games of tune-5 vs the top teams (`data/top-teams-2026-10-24/`).
Tool: `analysis/fight_dump.py`.
- A **decisive fight** is one where one of our champions dies to a champion and we get no kill within ±10 rounds.
- The full turn-by-turn dumps of the 7 fights are in `analysis/top_teams_fights_focus.md`. They cover every champion within 10 tiles, with:
  - position, HP / max HP, gems, strength and focus rebuilt from purchases, and item points by stat;
  - our vision of them for 5 rounds before the first hit;
  - every attack and cast in engine order, with slot, target and damage.
- Aggregates: 264 decisive fights vs vc?, Intercontinental Fish and willow best girl (in the dump file), and 634 vs all 10 teams (`analysis/top_teams_fights_all_aggregates.md`).

## The mechanism in one paragraph

Turn order, vision tricks and the first hit don't decide these fights. What decides them:

**Early (before round 150): numbers.**
- There is no stat gap: 0 item points on both sides, max HP equal.
- 85-89% of our deaths come against 2+ of their champions.
- They come together (often 3-4), focus one target and chain ability combos.
- Their HoR soaks our damage behind its shield.

**Later: a stat snowball from those early kills.**
- Rounds 150-400: item points killer 11 vs victim 3.
- After round 400: 58 vs 12, with killer minus victim strength +68, focus +80, max HP +800.
- They stack one stat per carry. Fish's VV had 36 strength points by round 192 and hit 235 per basic, against our 50-55.
- willow's HoR and Prism stack focus (412 focus on HoR): dash 635, Prism stun 456 and AoE 304.
- At that point one champion kills one of ours alone in 3-4 rounds, or in a single round of burst.

**Our side throughout.**
- Our victims ignore visible threats: in 5 of 7 fights the killers were visible for all 5 rounds before the first hit.
- We keep farming the camp (34%), or walk into the fight.
- We hit the shielded HoR instead of the champion killing us.
- Our melee champions neither close on nor flee a VV kiting at range 3-4.

## Aggregates

| | vc?/Fish/willow (264) | all 10 teams (634) |
|---|---|---|
| first champion damage of the fight by them | 77% | 77% |
| their side acted first in the round of the first hit | 46% | 47% |
| killer unseen by all of ours for the 3 rounds before the first hit | 27% | 26% |
| their champions damaging the victim (median) / 2+ | 2 / 74% | 2 / 67% |
| rounds from first hit to death (median) | 10.5 | 10 |
| victim damaged one of theirs before dying | 66% | 65% |
| their hits from beyond the victim's attack range | 33% | 38% |
| stun/cc landed on the victim | 66% | 59% |
| victim HP fraction at fight start (median) / below 0.75 | 0.96 / 24% | 0.94 / 26% |
| victim was attacking a camp in the 5 rounds before | 34% | 31% |

By phase, all 10 teams:

| fight starts | fights | item points killer vs victim | strength gap | focus gap | max HP gap | 2+ hitters |
|---|---|---|---|---|---|---|
| rounds 0-150 | 62 | 0 vs 0 | -5 | 0 | 0 | 89% |
| 150-400 | 158 | 11 vs 3 | +10 | 0 | +262 | 81% |
| 400+ | 414 | 58 vs 12 | +68 | +80 | +800 | 59% |

How to read these:
- **First hit.** Turn order is a coin flip (46-47%) and most killers were in our vision (73%). They hit first because they walk at us, while we keep doing what we were doing.
- **Victim HP.** Victims start the fight near full HP (median 0.94-0.96). Picking off already hurt targets happens (24-26%), but it isn't the main pattern.
- **Phases.** Two thirds of decisive fights come after round 400, when the item gap is 4-5x. The gap is built from the early kills, 100 gold each (`docs/TOP_TEAMS.md`: their gold 8.3k vs 3.0k per game).

## The 7 fights

Notation:
- `them:` / `us:` prefixes the actor.
- `B` is a basic attack; `S0`/`S1` is the ability slot, followed by its type.
- Damage is given in brackets.
- Rounds are listed in engine order within the round.

### 1. vc? on 00eight, r79-87: 3v1 focus on our VV, stun then dash, both resets

| side | champion | pos | HP/max | str | focus | items |
|---|---|---|---|---|---|---|
| them | Vesper Vale | (9,2) | 1000/1000 | 55 | 100 | none |
| them | Vendetta | (6,11) | 1000/1000 | 70 | 100 | none |
| them | Ryth | (7,10) | 1200/1200 | 45 | 100 | none |
| us | Vesper Vale | (13,7) | 1000/1000 | 55 | 100 | none |
| us | Ryth | (18,0) | 100/1200 | 45 | 100 | recalling |
| us | Ren | (12,4) | 360/900 | 35 | 100 | low from the camp |

All three of theirs were visible for 5 rounds before the first hit (VVVVV). Our VV and Ren kept hitting the camp while they walked in.

- **r79** them:VV `B > S0 reset > B` on Ren from range 4 (-55, -55). us:VV S1 dash toward the fight.
- **r80-82** our VV basics their VV (-55 each). Their Vendetta and Ryth close from 7 to 2 tiles, fully visible.
- **r83** them:Ryth **S0 AoE stun** on our VV (-100). Our Ren starts a recall.
- **r84** them:Vendetta **S1 dash** in, B (-70). them:Ryth `B > S1 reset > B` (-45, -45).
- **r85** them:Vendetta `B > S0 reset > B` (-70, -70), Ryth B. Our VV hits Vendetta once.
- **r86-87** them:VV comes back: `B > S0 reset > B` kills our VV.

Mechanism: 3v1 at even stats.
- Open with the reach stun, then the gap-closer, then **both resets in the same round** (four basic hits a round).
- Our VV traded 1-for-3 the whole time instead of leaving when three champions came into vision.

### 2. vc? on 00contest, r34-45: HoR baits, three others arrive from fog, focus Ren

| side | champion | pos | HP/max | str | focus |
|---|---|---|---|---|---|
| them | VV / Vendetta / Marcella | (27,14-17) | full | 55 / 70 / 45 | 100 / 100 / 60 |
| them | Heart of Ruin | (26,21) | 1000/1000 | 30 | 100 |
| us | Vendetta / Ryth / Ren | (28-30,22) | full | 70 / 45 / 35 | 100 |

Vision: VV, Vendetta and Marcella were unseen for all 5 rounds; HoR came out of a bush.

- **r34-41** HoR alone pokes our Vendetta and shields; our Vendetta trades with HoR for 8 rounds (the first two of our hits do 0 because of the shield). Marcella S1 damage (-120) at r40.
- Meanwhile VV, Vendetta and Marcella walk 5 tiles south in the fog, to 1-2 tiles from our group.
- **r41** our Ren dashes in toward HoR.
- **r42** them:VV `B > S0 > B` and them:Vendetta `B > S0 > B` on Ren (-250). HoR shields again.
- **r43-45** VV + Vendetta + HoR + Marcella `B > S0 > B` focus Ren; Ren dies at r45. Our Ryth (full HP, 1-2 tiles away) never acts.

Mechanism: the tank holds our attention while the damage arrives unseen.
- Then they kill the champion that stepped forward.
- Our Ryth stood next to the fight at full HP for 4 rounds without casting.

### 3. vc? on 00gemfight, r87-96: 1v4 we stood in, failed recall under chase

- Our Vendetta (1100/1100, 10 gems) stood at (8,1).
- vc?'s Vendetta, Marcella and HoR walked in a line toward it for 5 rounds, fully visible (VVVVV).
- Their VV was hurt, 9 tiles away.

- **r87** them:Vendetta **S1 dash** + B (-70). Our Vendetta hits back (-76). them:Marcella S1 damage (-120).
- **r88** them:Vendetta `B > S0 reset > B` (-140). HoR shields.
- **r89** them:HoR **S1 dash** (-150) + B.
- **r90-92** Vendetta + HoR basics (-100 a round). Ours hits back only every other round.
- **r92** at 320 HP ours dashes away 3 tiles; **r93** starts a recall at 220 HP.
- **r95** they have walked 3 tiles after it: Vendetta B + Marcella S1 (-190) cancel the recall. Dead at r96.

Mechanism: don't stand still when 3-4 visible enemies approach; leave at ~0.8 HP, not ~0.3.
- A recall is no escape within 3 tiles of a chaser.

### 4. Intercontinental Fish on 00collision, r106-112: we hit first, they win with numbers and a strength lead

| side | champion | HP/max | str | items |
|---|---|---|---|---|
| them | Vesper Vale | 1540/1600 | **120** | 13 str, 6 health |
| them | Heart of Ruin | 1300/1300 | 30 | 3 health |
| them | Vendetta | 660/1000 | 70 | none |
| us | Vesper Vale | 880/1000 | 55 | none |
| us | Tavi | 660/900 | 45 | none |

All of them were fighting a shared camp and all were visible.

- **r106** we land the first hit: our VV B on HoR, Tavi **S1 stun** + B on HoR (-254 total). them:Vendetta S1 dash + B on our VV.
- **r107** them:VV **S1 dash** in + B (-120). Vendetta B (-70).
- **r108** them:VV `B > S0 reset > B` (-240), Vendetta B, HoR B + **S1 dash AoE** (-167 to VV *and* Tavi).
- **r109** our VV dies (it attacked Vendetta every round, but for 55 against a 120-strength VV).
- **r110-112** Vendetta + HoR + VV on Tavi; dead at r112.

Mechanism: 3v2, plus a carry with **2.2x our strength by round 106** (13 strength points).
- Our first hit and stun went into HoR, the tank.

### 5. Intercontinental Fish on 00corners, r192-195: one carry, stat-stacked, kites a melee

- Their VV: 1600/1600, **strength 235** (36 strength points, 6 health).
- Our Ryth: 960/1300, strength 50, 2 item points.
- The VV was visible 5 rounds out; it had just been hitting a camp.

- **r192-195** them:VV B from **range 2-3** every round (-235 each), finishing with `B > S0 reset > B`. Ryth dies in 4 rounds.
- Our Ryth (melee, range 1) **does nothing for 4 rounds**: no attack, no stun cast, no step in or out.

Mechanism: the stat gap alone (4.3x strength) plus range.
- A melee champion that is out of range and has no "close or flee" rule just stands there.

### 6. willow best girl on 00packs, r110-114: range kiting, our damage into the shielded HoR

| side | champion | HP/max | str | focus |
|---|---|---|---|---|
| them | Vesper Vale | 820/1000 | **110** (11 str points) | 100 |
| them | Heart of Ruin | 920/1000 | 30 | 136 |
| them | Prism | 700/700 | 35 | 144 |
| us | Vendetta | **640/1200** | 70 | 100 |
| us | Vesper Vale | 1200/1200 | 60 | 100 |
| us | Tavi | 975/975 | 50 | 110 |

- **r110-113** them:VV B on our Vendetta from range 3-4 every round (-110). HoR shields.
- Our VV and Vendetta attack **HoR** (the first hits do 0 because of the shield). Our Vendetta walks toward HoR, staying inside the VV's range.
- **r112** them:Prism **S1 AoE** from range 5 on Vendetta (-168). HoR B.
- **r113** our Vendetta at 110 HP dashes **toward** their VV; dies at r114.
- Tavi keeps hitting a camp 7 tiles away throughout.
- willow casts `Recall` after every action, every round (see "open questions").

Mechanism:
- Wrong target: we hit the closest enemy, a shielded tank, while a ranged carry with 2x our strength kills us from 3-4 tiles.
- A 640/1200 Vendetta should not be in that fight at all.

### 7. willow best girl on 00pilgrimage, r836-845: focus burst, 1,136 damage in one round

| side | champion | HP/max | str | focus | item points |
|---|---|---|---|---|---|
| them | Prism | 1720/1720 | 42 | **232** | 19 focus, 17 health, 3 str |
| them | Heart of Ruin | 1702/1800 | 44 | **412** | 26 focus, 8 health, 4 str |
| us | Vesper Vale | 1600/1700 | 100 | 100 | 9 str, 7 health |
| us | Ryth | 960/1400 | 45 | 100 | 2 health |

- **r836** them:Prism **S1 AoE** from range 4-5 on our VV (-304).
- **r837** them:HoR **S1 dash** (-635) + B, then Prism **S0 stun** (-456). Our VV goes from 1296 to 160 in one round.
- **r838-840** HoR basics; our VV dashes away at 70 HP and survives on 24 HP.
- **r841-845** our Ryth (960/1400) **walks into** HoR and Prism and trades basics with HoR.
  - Prism B every round from range 3, then S1 AoE (-304).
  - HoR S1 dash (-199) kills Ryth.

Mechanism: focus-stacked casters.
- Their abilities do 3-6x a basic attack. After their cooldowns come back (8 turns) they repeat the burst.
- Our items are 16 points spread over strength and health, against their 38-39 focused on one stat.

## What it says, as rules for our bot

1. **Count before engaging, and leave when outnumbered.** If enemies within 8 outnumber allies within 5, and we aren't already winning the exchange, move away *now*, at high HP. Don't start a recall within 3 tiles of a chaser; walk first. (Fights 1, 3, 4, 7.)
2. **Stop farming when enemies come into vision.** 34% of victims were hitting a camp, and in 5 of 7 fights the killers were visible for 5 rounds. A visible enemy within 8 tiles should pre-empt camp attacks: either group up or leave.
3. **Target the damage dealer, not the closest.** Don't put basics into a shielded HoR. Prefer the enemy that is damaging us, then ranged carries (VV, Prism), then the lowest effective HP. (Fights 2, 4, 6.)
4. **Melee vs ranged: close with the dash or leave.** A melee champion taking hits from range 2-4 must dash in or walk out that turn, never idle. (Fights 5, 6.)
5. **Group, and fight together.** Allies within 2-3 tiles of a fight must join it: cast the stun on the attacker and use the reset. Our Ryth idled next to fights in 2 and 7.
6. **Use the double-hit every fight round**: basic, reset, basic for VV, Vendetta, Ryth and Marcella. They do this in nearly every round the reset is ready.
7. **Items: stack one stat per carry.** Strength on VV (Fish: 36 points by round 192); focus on HoR, Prism and Ryth (willow: 26 points on HoR). Our spread of strength and health plus Treasure/Jungle leaves us at 1/4 of their item points late. Kill gold is most of the gap, so items only partly fix it; but the focus build turns HoR's dash into a 600+ hit.

## Why the stand-ins don't reproduce this (for the sim)

The stand-ins built from TOP_TEAMS_RULES engage well but likely miss three things:
- **Concentration.** Their kills come with 2-4 champions together, arriving at once. A stand-in that engages per champion at 7-9 tiles fights 1v1s.
- **Stat stacking from round 1.** All strength on VV; all focus on HoR, Prism and Ryth. And a lead that compounds from kill gold.
- **The HoR shield as bait.** Our bot's closest-target rule pours damage into it; a stand-in with HoR that doesn't shield-and-soak loses that.

Fights won with no stat gap (before round 150) are all numbers: 89% 2+ hitters.

## Open questions / possibly broken

- **willow's recall every turn**: Prism and HoR cast `Recall` after their action every single round of fights 6 and 7. The rules say a channel blocks other actions until it finishes or is cancelled, with one start and one cancel per turn, so they presumably cancel at turn start, act, and recall again.
  - Possible gains: it costs nothing and gets them home automatically whenever they go 5 turns without acting or being hit.
  - Worth checking in the sim whether it also does something more (for example, being mid-recall when spawn recovery or damage is resolved).
- The Ren thorns (their attacker takes -20 when hitting our Ren) shows up in the dumps; it didn't change any outcome.
