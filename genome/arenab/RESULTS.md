# Arena B lead: real-cambc gate runs (cambc 3.0.5 --release, 40 maps x both sides, vs v23 interpreted)

`genome/arenab/real_gate.sh CAND REF`. First turns have a 200k budget; normal turns 100k. Bar since ~20:00 Oct 24: wins >= 42/80 and no crashes (fuel numbers reported only). All three runs: 0 crashes.

| date (UTC) | runtime | candidate | wins /80 | first turns at 200k cap | normal turns >= 100k (cand / v23) |
|---|---|---|---|---|---|
| Oct 24 19:50 | genome/v0 46f8c7a | seed v23.genome | 50 | 110 (5 champs x 11 maps x 2) | 831 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | seed v23.genome | 49 | 110 | 497 / 0 |
| Oct 24 20:05 | genome/v0 0d931cf | directed/commit-mono (intel b3ac967) | 51 | 110 | 482 / 0 |

Maps where the first turn hits the cap: 00ambush, 00corners, 00expanse, 00lanes, 00road-of-riches,
01big-world, 01boss-battle, 01fracture, 01islands, 01starvation, 01yellow-brick-road (v23's own
first turn is 154-188k on these).
| Oct 24 20:35 | genome/v0 2356e26 | Arena B B318 (20:00 snapshot) | 49 | 110 | 583 / 0 |
| Oct 24 20:40 | genome/v0 2356e26 | Arena B B279 (20:00 snapshot) | 50 | 110 | 652 / 0 |
| Oct 24 20:45 | genome/v0 2356e26 (both builds) | B318 vs commit-mono (not v23) | 45 | — | — |
| Oct 24 20:50 | genome/v0 2356e26 | commit-mono (rebuilt) | 51 | 110 | 482 / 0 |

## Sim gate (a), `python3 -m genome.arenab.sim_gate` at genome/v0 2356e26 (seeds 94001-94013)

| genome | vs style-gconv1 (800) | vs seed | anchors (change vs the original on the same games) | vs commit-mono (400, seed 95001) |
|---|---|---|---|---|
| commit-mono | 0.566 | 0.562 | v7 +1.8, tune-v20-L1 +9.3, rall2 +5.5, metadraft +5.5 | — |
| B279 | 0.649 | 0.525 | +2.5, +10.3, +7.7, +6.8 | 0.562 |
| B318 | 0.647 | 0.637 | +0.8, +10.3, +8.2, +4.8 | 0.613 |
| B263 | 0.641 | 0.588 | +2.5, +12.0, +8.5, +6.5 | 0.512 |

## Runtime genome/fuel 82b5dcb (cheaper first turn, reserve() pass guard), vs v23 interpreted, 3 jobs

| candidate | wins /80 | first turns at 200k cap | normal turns >= 100k (cand / v23) |
|---|---|---|---|
| seed (genome/seed f739709) | 41 | 6 | 226 / 0 |
| B318 | 56 | 9 | 224 / 0 |

## Sim gate (a) vs the actual live bot before v25, tune-v20-L1c (genome/v0 2356e26 runtime, seeds 96001-96013)

