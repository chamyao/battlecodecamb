# Prompt bench: a meta loop over mutation prompts (Cham, Oct 24)

Goal: find mutation prompts whose children include more prodigies (children clearly stronger than
their parent). The bench judges prompts on a fixed, paired test outside the arena; the arena keeps one
fixed prompt per run (no self-tuning inside the search). A bench winner enters an arena run as one
controlled change, judged there on the population's win rate vs the fixed anchors.

Why outside the arena: in arenaA-1 a newborn got ~80 games before it could die, and child-vs-parent
gains were within noise (top-tail children vs fixed anchors: +1.4 +- 2.0 points over their parents). A
prompt's quality is a property of its children's distribution, which the arena's ratings see too
noisily to compare prompts.

## One round

- Prompts: 8 variants of the MUTATE_TASK paragraph(s) that tell the model what kind of change to make.
  The rest of the prompt (game and language reference, the EDITABLE genes, the reply format) is fixed
  and owned by the bench, so every variant can be parsed the same way.
- Parents: the seed (genome/seeds/v23.genome) and the 4 genomes alive at the end of arenaA-1 with the
  most games. Fixed for the round.
- Links: for each parent, 8 links picked once with a fixed RNG seed (operators.pick_edges, one edge),
  shared by every prompt. So each prompt writes the same 40 (parent, link) children: a paired design.
- Model: Haiku (it writes ~90% of the arena's mutations), temperature as in the arena.
- Children: invalid ones and behavioural twins of their parent count as failures (logged, no games).
- Score: each valid child plays its parent 200 games: maps cycled, both sides, fixed seeds shared
  across prompts.
- Prodigy check: every child with >= 0.58 vs its parent also plays 200 games vs each of the 5 fixed
  anchors (style-gconv1, tune-v20-L1, rall2-ca4-lean-g, v7, opp-tune5-metadraft); its parent's anchor
  rates are measured once on the same seeds.

## Measures per prompt

- Primary: prodigy rate = children whose win rate vs parent has a one-sided 95% lower bound > 0.5
  (>= 112/200), and of those, the gain vs the fixed anchors over the parent.
- Tail: 90th percentile and max of child-vs-parent win rate (failures count as 0.5 for the quantile:
  no change).
- Cost and shape: twin rate, invalid rate, lines changed, genes added, $ per child.
- Paired comparison between prompts on the same (parent, link) cells.

## Outer loop

- Round 1: default (arenaA-1/3 prompt), creative (arenaA-4 prompt), and 6 hand-written variants
  (e.g. "add a behaviour for a situation the genes don't handle", "change what score() weighs",
  "replace a rule with a different mechanism", "make the champion more aggressive / more cautious
  here", "add a helper that computes something new", "simplify drastically").
- Later rounds: keep the top 2; Opus writes 6 new variants from the round's prompts and their measures
  (mutations and crossovers of the best prompts, new instructions).
- Winner's curse: each round's best prompt is re-tested on 5 fresh parents (from the current arena) and
  fresh seeds before it can enter an arena run.

## Cost

Per round: 320 children x ~$0.0012 (Haiku) + Opus prompt writing ~ $0.5-0.7; 64k parent games plus the
prodigy checks: ~40 min on one EC2 slot at db3f945. Counted against Arena A's $8; ask Cham beyond it.

## Logs

<out>/prompts.jsonl (round, id, text, origin), children.jsonl (round, prompt, parent, link, error,
lines, genes added, cost), games.jsonl (child vs parent / anchor results per game), rounds.jsonl
(per-prompt measures). Genomes kept under <out>/genomes/.
