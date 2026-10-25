# arenaZ-11: in-place gene splitting (approved by Cham, Oct 25)

Question: does refactoring long genes into smaller ones (behaviour unchanged) make the arena train better,
by giving link mutation finer targets and crossover by gene ID more homologous units?

## The one change vs arenaZ-1

Every 10 births, the arena picks one random live member whose longest gene has > 30 code lines (if none,
skip) and asks Claude to split that gene:

- Task: "Split gene G into a caller plus one or more new helper genes so that the program computes
  exactly the same thing in every situation. Do not change any behaviour, constant, order of tests, or
  primitive call results. New genes get @gene("new", "<one line>", parents=["<G's id>"]); G keeps its id."
  Same minimal system as today's mutation prompt (language reference) plus the full genome.
- Check: the child must type-check, contain more genes than the parent, and be a behavioural twin of the
  parent on the arena's fingerprint games (identical per-game outcomes). One retry with the failure
  message; otherwise discarded (logged).
- Apply in place: the refactored genome replaces the member (same name, rating, species, games); it is not
  a birth and costs no slot. Gene IDs: G keeps its id; helpers get fresh ids with parent G.
- Logged to splits.jsonl: member, gene, lines before/after, genes before/after, check result, cost.

Everything else as arenaZ-1 (7e40b6f, 648bafd, starter seed and only anchor, champions every 50, mix
70/15/15, Haiku with Opus every 10th, same RNG stream), 475 births, $3 (plus splits).

## Measures

- Primary: panel curve (11 held-out opponents, top 3 every 100 births) vs the baseline spread (Z-1, Z-2,
  Z-7), per birth and per hour.
- Structure: genes per genome over time; median gene size; species count; share of crossovers by ID vs by
  meaning; mutation edit size, twin and invalid rates; where later gains land (split-off genes or not).
