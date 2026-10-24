# Prompt experiment 1: link-change enforcement and context (Arena A, Oct 24)

Approved by Cham (Oct 24, ~22:30 UTC).

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

## Arms (approved by Cham, 22:3x)

- **A0 control**: today's mutation prompt and rules (genome/search 7e40b6f, default paragraph), one link.
- **A1 typed explicit**: the prompt in arenaa/prompts/mutate_link_v1.md: minimal system (role + language
  reference without the fuel bullet), the link's two genes in full, signatures + descriptions of the
  genes they call and of the callee's other callers, the explicit Task rules 1-7 and 9-10, the type's own
  instruction and check (T1 both / T2 insert / T3 helper / T4 replace / T5 specialise, drawn per cell
  with equal probability, fixed seed), and the explicit Reply section. No game summary, ladder
  observations, fuel advice, goal sentence, entry-gene notes, stats line or rest of the genome.
  Decisions on the open questions: neighbour descriptions kept; no call path; no example.
  A reply failing its type's check gets one retry with the check's message, then counts as a failure.

Links: drawn per parent with a fixed seed among links whose callee is not a trivial wrapper (here,
at_spawn, my tile ...); A0 and A1 use the same links. Same model (Haiku), temperature, parser.

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

- A1 vs A0: paired on cells, exact McNemar test on "better", one-sided, alpha 0.05. A1 replaces A0
  only if significantly better, or equal on the primary and cheaper ($ per child) with no worse invalid
  rate. Per-type rates are reported (descriptive; 24 cells per type is too few to test).
- If A1 does not beat A0, the next arena run is the plain resume (no prompt change) and the finding is that
  neither enforcement nor context changes the yield.
- Any arm whose winner goes into an arena run is re-tested on fresh parents first (as in round 1).

## Cost

240 children (with retries ~300 calls): ~$0.3 at Haiku rates. Scoring:
240 x (80 + 480) games + 40 nulls ~ 160k games on 648bafd: ~1 h on EC2/arena service. Against Arena A's $8
(spent $4.44 + benches <= $2.00).
