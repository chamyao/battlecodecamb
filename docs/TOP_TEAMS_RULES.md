# How the top teams fight: decision rules per champion

Source: the 50 unranked games of tune-5 vs the ladder's top 9 + vc? (`data/top-teams-2026-10-24/`,
`docs/TOP_TEAMS.md`), from **their** side. Tool: `analysis/fight_rules.py`; outputs in
`analysis/top_teams_rules_all.md` (all 10 teams, 1,317 engagements) and
`analysis/top_teams_rules_focus.md` (vc?, Intercontinental Fish, willow best girl: the route and
camp killers; 510 engagements). The two agree closely; the numbers below are all-team medians,
with [25th-75th percentile].

**Engagement**: one of their champions damages one of ours after >= 10 rounds without damaging
any; it ends after 6 rounds without damage. Distances are Chebyshev, measured at the end of the
previous round (so a melee hit can show as range 2 when the attacker stepped in that turn).

## Rules shared by every top champion

1. **Engage trigger: our champion within vision, while they are healthy.** At the first hit their
   HP is 0.90-1.00 (median), the target's 0.68-0.87. They close from 10-11 tiles to first-hit
   range over about 10 rounds: 11 [8-14] tiles 10 rounds before, 7 [5-9] 5 rounds before. So they
   start walking toward a visible enemy at about 7-9 tiles (vision is 8) and arrive within ~5
   rounds.
2. **Odds: 2v1 by default.** At the first hit there is 1 [0-2] other of their champions within 5
   tiles and 1 [1-2] of ours. They take fights where they have at least equal numbers, often
   one more, but don't wait for a full group.
3. **Target = the closest visible enemy** (87-94%). It's usually also the lowest-HP one (71-78%),
   and a carrier about half the time (42-54%; Prism and Willow 71%). Rule: attack the closest; on
   ties, the lowest HP; carriers are not sought out specially.
4. **Open with the ability, on the first hit turn** (rounds from the first hit to the first cast:
   0 for every champion). The opening ability is the one that reaches furthest or stuns: dash
   for melee divers, damage/stun spell for casters.
5. **Short chase.** Tiles moved during an engagement: 0-2 for most champions; 3-6 for kills by
   Heart of Ruin and Ryth. They don't follow a retreating target across the map.
6. **Disengage while still healthy.** Their HP at the end of an engagement is 0.77-0.94. They
   recall within 10 rounds after 37-47% of engagements (Prism 82%), i.e. they reset rather than
   fight on hurt. They die 1.6 times per game.
7. **From fog or bushes about 20% of the time** (Cassi 40%): not the main mechanism.
8. **Where**: 62% of engagements happen in **their** half of the map. The first fight of a game
   comes at round 86 [34-252], 78% of the time in their half. Our champions walk into them
   (farming their side, or on the way to altars), and they defend their area.

## Per champion

### Vesper Vale (285 engagements, kills 50%)
- Engage: first hit at range 4 [3-4], ranged basic attack.
- Opening: basic attack then attack reset then basic attack (`B > S0 reset > B`, 45%), or reset
  first (19%), or dash in then basic (17%). So **two basic attacks on the first turn** via the
  reset.
- Keeps range 3 (60% of basic attacks at 3, 16% at 2, 11% at 4). It kites; it doesn't close to melee.
- Chase 0 [0-2] tiles. Ends at HP 0.84; recall within 10 rounds 44%.
- Items by round 200: Treasure Strength (1.6 shards), Jungle Strength (1.0).

### Heart of Ruin (242, kills 52%)
- Engage: **dash in** from 3 [2-4] tiles (60% open with slot 1, the stunning dash), then basic
  attacks: `S1 dash > B > B` (44%), or `B > B > B` (19%). Shield (slot 0) is rarely the opener (5%).
- Fights in melee (74% of attacks at range 1). Engagements last 7 [3-13] rounds, the longest.
  Chases 4 [2-9] tiles on kills.
- Ends at HP 0.84; recall 37%.
- Items by round 200: Treasure Health (1.1), Jungle Focus (1.0).

