# metab-v3 (private arena house bot) vs tune-3 on 01hooks and 01starvation

Data: `data/arena/` on main (4 replays, Oct 24 ~01:50 UTC); tune-3 is side A in `*_A` and side
B in `*_B`. Replayed through the official engine (`analysis/extract.js`). Results: 01hooks
33-1001 and 1001-33 (lost by rounds 1,213 and 1,284), 01starvation 0-939 and 920-0 at round 2,000.

## Drafts

- metab-v3: **Vesper Vale, Heart of Ruin, Marcella, Ryth** (+ Vendetta on 5-champion maps).
- tune-3: Vendetta, Vesper Vale, Tavi, Ryth (+ Ren).

## 01hooks (31x31, one central altar at (15,15)): metab-v3 holds the altar zone

| | tune-3 | metab-v3 |
|---|---|---|
| deaths / kills | 47-51 / 0-4 | 5-10 / 47-51 |
| captures (gems) | 26-34 (154-198) | 66-68 (836-880) |
| elk+gem captures (the rich groups ringing the altar) | 7-9 | 38-40 |
| tributes (median bag) | 1 (33) | 64-66 (11) |
| gems lost dying | 121-165 | 0 |
| altar locks placed | 0 | 1 (one game, round 287) |

- **Opening**: all four metab-v3 champions walk together from spawn straight to the altar
  zone (identical paths, at (13-17, 11-21) by round 40-60). They then spend **40-62% of their
  alive time within 4 tiles of the altar** for the whole game. Ours: 0-54%, mostly under 10%
  after round 400.
- **Farming**: they farm the four elk+gem groups around the altar (at (15,13), (15,17),
  (16,10), (14,20)) and the gold pairs next to it, then tribute immediately (median 11 gems).
  The altar is never more than a few steps away, so every capture is banked.
- **Fighting**: anything entering the zone gets killed. 33-39 of their ~50 kills are within 6
  tiles of the altar. Killers: Heart of Ruin, Marcella, Ryth, Vesper Vale. Our champions
  arrive one or two at a time (4 deaths in rounds 68-86 of hooks_A) and die with bags (7-9
  times, 121-165 gems that go to them).
- **No altar camping by locks**: 1 lock in 2 games. They camp with bodies, not locks.
- **Recall**: they recall often (69-77 times per game), at median 33-58% health. They don't
  die (5-10 deaths).

## 01starvation (80x80, altars (35,15) and (44,15)): tune-3 beats itself

| | tune-3 | metab-v3 |
|---|---|---|
| deaths | 33-39: monolith 20-25, champions 8, elk x4 group 5-6 | 4-14 |
| our attacks on monoliths | ~360 per game | 0 |
| captures | 5 | 97 (wolves 42-46, gem x4 27, gold x2 24-28) |
| tributes | 0 | 66-70 (median bag 14) |
| gems lost dying | 236-260 | |

- tune-3 spends its game on the monoliths at (25,3)/(54,3): about 360 hits and 20-25 deaths per
  game, and one capture.
- Its gem carriers die to the **elk x4 + gem x4 + gold x4 group at (39,16)**, which sits between
  the two altars (213 gems lost to it in one game), or to metab-v3 champions near the altars.
  It never completes a tribute.
- metab-v3 doesn't fight much here (8 kills). It roams the north band between the altars in
  a loose group (median spacing 16-21 tiles), farms **wolves, the gem x4 cluster at (39,11)
  and gold pairs**, never touches the elk x4 group (3 hits) or the monoliths, and tributes
  small bags. In our sim, tune-3 presumably gets those cheap camps itself; against metab-v3
  they're taken, and tune-3 falls back on monoliths and the elk x4 group.

## Where our gems go (answers)

- **Altar locks**: practically none (1 in 4 games).
- **Altar camping**: on 01hooks yes, by bodies: they live in the altar zone and kill whoever
  comes (most kills within 6 tiles). On 01starvation no.
- **Rich groups**: on 01hooks they own the elk+gem ring around the altar (38-40 captures to our
  7-9). On 01starvation they avoid the rich and dangerous ones (elk x4, monoliths) and farm
  cheap safe camps near the altars.
- **Our gems**: 01hooks: we die with bags (121-165 gems handed to them) and tribute once.
  01starvation: we never tribute; bags are lost to the elk x4 group next to the altars and to
  champions, and our time goes on monoliths.

## Stand-in opponent spec (for the tune line)

A policy reproducing metab-v3's behaviour on these maps:

1. **Draft** Vesper Vale > Heart of Ruin > Marcella > Ryth > Vendetta.
2. **Opening rush**: all champions go together to the altar zone (the closest altar to the map
   centre) and arrive by round ~40-60. Stay within ~3 tiles of each other until then.
3. **Altar-zone farming**: goals = camp spawns within ~8 tiles of an altar. Exclude monoliths,
   golems and groups with 3+ elks; farm wolves, gem clusters, gold, and elk+gem pairs. On a
   single-altar map this keeps them in the altar zone all game.
4. **Tribute immediately** once carrying >= ~10 gems (median bag 11-14); the altar is close.
5. **Zone defence**: attack any enemy in range (focus the weakest), and chase enemies within
   ~6 tiles of the altar. Don't chase beyond that.
6. **Recall** at ~35-55% health (recalls often, rarely dies).
7. **No altar locks, no wards** (1 lock in 4 games, 0 wards).

## What it implies for tune-3

- Don't walk into a held altar zone one at a time: arrive together or not at all. Compare
  local strength first (the theta rule).
- Monoliths: no solo or understrength attempts. On 01starvation tune-3 died 20-25 times to
  them per game.
- Treat camps adjacent to the altar route as hazards for carriers: on 01starvation the
  elk x4 group between the altars killed our carriers.
- When the cheap camps are taken, don't fall back on monoliths or elk x4. Take cheap camps
  further out, or contest the cheap ones near the altar.
