# arenaZ-17: cull fix (Cham: "ok fix it", Oct 25)

Question: does culling the lowest-rated genome (instead of, in practice, the parent of a same-species
newborn) make the arena train better?

## The bug

genome/search arena.py cull(), since 7e40b6f:
`pool = strict or [m for m in ok if species has > 1 member] or ok`, then the lowest mu in pool dies.
With 24 members in ~24 species the strict pool (species above --min-species = 2) is almost always empty.
A newborn joins its parent's species, which becomes the only 2-member species; the newborn has fewer
than --min-games games, so the parent is the only candidate and dies whatever its rating.
arenaZ-10: 442 of 453 deaths took the relaxed rule. 152 were the parent of the newest same-species birth.
In the second half the median victim had mu 34.7 while the top was ~37 (53 victims >= 36, 14 >= 37).
Side effect: same-species crossover partners are rare, so crossover by gene ID almost never fires
(arenaZ-10: 0 gene-ID crosses, 84 crossovers by meaning).

## The one change

`--cull min-mu` (genome/search e837b50e; patches/cull-minmu.patch for 7e40b6f): if the strict pool is
empty, the lowest-rated eligible genome dies (eligible = >= --min-games games, species not protected).
The default `--cull legacy` is the old rule, unchanged.

## Runs

The writer and everything else as arenaZ-15 (7e40b6f + batch-mutate.patch, runtime 648bafd, starter seed
and only anchor, batched Opus edit mutations, --max-births 475):

| run | cull | rng salt |
| --- | --- | --- |
| arenaZ-15 (done, control) | legacy | 0 |
| arenaZ-17a | legacy | 1 (replicate of the control) |
| arenaZ-17b | min-mu | 0 |
| arenaZ-17c | min-mu | 1 |

Cost about 3 x $18 from the Arena A reserve ($98).

## Measures (fixed before running)

- Primary: panel best and top-3 mean (11 held-out opponents, /880) at each 100-birth milestone and at the
  end; min-mu arms vs legacy arms.
- Selection: share of deaths by rule; victim mu rank among the living at death; how long the top-rated
  member survives; species count and size.
- Operators: share of crossovers by gene ID vs by meaning; acceptance per operator.
- Decision: adopt min-mu if both min-mu arms end above both legacy arms on the panel best (or the means
  differ by more than the legacy replicate spread). Otherwise report "no measurable effect".

## Update 07:10 UTC: API credits ran out; arenaZ-18 on session writers

API credits ran out at 06:50, with Z-17a/b/c at 357 / 351 / 415 births. They were stopped. Each gets a final panel
milestone on its final population, and they are compared at their stopping points.

arenaZ-18a-d repeats the test with session writers (no API spend). Setup: setup_z5.sh (7e40b6f + file queue,
648bafd) + cull-minmu.patch, --births-in-flight 8, --max-births 475, one continuous session each. Mirrors go to
arenaa/z18{a,b,c,d}-mirror; panels end on queue/DONE.

| run | cull | session |
| --- | --- | --- |
| Z-18a | legacy | session_0124AdjXpbfxCvSQsScx2yEw |
| Z-18b | legacy | session_01ULhgKDzHAr3dGhyoD3U8YN |
| Z-18c | min-mu | session_019MLHiGCXuWrwBfEstUEbeR |
| Z-18d | min-mu | session_01CS5TjBxC3g5RcfD4n5gHHm |

The rng-salt patch does not apply on the queue patch and is not needed: session replies differ run to run, so each
run is its own replicate. The measures and the decision rule are as above.

## Z-17 result (07:20 UTC; stopped early when the API credits ran out)

| arm | stop | best | top-3 | rank 1-3 culled | mean victim rank (of ~25) | gene-ID crosses | species alive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Z-15 legacy s0 | 475 (207 at b405) | 207 | | 32 | 18.4 | 0 | 24 |
| 17a legacy s1 | 407 | 200 | 183.0 | 33 | 18.3 | 0 | 24 |
| 17b min-mu s0 | 411 | 190 | 167.3 | 8 | 22.2 | 9 | 19 |
| 17c min-mu s1 | 463 | 194 | 190.3 | 12 | 20.6 | 27 | 18 |

