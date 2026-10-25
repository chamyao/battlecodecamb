# arenaZ-20: writer-side screening (Oct 25, 09:05 UTC)

Question: does a session writer that plays its own candidates before replying train better than one that relies
only on the arena's feedback? This is STRATEGY.md's principle (compute is part of the action space) applied to the
training loop.

## Why

Z-18b (session writer, legacy cull) missed its stop. Its writer screened children with its own 80-game genome_eval
head-to-heads, and it reached **610/880** at 477 births (Z462, top-3 mean 607). The clean, unscreened runs at similar
birth counts: Z-18d 301 (min-mu), Z-5 394 (b413), API arms 190-207. It is the highest Z result by far, but it was one
uncontrolled run: the writer also read the sim's item table and the map files.

## Runs

The treatment arms are the arenaZ-19 setup (setup_z5.sh + cull-minmu.patch, --cull legacy, --births-in-flight 8,
--max-births 475, isolation rule), plus permission to screen with genome_eval (--threads 1; screens logged to
screens.jsonl). Controls: arenaZ-19a/b (same setup; no own games allowed).

| run | screening | cull | session |
| --- | --- | --- | --- |
| Z-20a | yes | legacy | session_01Cnnv8iUSciZg8GbgDqNMCf |
| Z-20b | yes | legacy | session_01RJosSetbfPKZy7vbviPhtz |
| Z-19a / Z-19b (controls) | no | legacy | CULL.md |

## Measures (fixed before running)

- Primary: panel best and top-3 mean (11 opponents, /880) per 100-birth milestone and at the end; Z-20a/b vs Z-19a/b.
- Cost: wall time per birth, screens and games per birth, and how often the screen changed the writer's choice.
- Decision: adopt screening if both screened arms end above both controls on panel best.
