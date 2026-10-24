# Ladder losses: v16 (tune-5), 24 Oct 2026

Data: our ranked games created from 03:45 UTC (tune-5 went live at 03:44) to 04:42: **30
games, 11-19**. Replays in `data/master-v16-2026-10-24/`; tables in `analysis/v16_race.md`
(`analysis/race_analysis.py`) and `analysis/v16_report.md` (`analysis/v6_report.py`).

## Summary

We are out-raced mostly because **our carriers die with big bags and the gems go to the
opponent**. Our tributed total flatlines early in about half the losses. Secondary causes:
opponents take richer groups (golems, monoliths), the old monolith and approach-tile problems
persist on three maps, and the meta comp (vc?) wins every fight.

| per game | us in losses | them in losses | us in wins | them in wins |
|---|---|---|---|---|
| deaths | 20.3 | 12.6 | 6.7 | 16.2 |
| kills | 3.9 | 15.0 | 8.8 | 3.8 |
| gems lost dying | 204 | 87 | 84 | 41 |
| tributes | 13.4 | 36.0 | 36.8 | 28.4 |
| median bag | 35.5 | 34.0 | 24.6 | 18.3 |
| gems captured | 624 | 930 | 1,044 | 511 |
| gems per capture | 14.1 | 22.1 | 12.2 | 13.0 |
| gold earned | 4.7k | 6.2k | 11.4k | 4.6k |

16 of 19 losses end with the opponent reaching 1,000; 3 on the gem tiebreak at round 2,000.

## Causes, ranked

### 1. Carriers die with bags to enemy champions (most losses; dominant in about 10)

- In the 19 losses we died with gems 213 times and lost **3,364 gems to enemy champions**:
  1,917 away from altars (on the way, or at camps) and 1,447 within 6 tiles of an altar. Those
  gems become theirs.
- Our tributed curve flatlines while we keep capturing: `00gemfight` vs Ely2sh, 132 from round
  250 to the end, with 74 captures; `00elkring` vs Mein Kraft 135 flat; `00eight` vs vc? 76 flat
  from round 500; `00interlock` vs vc? 244 flat from 750; `00quadrants` and `01broken_curve` vs
  newbies, 123 and 192 flat from 500; `01starfish` and `01starvation` vs newbies, 0.
- We tribute rarely (13 per game in losses vs their 36) with big bags (median 35.5). tune-2's
  "bag >= 25" (carried into tune-5) means a carrier walks around with 25+ gems, and on maps
  where the enemy roams or holds the altar zone it dies before banking. In wins our bag was 25
  and we tributed 37 times.
- Kills in losses: 3.9 per game for us vs 15.0 for them.

### 2. vc? (0-5): the meta comp wins every fight

vc? drafts **Vesper Vale, Heart of Ruin, Marcella, Vendetta (+ Ryth)**, the ladder meta. Against
our Vendetta, Vesper, Tavi, Ryth, Ren:

| map | gems | our deaths / their deaths | our kills | gems we lost dying |
|---|---|---|---|---|
| 00eight | 76-1007 | 46 / 4 | 1 | 239 |
| 00gem_fields | 499-1011 | 24 / 6 | 5 | 256 |
| 00gemfight | 659-1032 | 30 / 8 | 7 | 452 |
| 00interlock | 244-1010 | 22 / 1 | 1 | 212 |
| 00rushbait_v2 | 907-1011 | 8 / 2 | 1 | 128 |

vc?'s gems per capture are 13-33 vs our 8-14, but fights decide it: 130 deaths to 21 over five
games. Most of our deaths come away from the altar (on the route or at camps). It's not altar
camping (vc? spent 6-29% of its time in the altar zone; no locks).

### 3. 00gemfight (both losses): altar zone held, carriers with big bags walk in

- vs Ely2sh, 132-1014: we captured 74 times (gems per capture 7.7) but tributed 132 gems, all
  before round 250. Ely2sh spent 32% of its time in the altar zone vs our 10%, made 12 of its
  kills near the altar, and **260 of the 423 gems we lost dying were lost near the altar**.
  Our median bag was 46.
- vs vc?, 659-1032: 30 deaths, 452 gems lost dying (175 near the altar), 14 of vc?'s kills near
  the altar.
- So on 00gemfight the opponent sits on the altar approach, and our bag >= 25 rule sends
  carriers in late and alone with big bags.

### 4. Richer groups for them (all losses)

Gem sources in losses: theirs gem groups 14,050, golems 1,272, monoliths 1,228; ours gem groups
8,762, wolves 1,548, golems 624, monoliths 400. Their gems per capture: 22 vs our 14.

### 5. Old map problems, still present (4 losses)

- **Monolith deaths**: `00lost_world` 25 (341-1001), `01starvation` 19 (0-935),
  `01broken_curve` vs Mein Kraft 14 (764-897), `00contest` 10. The "scoreless -> monolith"
  fallback the tune line is fixing.
- **Idle on 01broken_curve**: 1,519 and 1,235 idle rounds in the two losses there (the
  approach-tile freeze from `docs/LADDER_LOSSES_V6.md`, or a relative of it).
- **4 lock stalls** flagged (00gemfight vs Ely2sh, 00elkring, 00quadrants vs newbies,
  01broken_curve vs newbies). These overlap with cause 1: the carrier dies before reaching
  the altar, rather than freezing at it.

## Suggestions

1. **Bag rule by risk, not a fixed 25.** Tribute when the bag is >= 25 **or** an enemy
   champion is visible or near (`enemies_within(r) > 0`), **or** when farming far from an altar
   with a bag >= 10 and `local_strength` is unfavourable. The threat banking already being
   tuned (T240) is a form of this; extend it to visible enemies. In wins our median bag was 25;
   in losses 35.5 with 3x the gems lost.
2. **Carry gems in pairs** on maps where the enemy roams or holds the altar zone: a carrier
   with a bag walks with an ally (`allies_within`) or waits for one.
3. **Draft vs the meta**: we lose every fight to VV/HoR/Marcella/Vendetta. Screen drafts against
   vc?'s composition in the mirror league (the draft is the biggest lever we've found).
4. **Value-weighted goals** (`group_gems` / `rich_spawns` exist now): they get 22 gems per
   capture to our 14.
5. Finish the starvation/monolith fix (tune line) and re-check 01broken_curve idling in the
   simulator.
