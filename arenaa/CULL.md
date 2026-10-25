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
