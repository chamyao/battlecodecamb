# Link mutation prompt, draft v1 (not in use; for Cham's review)

Rendered for parent = seed (v23), link r_run -> under_fire.

## System

```
You edit one link of a program written in a small typed language (reference below). A link is a
caller gene and a gene it calls. You will be given the two genes' code and the signatures of the
genes around them. You rewrite those two genes. You do not see or change anything else.

# Language
[genome/LANGUAGE.md sections "A genome file", "Types", "Fields", "Primitives", "Constants",
 unchanged; the fuel bullet removed]
```

## User

```
# Link
r_run  ->  under_fire        (r_run calls under_fire)

# Editable gene 1: r_run   [r3]   called by: rule
@gene("r3", "retreat on foot: below 30% health and under fire")
def r_run() -> Bool:
    return not at_spawn() and hurt_below(0.3) and under_fire()

# Editable gene 2: under_fire   [s8]   called by: r_run, r_cashout
@gene("s8", "under fire: in danger or an enemy champion within 8")
def under_fire() -> Bool:
    return in_danger() or enemies_within(8) > 0

# Genes these two call (fixed; you may call them, and any other gene listed here)
at_spawn() -> Bool                 [s2]  standing on our spawn region
hurt_below(f: Num) -> Bool         [s3]  health below a fraction of max
in_danger() -> Bool                [s7]  in danger: an awake camp can hit me, or an enemy champion is within its range + 1
enemies_within(r: Num) -> Num      [s6]  visible enemy champions within r tiles

# Other callers of under_fire (fixed; they must still type-check)
r_cashout() -> Bool   [r5]  recall with gems when below half health and nothing near

# Task
You are making one mutation of this program. The mutation may touch exactly two existing genes,
r_run and under_fire, and may create new genes.

What you may do:
1. Rewrite the body of r_run, of under_fire, or both: change conditions, thresholds, arithmetic,
   which genes and primitives they call, the order of tests, add or remove branches.
2. Change the parameters or return type of r_run or under_fire.
3. Create new genes. A new gene can be called by r_run, by under_fire, or by another new gene. It may
   call any gene listed in this prompt and any primitive.
4. Stop calling a gene: r_run may stop calling under_fire, under_fire may stop calling in_danger, etc.

What you may not do:
5. Change any gene other than r_run and under_fire (the listed fixed genes stay exactly as they are).
6. Use a gene or primitive that is not listed in this prompt or in the language reference.
7. Break a caller: r_run is called by rule() as r_run() -> Bool, and under_fire is called by r_cashout()
   as under_fire() -> Bool. If you change either signature, those calls must still type-check, so
   keep the old signature for them (for example: keep under_fire as it is called and give r_run a new
   gene with the new signature).

What counts as a mutation (checked automatically; otherwise the reply is rejected):
8. Either both r_run and under_fire have a changed body, or at least one new gene is created and
   called. Changing only one of the two genes, with no new gene, is rejected.
9. Changing only a description, renaming, reformatting, or reordering code without changing what it
   computes does not count as a change.
10. The result must type-check under the language reference. Every gene must return its declared
    type on every path.

# Reply
Reply with exactly one ```python code block and nothing outside it. The block contains:
- Each of r_run and under_fire that you changed, in full, with its original id: @gene("r3", ...) and
  @gene("s8", ...). Update the description to one plain line saying what the gene now computes.
  Omit a gene you did not change.
- Each new gene, in full, as @gene("new", "<one plain line saying what it computes>",
  parents=["<id of the gene it was derived from, r3 or s8>"]).
- Any new keep declaration your genes use (NAME: Type = value), above the genes. Only update() may
  assign keeps, so r_run, under_fire and new genes may read keeps but not assign them.
Do not repeat fixed genes. A new gene that nothing calls is deleted.
```

## What was removed vs today's prompt, and why

| removed | today | why |
| --- | --- | --- |
| game rules summary | system | high-level; the genes' descriptions carry the meaning needed for one link |
| "Observations from today's top-12 ladder games" | system | ladder intel; not sim-only |
| "cheaper policies are better" / fuel notes | system | steers towards fuel edits; fuel is a rule, not a goal |
| "Aim for a change that should make the bot win more ... Keep what already works" | task | high-level goal; replaced by an explicit structural task |
| entry-gene / consider / after / shared-byte notes | system | not about this link |
| "Current results: ..." stats line | user | no use to the edit |
| the other ~75 genes' signatures and descriptions | user | only the link's neighbourhood is shown |

## Open questions for Cham

1. Keep the descriptions of neighbouring genes (they are the only semantic hint left), or signatures only?
2. Should the model see the whole call path from score() down to the caller (one line per gene), so it
   knows when the link matters?
3. Option (b) lets the new gene ignore under_fire entirely. Allowed, or must it call the callee?
4. One example of a valid change in the task (as above), or none (less steering)?
