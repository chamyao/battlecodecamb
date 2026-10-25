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