Mechanism confirmed: min-mu stops culling the leaders and lets species grow, so crossover by gene ID returns.
Strength: the decision rule is not met (min-mu 190 / 194 vs legacy 200 / 207 at ~400 births). Verdict: no
measurable effect on panel strength at this length. Caveats: the runs were stopped early, and births after
06:50 were tunes and gene-ID crosses only. Z-18 (session writers) is the second test.

## Z-18 cancelled (contaminated), Z-19 restarted with isolation (08:30 UTC)

Z-18a m1 was 517 at b112, far above anything earlier. The check: Z-18a's writer added A61188's exact draft table
(pick_value Vendetta 6 / Vesper Vale 5 / Tavi 4 / Ryth 3 / Ren 2) at Z15, and its shop sequence uses A61188's items.
The starter has neither. (Correction 08:55: my first count matched any VESPER_VALE mention. The exact-table audit finds the copy only in Z-18a; Z-18b's draft is its own.) The writers had
read evolved genomes in the repo (genome/candidates etc.), so Z-18 does not measure training from the starter, and
the contamination is uneven across arms. Cancelled.
Z-5's Z392 and the relay's Z400 do not carry the table (their draft and shop genes are their own).

arenaZ-19a-d: same design plus an explicit isolation rule (ideas only from the requests, feedback, GameRules,
LANGUAGE; no other genomes, policies or runs). After the runs, check the genomes for A-line fingerprints.

| run | cull | session |
| --- | --- | --- |
| Z-19a | legacy | session_013q8Ddw7WvTHC2oEBWtWPne |
| Z-19b | legacy | session_01R9v74DAjVMtZPr6b1Yk49e |
| Z-19c | min-mu | session_01KiAQyz3ExQJnqUuMh5hXuT |
| Z-19d | min-mu | session_01LfY14SU47oxSPeSiE8zGZ6 |

### Z-18b (finished despite the stop) and writer-side screening

Z-18b missed the stop and ran to 477 births (in-arena top Z400 47.5). Its writer screened candidates with its own
80-game genome_eval head-to-heads before replying. That is a different treatment (extra compute in the loop) and
keeps it out of the cull comparison. Z-19 writers were told (08:55) not to run their own games; the arena feedback
is their only signal. Writer-side screening is a candidate experiment of its own.
Z-18b also reports that 00road-of-riches and 01shortcut end 0-0 for every bot (no TRIBUTE option ever appears);
this was sent to the search session to check against the real engine.
Z-18d (min-mu) also ran to 477 births. Its writer read no evolved genomes and ran no games of its own (feedback,
state.json and matches.jsonl only), so it matches the Z-19 protocol. Its final panel is an extra min-mu data
point (labelled; it is not one of the four Z-19 arms).
Z-18a also ran to 477 births despite the stop (afb50dd). It stays void: it copied the A-line table, screened with its
own games including against seeds/v23 (an evolved policy), and auto-answered with a script from about request 245.
Z-19c (min-mu, screened from seq 9 to ~355, scripted from ~seq 199) finished at 475 births (0697f7f); in-arena top
Z417 43.1. Panel final pending.
Z-19a (legacy) finished at 478 births (33a7b387); in-arena top Z469 40.1. It also screened (genome_eval on its own
children) and scripted replies from ~b230; it rewrote rep-335/337/339 after the arena had consumed them. Its findings on
the panel maps: the genome starter's near(altar,1) goal set scores 0 on 00road-of-riches (fixed by subtracting
walls/holes/altars); 01yellow-brick-road suspends genomes about 960 times per game (0 gems for every genome on 648bafd).
So all four Z-19 runs are screened. The cull comparison stands as screened-vs-screened.
Z-19d (min-mu) screened with its own games from seq 2 and used a scripted driver for seq 146-224; it read the no-games
message at 12:13 and switched to hand-written, unscreened replies from seq 225. It is a mixed run: screened to about
b225, unscreened after.
Z-19d finished at 476 births (7808ab26); in-arena top Z467 43.3. Screened for seq 1-224, feedback-only for seq 225-462.
All four Z-19 runs are done; their final populations are being scored once each.
