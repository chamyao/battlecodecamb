# Link mutation prompt, draft v1 (not in use; for Cham's review)

Rendered for parent = seed (v23), link r_run -> under_fire.

## System

```
You edit one link of a program written in a small typed language (reference below). A link is a
caller gene and a gene it calls. You will be given the two genes' code and the signatures of the
genes around them. You change how the caller uses the callee. You do not see or change anything else.

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
Change the interaction between r_run and under_fire. Do one of:
  (a) change both genes, so that what under_fire computes and how r_run uses it change together
      (for example: under_fire takes a parameter that r_run sets, or returns a Num that r_run
      compares, instead of a Bool);
  (b) insert a new gene between them: r_run calls the new gene, which may call under_fire.
A reply that changes only one of the two genes is rejected.
If you change under_fire's signature, its other callers keep working only if you keep a gene with
the old signature (you may duplicate under_fire as a new gene for r_run instead).

# Reply
One ```python block with: each changed editable gene (keep its @gene id; update its description to
say what it does now), and each new gene as @gene("new", "<one line>", parents=["<id it came from>"]).
Nothing else.
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
