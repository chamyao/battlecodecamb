# Prompt experiment 1: link-change enforcement and context (Arena A, Oct 24)

Draft for Cham's approval. Nothing here runs until approved.

## Question

Does a link mutation that must change the *relation* between its two genes, given only the context it
needs, produce more children that are genuinely stronger than their parent than today's mutation?

## What today's mutation prompt contains (arenaA-3, genome/search 7e40b6f)

Median per call: ~10,000 input tokens (5,175 cached system + 4,850 user), ~900 output tokens.

| part | where | ~tokens | needed to write a valid edit? |
| --- | --- | --- | --- |
| role + fixed-loop description | system | 60 | yes (what score() is) |
| game rules summary (funsearch GAME) | system | 350 | maybe (what the genes mean) |
| "Observations from today's top-12 ladder games, for inspiration" (monoliths, drafts, builds) | system | 250 | no; ladder intel leaking into Arena A |
| "every block costs fuel ... cheaper policies are better" | system | 60 | no; pushes fuel edits |
| gene language reference (LANGUAGE.md: types, fields, all primitives, constants) | system | 1,900 | types + signatures of primitives: yes |
| consider/update/after/shared-bytes notes | system | 150 | no for most links |
| task paragraph (MUTATE_TASK) | system | 200 | yes |
| "Current results: ..." stats line | user | 30 | no |
| keep declarations | user | 100 | only those the two genes use |
| every other gene: signature, id, description, calls (~79 lines) | user | 2,500 | only callers/callees of the two genes |
| the two EDITABLE genes' code | user | 300 | yes |

Observed behaviour (371 one-link mutations, arenaA-1/3): 88% change one gene only, 11% both, 0.5% add a
gene. Bench round 1 (8 task paragraphs): new genes ~1 per 30-40 children under every wording.

## Arms (one factor at a time, all on the same cells)

- **A0 control**: today's prompt and rules (the round-1 "default" arm, re-run on these cells).
- **A1 enforced**: A0 + the link rule. Task paragraph replaced by:
  > Change how `{A}` uses `{B}`. Your change must alter the interaction between these two genes:
  > change both genes so that what `{B}` computes and how `{A}` uses it change together, or insert a
  > new gene between them that `{A}` calls instead of, or as well as, `{B}`. A change to only one of
  > the two genes is rejected.
  Checked mechanically: accepted only if both editable genes' bodies change or a new gene is called by
  `{A}`; otherwise one retry with the rejection message, then counted as a failure.
- **A2 enforced + minimal context**: A1's task and check, with the context cut to what an edit needs:
  role + fixed loop; types and primitive signatures (no prose); the two genes' code; signatures and
  descriptions of their callers, of the genes they call, and of the genes one step further down; the
  keep declarations they use. Removed: game summary, ladder observations, fuel sentence, entry-gene
  notes, stats line, the rest of the genome.
- **A3 enforced + minimal + game rules**: A2 plus the game rules summary (no ladder observations, no fuel
  sentence). Tells us whether game knowledge helps once the rest is gone.

Links: A1-A3 skip links whose callee is a primitive-wrapper with no logic (e.g. `here`, `at_spawn`);
A0 keeps today's link draw. Same model (Haiku), temperature and parser for all arms.

## Cells

120 (parent, link) cells: the 15 parents of r1b/r1c/promptbench-2 x 8 links. A link valid for A1-A3
(non-trivial callee) is drawn per parent with a fixed seed; A0 uses the same links. Runtime 648bafd.

## Measures (fixed before running)

- **Primary**: per child, wins vs the 6 anchors (style-gconv1, tune-v20-L1, rall2, v7, metadraft,
  tune-v20-L1c; 80 distinct games each, bot seeds) minus its parent's wins on the same 480 games. A child
  is **better** if that difference exceeds the 95th percentile of the measured null (40 sigma-0.02
  constant tweaks, re-measured on 648bafd; currently ~+20 of 480). Primary statistic: the share of
  cells whose child is better. Failures (invalid, twin, rejected) count as not better.
- Secondary: share changing both genes / adding a gene; invalid, twin and rejection rates; lines
  changed; vs-parent win rate (80 games); mean and 90th percentile of the anchor difference; $ per child.
- The vs-parent 80 games are recorded for every child (to learn whether they predict the anchor score).

## Decision rule (fixed before running)

- A1 vs A0, then A2 vs A1, then A3 vs A2: paired on cells, exact McNemar test on "better", one-sided,
  alpha 0.05. An arm replaces the previous one only if it is significantly better, or equal on the
  primary and cheaper ($ per child) with no worse invalid rate.
- If nothing beats A0, the next arena run is the plain resume (no prompt change) and the finding is that
  neither enforcement nor context changes the yield.
- Any arm whose winner goes into an arena run is re-tested on fresh parents first (as in round 1).

## Cost

480 children (with retries ~600 calls): ~$0.5 at Haiku rates (A2/A3 calls are ~3x shorter). Scoring:
480 x (80 + 480) games ~ 270k games on 648bafd: ~1 h on EC2/arena service. Against Arena A's $8
(spent $4.44 + benches <= $2.00).
