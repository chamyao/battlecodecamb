# Our live bot (tune-5, ladder v16) vs the ladder's top teams

Data: 10 unranked groups of 5 games (24 Oct, ~06:00 UTC) against prism best girl (#1),
Intercontinental Fish (#2), Univardisty of Shingtonwash (#3), :3 (#4), willow best girl (#5),
procless (#6), policy wonk (#7), Claudus Maximus (#8), Mite (#9) and vc?. Groups #2-#9 cover
all 40 maps. Replays in `data/top-teams-2026-10-24/`; tables in `analysis/top_teams_report.md`
(`analysis/top_teams.py`, `analysis/race_analysis.py`). We are rank 410 of 765.

**Result: 0-50.** No game was close. The best was 775-1015 vs vc? on 01the_farm; in 15 games we
tributed 0.

## The gap, per game

| | us | top teams |
|---|---|---|
| deaths | 17.8 | 1.6 |
| kills | 0.3 | 12.9 |
| damage to champions (official summaries) | 7.2k | 21.1k |
| gems captured | 347 | 983 |
| gems per capture | 11.8 | 21.5 |
| tributes (median bag) | 5.7 (20) | 24.2 (57) |
| gems lost dying | 140 | 11 |
| gold earned | 3.0k | 8.3k |
| distinct items per champion | 5.0 | 7.8 |
| share of time within 4 tiles of an altar | 11% | 22% |

## (1) What the top teams do that we don't

**Draft.** Every top team runs the meta core of **Vesper Vale and Heart of Ruin**, plus two or
three of Marcella, Vendetta, Prism, Ryth, Tavi, Willow:
- prism best girl: Prism, Marcella/Vesper, Ryth, HoR.
- Fish: Vesper, Vendetta, HoR, Cassi, Ryth/Varg.
- vc?: Vesper, Vendetta, Marcella, HoR, Ryth.
- policy wonk: Marcella, Vesper, Tavi, Willow, HoR.

Their kills on us by champion: Vesper Vale 191, Heart of Ruin 151, Vendetta 102, Marcella 74,
Ryth 49, Prism 33. Ours is Vendetta, Vesper, Tavi, Ryth, Ren every game.

**They win fights at even strength, early.** Max HP per champion is equal at round 100
(1,044 vs 1,071) and close at round 200 (1,137 vs 1,209), yet their first kill on us comes at
a median of round 175 (earliest round 18). The item gap (7.8 vs 5.0 items; HP 1,692 vs 1,343
at round 400) comes from the kills (100 gold each), not before them. At their kills, the
number of their champions within 5 tiles was 1 for 201 kills, 2 for 218, 3 for 151, 4+ for 73:
mostly one or two hunters, not a pack.

**We don't fight back properly.** In the 5 rounds before each of our 645 deaths to champions:
- the victim attacked an enemy champion in only 59%;
- it cast an ability on an enemy champion in only 16% (casts went to self or dash in 32%);
- it had started a recall, which damage cancels, in 23%;
- it attacked a camp in 18%;
- it did nothing logged (moving or idle) in 12%.

Their damage to champions is 3x ours.

**Farming and banking.** Their first capture comes at round 18-44 like ours. They capture rich
groups (21.5 gems per capture vs 11.8; monoliths 4,428 gems and golems 1,148 across the 50
games) and bank **big bags safely**: median bag 57, only 7-24% of their tributes with one of
our champions within 8 tiles. They can carry 50+ gems because we never threaten them.

**Altar control.** They spend twice our time in the altar zone (22% vs 11%). Claudus Maximus
(71% of its kills within 6 tiles of an altar) and Mite (64%) hold altars. Fish (20%) and
willow best girl (6%) kill elsewhere, on the route and at camps.

## (2) Does the v16 failure (carriers dying with bags) show up here?

Yes, but it's a symptom. Of their 645 kills, 308 (48%) were on carriers (232 with 1-24 gems,
76 with 25+). We lost 140 gems per game dying, and they tributed most of it. But **52% of our
deaths carried no gems at all**: they kill whatever they meet, and we lose even fights. Banking
earlier would save some gems; it won't fix 17.8 deaths per game.

## (3) What a "hunter" stand-in must copy to reproduce these losses

In order of importance:

1. **Draft the meta core**: Vesper Vale, Heart of Ruin, then Vendetta and Marcella (Prism or Ryth
   as fifth). Most kills come from VV, HoR and Vendetta.
2. **Engage any enemy champion in vision, not only carriers.** Attack when an enemy is within
   about 5-6 tiles, prefer low health or carriers, and chase a short distance: killers travelled
   a median 4-6 tiles in the 10 rounds before a kill. Don't wait for numbers: 1-2 hunters are
   enough against us.
3. **Use damage and stun abilities on champions**: HoR's stunning dash, Vesper's reset and dash,
   Marcella's stun-reset and damage, Vendetta's reset (kills refresh cooldowns). That's what
   makes their fights 3:1.
4. **Survive**: retreat or recall at moderate health, only when safe (they die 1.6 times per game).
5. **Farm rich groups and bank big bags (~40-60) when no enemy is within 8 tiles**; tribute
   immediately when one is.
6. **Start early**: be fighting by round ~150.

A stand-in that only hunts carriers, or only camps altars, won't reproduce this. The losses come
from winning every fight at parity.

## What it implies for us

- **Fight back**: when an enemy champion is in range, cast damage and stun abilities on it,
  focus it, and don't start a recall while in danger (move away first).
- **Draft**: test the meta core (VV + HoR + Vendetta/Marcella) against our current draft.
- Bank earlier when enemies are near (v16 analysis), and take richer groups.