| genome | vs tune-v20-L1c (800) | anchors (change vs L1c's own rate) |
|---|---|---|
| B318 (uploaded as v25) | 0.606 | v7 -0.7, tune-v20-L1 +11.5, rall2 +7.3, metadraft -1.7 -> PASS |
| B279 | 0.610 | +0.5, +11.0, +6.0, -0.7 -> PASS |
| B263 | 0.595 | -0.2, +6.8, +5.2, -2.0 -> PASS |
| commit-mono | 0.570 | +1.3, +4.7, +5.5, -1.5 -> PASS |

**Caveat (genome lead, 20:48):** the seeded runs above give the policy bots random seeds; deployed bots play
fixed seeds, so a deploy-faithful pairing has only 80 distinct games. With `--bot-seeds`
(`python3 -m genome.arenab.sim_gate ... --bot-seeds`), B318 vs tune-v20-L1c at 2356e26 is **38/80 (0.475)**:
anchors v7 +1.3, tune-v20-L1 +2.5, rall2 +3.7, metadraft -1.3. The arena gives 38/80 at db3f945 and 43/80 at
77da39c. Real cambc vs the v22 ZIP (old build): 46/80.

## B792 (Arena B run 13, gatekeeper pass) vs the live v25 build

| date (UTC) | build | vs | wins /80 | first turns at 200k cap (cand / ref) | normal turns >= 100k (cand / ref) |
|---|---|---|---|---|---|
| Oct 24 21:25 | B792 at genome/v0 212a505 | v25 = genome/v0 2013533 genome/candidates/B318.genome | 43 | 11 / 110 | 279 / 692 |

Gatekeeper (arena, 212a505, bot seeds): 47/80 vs B318 built at 212a505; anchors L1c +7, gconv1 -1, v7 +2, L1 +2, rall2 +3, metadraft +3.

## Band batches (intel, b1's plan: 10 teams +55..+145, 50 games)

| batch | live bot | record | note |
|---|---|---|---|
| b1 19:02 | v22 (tune-v20-L1c) | 15-35 (30%) | |
| b2 20:47 | v25 B318 | 18-32 (36%) | paired vs b1: gems +105 ± 49, lost on death -63, stuck spells 61 -> 4 |
| b3 21:28 | v26 B792 | 17-33 (34%) | paired vs b2: all within noise (deaths +1.5 ± 1.1) |
| b4 ~02:00 Oct 25 | v27 A61188 (Arena A) | 13-37 (26%) | paired vs b3: 4 flips to wins, 8 to losses (p ~0.4); worse vs early bankers (GLM5.3 3-2 -> 0-5); sim: rushbank 50/80 vs B792 59 |
| b5 ~03:50 Oct 25 | v28 a61188-mono | 18-32 (36%) | paired vs b4: 5 flips to wins, 0 to losses (p ~0.03); monolith deaths 1.86 -> 0.58, camp deaths -1.0, gems +39 ± 23 |

B792's sim edge over B318 (47/80, bot seeds) did not show in band games. The sim selection signal
(self-play + own past bots + stress anchors) predicts band results poorly (GENOME.md open point 4).

## a61188-mono (intel, v27 + mono-spare edit), real cambc --release, all builds at genome/v0 ca5180b

| vs | wins /80 | note |
|---|---|---|
| A61188 (v27 genome) | 42 | crashes 0; first turns at cap 12 vs 11; capped turns 318 vs 323 |
| B792 (v26 genome) | 49 | A61188 itself vs B792: 48 |
| B318 (v25 build, 2013533) | 49 | |

Sim (intel, bot seeds): 41/80 vs A61188; non-champion deaths great-wall 25 -> 15, shortcut 17.5 -> 9.5; 15 anchors all +0..+4.

Uploaded as **v28** at 03:43:47Z Oct 25 (bundle 8a921761..., genome/v0 568cbf5 genome/candidates/a61188-mono.genome). Validation: intel batch 5.

## arenaB-14 session-mutator relay: tops vs v28 (bot seeds /80, sim at genome/v0 ca5180b)

| genome | leg | vs v28 | anchor check (cand / v28) |
|---|---|---|---|
| B1460 | 1 | 40 | — |
| B1480 | 1 | 39 | — |
| B1543 | 2 | 42 | — |
| B1526 | 2 | 41 | — |
| B1573 | 2 | **44** | FAIL: B318 43/53, hunter 56/65; others level or up (A61188 44/41, exploit-353 54/50) |

## v28-emblem (intel; Treasure shards on one carrier until its emblem, then v28's plan)

Real cambc --release vs the v28 build (both at genome/v0 ca5180b): **45/80**, 0 crashes; capped normal turns 342 vs 382.
Sim bot seeds (intel): 52/80 vs v28; anchors -4 metadraft/farmer/lockall, +16 A61188, +7 rushbank/hunter-carry, others within ±3.

Uploaded as **v29** at 05:11:34Z Oct 25 (bundle 61743fda..., genome/v0 97194bf genome/candidates/v28-emblem.genome). Validation: intel batch 6.

## Solo farming vs builtin:idle (no opponent), bot seeds 80 games, sim at genome/v0 ca5180b

v29 can't reach 1000 gems in 2000 rounds alone on 8 maps (rushbait-v2 9, reverse-spiral 78, contest 200,
broken-curve 309, shortcut 586, boss-battle 787, elk-arena 792, gold-rush 880). Cause: m11 camp_goal is the
nearest small camp, with no weighing of gems vs gold, and monolith/golem groups are excluded.

