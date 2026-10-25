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

## Overfit check on Z-18b (search session, 09:08 UTC)

A map-held-out panel is impossible (only 40 maps). Two held-out variants on 648bafd instead: (a) the same 11 opponents
with new game instances (bot seeds off, policy seeds 11 and 12); (b) 6 opponents no Z panel or screen ever used
(/480).

| genome | fixed panel /880 | new instances (mean) | held-out opponents /480 |
| --- | --- | --- | --- |
| Z462 (18b, screened) | 610 | 585 | 186 |
| Z400 (18b, screened) | 610 | 602 | 180 |
| Z392 (Z-5) | 394 | 350 | 82 |
| Z446 (18d, clean) | 301 | 297.5 | 45 |
| Z403 (Z-15, API) | 207 | 206.5 | 25 |

No sign of overfitting. The screened genomes lose less on new instances than Z-5's, and lead by more on unseen
opponents (2.2-2.5x Z-5). The ranking holds across all three measures. n = 1 run; Z-20 is the replicate test.
