# Why v3 still loses: second ladder analysis

Data: v3's ranked games created after 17:05 UTC on 23 Oct 2026. There are **35 finished
games, 13-22**, against ShadowKnight, Quantum Elk, Brr Brr Battlecode, Kuchh_bhii, Sheeesh---,
hey it's me it's verity and ohhhhhh caml. Replays are in `data/master-v3-2026-10-23/`. Tools:
`analysis/fetch_mine.py` (re-run to add games), `analysis/v3_analysis.py`. The first
analysis is in `docs/LADDER_LOSSES.md`; v3 is `policies/v3.policy` on `interp/v0`.

## What changed since fs-1

The camp-death problem is mostly fixed. In losses, our deaths are now **418 to champions** vs
171 to camps (fs-1: 103 vs 324). Per 1,000 rounds in losses we die 16.0 times vs their 6.8,
and they kill 11.6 of ours vs our 4.0.

## How games end

| ending | v3 W-L |
|---|---|
| a side reached 1,000 | 6-10 |
| round 2,000, more gems tributed | 7-8 |
| round 2,000, 0-0, decided on lifetime gold | 0-4 |

In losses our tributed total flattens: median 115 at round 1,000, 158 at 1,250, 183 at 2,000.
Theirs keeps climbing (352, 535, 899). In wins, ours climbs (384, 513, 968). Most losses are
not slow races: our scoring *stops*.

## Causes, ranked by games cost (22 losses)

### 1. Altar access: about 8 losses

- **Altar locks freeze us (4 losses, 1 partial).** v3 targets `minus(altars(), locked_altars())`.
  When enemy locks cover every altar we can reach, the target set is empty,
  `move_towards(closest(...))` does nothing, and champions carrying gems end every turn
  without acting. Our tributed total stops exactly at the first effective lock:
  - `00collision` vs Brr Brr: lock at round 285, at 153 gems → 153 at the end. The other altar
    is unreachable from our side. 4,986 idle rounds.
  - `01concentrated_wealth` vs Kuchh_bhii: locks at 360 and 449 (both altars), 19 → 19.
  - `00eight` vs Kuchh_bhii: lock at 446 on the map's only altar, 164 → 164.
  - `00interlock` vs Brr Brr: four locks (216-1010), 42 → 109.
  - Partly `01corridors` vs Sheeesh---: lock at 803, 72 → 202, 2,083 idle rounds.

  The engine converts a tribute attempt at a locked altar into an attack on the lock, which
  breaks after 5 hits, and the interpreter's `tribute()` passes straight through. Where
  another altar stays open we win anyway (5 games vs Sheeesh--- and Kuchh_bhii with locks).
- **No reachable altar (2 losses, both 0-0 on gold).** `01boss_battle`, twice: the only altar
  sits behind a monolith (holes and walls on its other sides). v3 skips monoliths, so champions
  pick up gems and then stand still (7,534 and 7,208 idle rounds), and we lose the gold
  tiebreak (852 vs 2,138; 1,287 vs 6,987).
- **Altar inside a monolith's range (1 loss).** `00great_wall` vs ohhhhhh caml: 38 of 55 deaths
  were to a monolith within 3 tiles of the altar we tribute at (monolith range 5).

### 2. Losing fights to champions: about 7 losses

`00stampede` vs Kuchh_bhii: 55 deaths to champions, 0-0, lost on gold 4.0k vs 16.8k.
`00contest` x2: 39 and 71 champion deaths; 112-139 captures but **zero gems** (we only farm
the gold clusters at the edges; the gem camps are in the contested middle), 0-0 / 0-600.
`00corners`, `00packs`, `00interlock` vs ShadowKnight, `00elkring` vs ShadowKnight: 15-28
champion deaths each, against 1-15 for them. Most of our champion deaths come from above 50%
health five rounds earlier (`00stampede`: 42 of 55): we start or accept fights we can't win,
and the 30% retreat trigger is too late against burst damage. v3 still attacks any enemy in
range regardless of numbers or health.

### 3. Slower races: about 4 losses

`00lanes` vs Brr Brr 884-1007, `00gem_fields` 795-1008, `01islands` 877-1017, `00quadrants` vs
verity 657-1003. Our median tribute bag is still 7 gems vs their 15-18. Opponents earn 2.1x our
gold per round in losses and spend 2.1x as much.

### 4. Other (3 losses)

`01starvation` x2: still 33 elk deaths in one game. `01the_farm`: 0-14, one capture, 1,599
idle rounds (not investigated further).

## Tiebreaks

- **Gold tiebreak (0-4).** All four 0-0 games were ones we could not score in: no reachable
  altar (`01boss_battle` x2), or champions dying (`00stampede`, `00contest`). The opponents'
  gold was 2.5-4.2x ours. When tributing is impossible, we should farm gold safely, since
  lifetime gold decides it.
- **Gem tiebreak (7-8).** Losses here are the frozen-by-lock games (`00collision`,
  `01concentrated_wealth`, `01corridors`) and fight-heavy maps (`01starvation`,
  `00great_wall`, `00contest`). Wins came from steady scoring (median 968 by round 2,000).

## Top changes

1. **Altars.** (a) Target all altars, locked or not: tribute at a locked altar attacks the
   lock. Replace `minus(altars(), locked_altars())` with `altars()`. (b) Prefer altars
   outside monolith range: `minus(altars(), ring(monolith_tiles(), 5))`, falling back to all
   altars if empty. (c) If no altar is reachable (`01boss_battle`), farm gold for the
   tiebreak or take the monolith with 3+ champions. (d) Consider placing our own locks:
   three of these opponents do, and it froze us. Worth about 7-8 of 22 losses.
2. **Pick fights.** Don't attack champions when `allies_within(4)` is less than the number of
   visible enemies, or when our `unit_health_frac` is lower than theirs. Retreat from enemy
   champions earlier than from camps (`in_danger()` with enemies near and health < 60%).
   Avoid contested centres when carrying gems. Worth about 7 losses, and the gold-tiebreak
   games.
3. **Bigger bags and more gold.** Now that deaths are down, re-test tributing at ~15 gems
   (opponents' median 15-18) and spending on Treasure early. Worth about 4 close races.

## Missing blocks this points to

- `reachable_altars() -> TileSet`: altars with a walkable adjacent tile from here (static map
  plus alive camps), so policies can detect `01boss_battle`-type maps and switch to gold or
  monoliths.
- `enemy_locked_altars() -> TileSet` (vs `locked_altars()`, which may include ours): keep
  them as targets but know a lock is there.
- `buy_consumable(altar_lock)`, `place_altar_lock(Tile)`: opponents lock our altars; we
  don't lock theirs.
- `enemies_within(Num) -> Num` (alongside `allies_within`), and `visible_enemy_dps() -> Num`
  to judge a fight before it starts.
- Still open from the first analysis: `group_hp/group_dps/my_dps` (camp fights such as
  `01starvation`) and `altar_reachable()` (subsumed by `reachable_altars()`).