v29-gg (genome/arenab/cand/v29-gg.genome) = v29 + gem-groups-cm's edit (nearest gem-paying group first):
- vs idle: elk-arena 792 -> 1008 gems (1887 -> 1314 rounds), gold-rush 880 -> 1001 (2000 -> 1428), broken-curve
  309 -> 502 (one of two games now finishes), yellow-brick-road 1086 -> 810 rounds; stampede worse
  (980 -> 800 gems, deaths 6 -> 21.5); rushbait/reverse-spiral/contest/boss-battle unchanged (their gems
  are in monolith/golem groups). Sum of rounds over 80 games: 53,218 -> 50,771.
- head to head vs v29: 39/80 (even), which is why h2h-only gates kept dropping it.

**Sim/real divergence (confirmed by the genome lead, Oct 25 ~05:58):** in every real genome bot, group_gems / group_gold /
group_reward return 0 (bot_api.cpp builds groups from sdk_map_camp_layout without storing rewards); the sim fills them.
So v29-gg plays identically to v29 in real cambc (vs a do-nothing bot: same rounds, same final 1008 gems / 2 kills /
19238 gold on elk-arena; real h2h 39/80 mirrored). Every gem-reward-weighted genome so far was sim-only. The fuel session
has the fix; re-test v29-gg in real after it lands.

After the fix (genome/fuel 0b1c4281, both bots rebuilt there), real cambc --release:
- vs a do-nothing cambc bot: elk-arena 1796 -> 1272 rounds, gold-rush 2000 -> 1460, yellow-brick-road 1522 -> 867;
  broken-curve, stampede, shortcut still 2000 for both.
- v29-gg vs v29 head to head: 39/80, 0 crashes; capped normal turns 292 vs 350.

## A81582-ringgg = A81582 (Arena A, gate pass vs v29) + intel's ring fix + weak-gem-groups-first

Sim, bot seeds (vs idle: total rounds / games short of 1000 / deaths per game):
A81582 100,601 / 10 / 6.16; A81582-ring 100,368 / 9 / 6.40; **A81582-ringgg 96,568 / 8 / 5.95**.
H2h: ringgg vs v29 45/80, vs A81582 39/80; ring vs v29 49/80.

Real cambc --release, all built at genome/v0 fd778fc (has the group_gems fix):
- **A81582-ringgg vs v29: 49/80**, 0 crashes (first turns at cap 30 vs 26; capped normal turns 473 vs 307).
- vs a do-nothing cambc bot, rounds to 1000 (2000 = not reached), A81582 -> ringgg: broken-curve 2000 -> 1258,
  elk-arena 1978 -> 1268, pilgrimage 1680 -> 1307, yellow-brick-road 969 -> 702, gold-rush 1359 -> 1432,
  starfish 1083 -> 1220, starvation 1650 -> 1864, stampede 1674 = 1674, contest/shortcut 2000 both.
  Sum over the 10 maps 16,393 -> 14,725.

**A81582-ringgg withdrawn:** in real cambc it loses pilgrimage, gold-rush and broken-curve 0-2 each vs v29. Gem-first starves
gold vs a real opponent (intel: pilgrimage gold 4,583 vs 14,258, gold-rush 3,474 vs 23,151).

