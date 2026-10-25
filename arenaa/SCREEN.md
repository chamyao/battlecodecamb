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

Extra data point: Z-18c (min-mu) was stopped at 331 births. Its writer copied no evolved genomes and screened with its
own genome_eval games (vs the starter and its own members). Its final population is being scored, for comparison
with Z-18d (min-mu, unscreened, 301 at 477).
Z-18c result: best 384 (Z320), top-3 mean 367, all clean. At matched cull (min-mu), screened 18c (331 births) beats
unscreened 18d (477 births, 301) by +83 with 146 fewer births. That is the same direction as 18b (610). Uncontrolled
(births, cull and screening vary together); Z-20 vs Z-19 decides.

## Control problem (10:36 UTC)

Z-19b (meant as an unscreened control) reports that it ran many local genome_eval A/B tests against its own run's genomes,
built a map dumper and trace tooling from sim source, and from about request 244 generated most replies with its own
scripts. So it is effectively a screened run; its m2 of 409 at b283 is a screened result. Z-19a/c/d were asked what
they did. Prompt rules alone do not stop an Opus session from running games when the binary is available. A real
control needs enforcement: no genome_eval binary in the writer's environment, or a writer without shell access.

## Revised design (11:05 UTC)

Z-19b and Z-19c both screened throughout: 19c ran 200+ evaluations, tens of thousands of games, and later scripted
replies. The no-games message reached them after or near the end (session messages arrive up to ~1h45m late).
Z-19 is therefore a set of screened runs (two per cull rule). That still gives a valid cull comparison, but no
screening control. New controls carry the rule in the starting prompt:

| run | screening | cull | session |
| --- | --- | --- | --- |
| Z-21a | no (starting-prompt rule; attestation in the report) | legacy | session_01WHoWWMTrLqxyWcWj7GNGNJ |
| Z-21b | no (starting-prompt rule; attestation in the report) | legacy | session_01SuaXXWj1bowZj6Kn53bCsV |

Comparison: screened legacy runs (Z-20a/b, plus Z-19a/b and Z-18b as extra screened data) vs Z-21a/b. The decision
rule is as above, with Z-21a/b as the controls.

## First control milestones (12:35 UTC)

| run | treatment | m1 | births at m1 |
| --- | --- | --- | --- |
| Z-20a | screened | 365 | 112 |
| Z-20b | screened | 367 | 110 |
| Z-21a | no own games | 339 | 186 |
| Z-21b | no own games | 272 | 175 |

Per birth, screening leads (365/367 at ~110 vs 339/272 at ~180). Per wall hour the controls are faster: at 12:19,
Z-21 had ~290 births in 75 min and Z-20 ~190 in 3h15. The verdict needs both views; the final comparison is at
matched births and at matched wall time.

Z-21a (control) finished: 478 births in ~1h46m (11:05-12:51), mirror 4748376. In-arena top Z476 42.6. Its writer
attests that it ran no games, traces or replays, built no game tools, opened no other genome or run, and wrote every
reply by hand. A clean control. Its final population is to be scored once. For comparison, the screened Z-19 runs took
3h09-4h19 for the same births.
