# Policy grammar (v0, to iterate)

A policy is a program the generator network writes token by token. Every
block it uses has a fuel price; the simulator charges them.

- **Pure blocks** return a typed value and change nothing. They nest:
  `move_towards(closest(ring(altars(), 1)))`.
- **Effect blocks** change the world or memory (move, attack, cast, buy,
  write_shared, write_draft, end_turn ...). Order matters, so they appear as
  steps in a sequence.
- **Steps** run in order. Kinds:
  - an effect block call
  - `if <bool expr>: <steps> [else: <steps>]`
  - `let name = <expr>`: store for this turn (computed once, reused for ~0 fuel)
  - `keep name = <expr>`: store in private memory, persists across turns
    (computed once; the policy decides when to recompute)
  - `end_turn()`
- **Types** (number, bool, tile, tile set, unit, unit list, item, champion ...)
  decide what can plug into what; the generator is masked to type-correct
  tokens and to variables that already exist.
- Memory: reads are pure blocks; writes (shared, draft, private) are effect
  blocks. `let` is a private write cleared at turn end.

No loops for now: list/set blocks (`filter`, `first`, `union`, ...) cover the
cases the starter bot uses loops for.

Example: `policies/starter.policy` (the official starter bot, translated).