## A81582-ringheal = A81582 + intel's two solo-farming bug fixes (no gem-groups)
- ring: altar rings exclude small-camp spawn tiles (bank walks no longer target a tile a living camp blocks);
- heal: r2 ignores enemies standing on their own spawn (hurt carriers next to an enemy spawn otherwise never heal).
Sim, bot seeds: vs idle total rounds 100,601 -> 99,212, games short of 1000 10 -> 5; vs v29 46/80, vs A81582 40/80.
Real cambc --release (genome/v0 fd778fc builds): **A81582-ringheal vs v29: 55/80**, 0 crashes (capped normal turns 450 vs 301);
plain A81582 vs v29: 50/80 on the same builds.

## Oct 25 06:2x: search passes vs v29, checked against v30 (A81582-ringheal)
Sim, bot seeds, /80 vs A81582-ringheal: A81615 37, A91640 40. With the ring+heal fixes grafted on
(ring lines in v2, r2 heal uses i22): A81615-rh 38, A91640-rh 40. Not forwarded; search told to
regate vs v30 once it is live.

## Oct 25 ~06:50: A-8 family dies to monoliths solo; A81582-ringheal-mono (cand/)
Real cambc vs A81582-ringheal (v30): A91640-rh 40/80, A81615-rh 35/80 (both FAIL; not forwarded).
00great-wall solo vs idle (sim): v30 1750/1975 rounds, 38/45 deaths; v29 1448/1345, 11/12.
Bisect (one gene swapped at a time, both directions): v30's a0 and r14 put into v29 bring the deaths back
(34/33 and 29/42). The A-8 lineage predates intel's monolith fix (camp-walk attacks, r13/r14 and s14 only on
farmable camps, i1). graft.py `mono` onto v30 = A81582-ringheal-mono:
- great-wall solo 1313/1267 rounds, 16/13 deaths; all 80 solo: rounds 98956 (v30 99212, v29 106435), deaths 356 (v30 522).
- sim h2h /80: 40 vs v30, 50 vs v29.
- real cambc: 45/80 vs v30 (0 crashes), 57/80 vs v29 -> PASS. Next upload after v30.

## Oct 25 ~07:20: v30 + mono + intel rhm (contest) + intel gg6 (gem-first after 6 buys)
All on A81582-ringheal-mono (cand/). Real cambc /80, 0 crashes everywhere:
| cand | vs rh-mono | vs v30 (ringheal) | vs v29 | sim h2h vs v30 | solo rounds / deaths |
|---|---|---|---|---|---|
| rh-mono-rhm | 44 | 48 | - | 40 | 98867 / 364 |
| rh-mono-gg6 | 45 | 46 | - | 42 | 97569 / 371 |
| rh-mono-all (both) | 49 | 51 | 62 | 42 | 97417 / 379 |
(v30 solo: 99212 / 522.) The gg6 and rhm diffs overlap in context, so rh-mono-all was built by applying
rhm's three edits (MONO_ONLY global, its v2 line, r15) to rh-mono-gg6. gg6 needs group_gems: build at or
after genome/v0 fd778fc. Recommended next upload: A81582-rh-mono-all.

## Oct 25 ~07:45: tune-B constants (found on v29) ported to rh-mono-all
| variant | sim /80 vs rh-mono-all | real /80 vs rh-mono-all |
|---|---|---|
| cash4 (r5 `g < 4`) | 43 | 44, 0 crashes |
| bag6 (r11 `g >= 6 and altar_eta() <= 3`) | 39 | 42 |
cash4 is a small, insignificant gain (~+4/80); kept as cand/A81582-rh-mono-all-cash4 to ride along a later upload.
01shortcut solo (sim, rounds/deaths): v29 2000/2000 (9/7), ringheal 2000/2000 (30/30), rh-mono 1584/1709 (5/6),
rh-mono-all 1563/1709 (4/6): mono does not regress shortcut once the ring fix is present.