### Vendetta (144, kills 58%, the best)
- Engage: dash in from 3 [2-4] (53%: `S1 dash > B > B`), or basic then reset then basic
  (`B > S0 reset > B`, 42%).
- Melee (62% at range 1). Kills reset its cooldowns, so it chains into the next target.
- Chase 1 [0-4], 3 on kills. Ends at HP 0.77, the lowest: it fights deepest. Recall 47%.
- Items by round 200: Jungle Strength (1.0), Jungle Health (0.9), Treasure Health (0.8).

### Marcella (235, kills 28%)
- Engage: **damage spell (slot 1) from range 4** (89% of openings). Often that is the whole
  engagement (`S1` alone, 54%: poke and leave), or `S1 > B > S0 reset` (30%) when it follows up
  into melee (range 1-2).
- Starts at full HP (0.96). Engagement 1 [1-8] round. Chase 0.
- Recall 40%. Items by round 200: Jungle Strength (1.1), Treasure Strength (0.8).

### Ryth (186, kills 22%)
- Engage: **AoE stun (slot 0) from range 4 [3-5]** (86% of openings), then basic, then reset
  (`S0 > B > S1`, 36%), or just the stun (46%).
- 2 [1-3] allies within 5 at the first hit, the most of any champion: it opens fights for the team.
- Melee follow-up (64% at range 1). Kills come after chasing 6 [3-8] tiles.
- Items by round 200: Treasure Health (1.0), Jungle/Durability Health.

### Prism (56, kills 46%)
- Engage: **AoE (slot 1) from range 5 [4-6]** (55%) or the damage-stun (slot 0, 30%), often both
  (`S1 > S0`). Basic attacks at range 3 (78%).
- Starts at full HP (1.00), targets carriers (71%), ends at HP 0.94, and recalls within 10 rounds
  after 82% of engagements: **burst once, then go home**.
- Items by round 200: Durability Health, Monster Focus/Health.

### Tavi, Cassi, Willow (smaller samples)
- Tavi (72): stun-damage (slot 1) from range 4 (76%), then reset and basic; range 3-4.
- Cassi (42): stun (slot 1) from range 5 (74%), then damage (slot 0); range 3; 40% from a bush;
  2 allies nearby.
- Willow (31): attack reset (slot 1) then basics from range 4; targets carriers (71%).

## Opening and items

- First engagement at round 86 [34-252], usually in their half (78%), most often by Vesper Vale,
  Marcella, Vendetta or Prism. Before that they farm their own side (first captures at round
  18-44, `docs/TOP_TEAMS.md`).
- Items by round 200 are few (1-3 shards per champion). The fights are not won by an early item
  lead: Treasure first (Strength for VV/Tavi/Willow, Health for HoR/Ryth/Vendetta), then Jungle.
  About half the games buy an altar lock by round 200.

## A hunter policy in our language (sketch)

```
let enemy = closest( enemies_visible() )        # target: closest, tie -> lowest HP
if exists(enemy) and health() > 0.8 * max_health() and enemies_within(5) <= allies_within(5) + 1:
    if distance(position(), unit_position(enemy)) <= 8:    # engage at vision range
        # open with the reach ability on the first hit turn
        if i_am(champ_heart_of_ruin()) or i_am(champ_vendetta()): cast dash toward enemy when <= 3
        if i_am(champ_marcella()): cast slot 1 (damage) when <= 4
        if i_am(champ_ryth()): cast slot 0 (aoe stun) at enemy tile when <= 4
        if i_am(champ_prism()): cast slot 1 (aoe) when <= 5, then slot 0
        if i_am(champ_vesper_vale()): basic, cast slot 0 (reset), basic; stay at range 3
        attack(enemy); chase at most ~3 tiles (6 for HoR/Ryth on a low target)
if in an engagement and health() < ~0.75 * max_health() and no kill in reach: walk away, recall when safe
```

The parts that matter most: engage early at vision range with numbers, open with the
ability on the first turn, target the closest, and leave at ~0.8 HP instead of trading down.
