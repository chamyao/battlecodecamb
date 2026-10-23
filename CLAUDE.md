# Notes for Claude sessions working on this repo

Cambridge Battlecode 2026a (https://2026a.battlecode.co.uk). Read
`docs/STRATEGY.md` first: its core principle (compute is part of the action
space; fuel is a rule, not a constraint) is the basis of the whole strategy
and must not be dropped.

Reference docs (exported from the handbook, Oct 2026):
- `docs/GameRules.md`: full rules and champion specs.
- `docs/BotAPIPython.md`: Bot API (Python flavour; C++/Rust/OCaml are the same SDK).
- `docs/handbook/*.txt`: text dumps of the guide/reference pages
  (bitboards, distance fields, errors, getting started, WASM API).

The official engine ships in the pip package `cambc` (closed native binary,
deterministic). It is the reference our simulator is tested against.