## Oct 25 06:39: v30 = A81582-ringheal live; rh-mono-all is the v31 candidate (genome/v0 7f5de79)
- Search, solo-farm vs v30 (53,100): rh-mono-all 49,654, passes (warns: 01boss-battle +813, 01gold-rush +216).
  ringheal-mono 52,774, blocks on boss-battle, gold-rush, elk-arena. The 01shortcut "+522" was raw A81582's
  missing ring fix, not mono.
- Search, v30 regates of A81615/A91640/A81582, raw and +mono: all six blocked by solo-farm.
- Intel, paired rows for rh-mono-all vs ringheal's: net +9, no significant drop (rall2 +6, p 0.07); monster deaths 6.53 -> 4.74.
  Regression: boss-battle +534 rounds (only altar behind a monolith). Intel is building a narrow exemption.

## Oct 25 ~07:00: A81582-rmab (intel boss-battle exemption on rh-mono-all)
Real /80 vs rh-mono-all: 41, 0 crashes (near mirror; one-map change). Intel: boss-battle real 2-0, solo 1974 -> 1423 rounds.
Safe to ride along with the v31 upload.

## Oct 25 06:51: rh-mono-all confirmed as v31 (after batch 7)
Genome lead real 51/80 vs v30 (same as ours). Search full gate vs v30: sim h2h 42 (bar 43), solo-farm pass, paired anchors
no blocks (v29 55 vs 44, v28 56 vs 46, A61188 59 vs 49). rmab held for its own version after batch 8.
Intel: gold-rush +216 is mono (centre monolith group of ~24 gold clusters in its range); accepted trade-off.

## Oct 25 ~07:20: "B1782" gate pass vs v30 = intel A81582-gg6 (directed insert in leg 6)
B1782 sha 80890c76 is byte-identical to genome/intel/directed/A81582-gg6; B1783 = gg3. Relay top B1796 (gg6 lineage),
real /80 vs rh-mono-all: 37 raw, 41 with mono (sim 34, 37). Not forwarded. Leg 6 asked to insert rh-mono-all and rmab.
exploit-3 stopped at $9.15 when API credits ran out (06:50Z).

## Oct 25 07:15: band batch 7 (v30), paired with b6
21-29 (b6 20-30). Stuck champion-rounds -63 +- 48 (heal fix live); monolith deaths +1.7 +- 0.8, camp deaths +2.0 +- 0.7
(shortcut 0-2 at 12 monolith deaths/game, great_wall 35). elk_arena still no-bank vs real opponents. v31 = rh-mono-all next.

## Oct 25 07:16: v31 = A81582-rh-mono-all live (bundle e4932580)
Gem gate after 3 buys instead of 6, on v31: sim 39/80, real 39/80 vs v31 (0 crashes). Not better; keep 6 unless b8 shows side-A elk_arena losses.

## Oct 25 ~07:50: Arena B leg 6 done (1881 births, solo filter on); B1873 beats v31
Top 3 relay genomes (all with the monolith fix) vs v31 = rh-mono-all, sim / real /80:
B1881 39 / 39, B1873 37 / 47, B1872 43 / 40. All 0 crashes.
B1873 (B1850 + kill-shot fight outranks the pass-through bank: rule 165 + r_killshot): real 49/80 vs v30, 56/80 vs v29;
solo vs idle 95,846 rounds / 362 deaths (v31 97,417 / 379). Sim undershoots it by 10/80. Sent as the v32 candidate.

## Oct 25 07:36: B1873 full gate vs v31 (search)
Sim h2h 37 (fails, real 47). Paired anchors: 0 blocks (lowest p 0.29). Solo-farm: total better (48,980 vs 49,654) but a
per-map block on 01gold-rush +417 and 00contest +333 (my runs: contest side B 400 vs 600 gems, gold-rush 2000/1927 vs
1581/1627 rounds; it has the rhm rule). Going up as v32 on real; watch gold-rush/contest in batch 9.
