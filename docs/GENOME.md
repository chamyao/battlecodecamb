# Genome: a clean-slate policy representation for the search

Design notes from a discussion with Cham, Oct 24 2026. Not built yet. Read `docs/STRATEGY.md` first: the
core principle (compute is part of the action space; fuel is a rule, not a constraint) applies throughout.

## Why change

- The search edits 200+ line rule piles (if/elif chains). In 2,182 hybrid/pure/style children the median
  child scored below its best parent at every edit size, and invalid code rose with size (2% at 1-2 changed
  lines, 19% at 41+). One edit can reorder priorities and disable unrelated behaviour.
- The block set mixes three things: generic operations, the game's API, and our hypotheses written as
  blocks (`in_danger`, `local_strength`, `group_threat`, `threat_eta`, `bank_detour`, ...). The hypotheses
  are frozen: the search can use them but never change what is inside them.

## The one rule

**Only the game is fixed. Everything we write is a gene, and every gene is treated the same.**

| part | what | fixed or evolves |
| --- | --- | --- |
| Primitives | the game's SDK: reads (vision, map, own state, shared memory, fuel), actions (move, attack, cast, ward, buy, sell, consumables, recall, tribute, cancel, shared-memory write, priority, draft pick, draft memory) and its native compute (distance fields, bitboards); plus generic operations (arithmetic, logic, sets, `best(set, score)`) | fixed |
| Genes | named functions written in primitives and other genes. Today's hypothesis blocks become ordinary genes | all evolve, same operators |

No designed blocks. If something is expensive to compute in bot code, that is the game's fuel rule, and the
search decides whether it is worth paying for.

## A turn: one gene, one loop

- One top-level gene, `score(option)`. An option is any legal action right now (its type, move / attack /
  cast / ..., is an input the gene may branch on). The score means "value of doing this now"; 0 = not worth
  doing.
- The fixed loop (the frozen kernel, like the conserved top of a developmental gene network):
  ```
  repeat:
      list every legal option now (from the game's rules: allowances, cooldowns, channels, ranges)
      score each
      if the best score <= 0: end_turn
      do the best one, re-observe
  ```
- The loop limits nothing: genes see what has already happened this turn, so any action order a hand-written
  turn could produce, scores can produce. Order, exclusivity (channels, shared allowances, excludes-walk) and
  retries (unseen occupants) fall out of legality.
- No partition is imposed. Per-action modules, a "danger" signal, a rally tile, roles by champion type,
  phases: all are genes if evolution finds them useful.
- Draft: the same loop over legal picks; the draft-memory write is a gene whose output is the bytes.
- This is "intuition" (evaluate options in the current position). Calculation (simulate ahead, evaluate the
  resulting position) can come later as genes that look ahead, with the depth chosen by the genome. Within
  our own turn that lookahead is exact and cheap; across turns it needs a forward model in the bot.

## Identity, crossover, linkage

- Every gene carries an ID kept on inheritance and a one-line description written when it is created. A
  duplicated gene gets a new ID.
- Mechanical crossover lines genes up by ID (homology by descent): for each ID pick either parent's version,
  then take the dependency closure (a gene comes along with whatever calls it; uncalled genes are dropped).
  It works between relatives. Every lineage starts from one shared seed genome, so at first everything is related.
- Between distant lineages Claude crosses over by meaning (as hybrid #14's casting graft onto v7-zerogem
  did), helped by the descriptions.
- Chromosomes (inheritance units with evolvable grouping) only if we see crossover breaking co-adapted genes
  that do not call each other. If added, a new gene is placed next to the gene it came from (tandem
  duplication), so clusters form by descent, never by design.

## Mutation

- **Dependency graph:** edges are calls, plus data links (one gene writes what another reads: shared-memory
  bytes, `keep` variables).
- **A mutation picks one existing edge and may change the two genes on its ends however it likes.** That includes
  calling other existing genes, or new genes the mutation creates (fresh helpers, insertion between two genes,
  a duplicate of an existing gene, a small new subtree). All other existing genes can be called, not modified.
- So at most two existing genes are modified, and they are ones that already interact. A new gene is
  always called by something, so it is never born dead; a gene left uncalled is removed.
- Changing a gene's inputs for one caller: duplicate it, change the copy, point that caller at it.
- Default one edge per child, sometimes two. No hard size cap: log per child the edges, genes and lines
  changed and the number and size of added genes, and shift the sampling toward sizes that give
  confirmed gains. Evidence: in today's children the share beating the parent by > 0.03 was flat across
  edit sizes (2-4.5%), and highest when 2-3 top-level units changed (4.7-4.8% vs 2.0% for one); screen
  scores, so noisy.
- Operators: Claude for gene bodies and new genes (prompt = the edge's two genes plus the signatures and
  descriptions of the rest), evolution strategies for constants (no LLM), crossover as above.

## Open points

1. Fuel honesty: if the bot interprets genes, it pays interpreter overhead the game does not charge. That
   is compute outside the game. Option: compile genes to native code at bot build time, and use the same
   code (or prices measured from it) in the sim.
2. Seed genome: translate the live policy into genes and check it plays the same (about 50% against the
   original) before searching.
3. Evolvability check: children beating parents, and crossover children beating both, vs the current format
   at the same budget.
4. Separate from representation: the opponents. The league of our own past versions predicts real band
   results poorly; an exploiter population (policies evolved only to beat our best) is the proposed fix,
   with a ~$2 test first.
