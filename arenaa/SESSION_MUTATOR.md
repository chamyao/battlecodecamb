# A Claude Code session as the mutation writer (design draft, Oct 25)

Idea (Cham): one long-lived Claude Code session writes every mutation of an arena run, so the writer keeps
a continuous context instead of a fresh API call per child.

## Mechanics

- The arena runs inside the mutator session's own container (4 cores, ~70k games/h measured), in the
  background. Its LLM backend is swapped for a file queue: each mutation request (the operator's prompt:
  system + user text, plus a request id) is written to `queue/req-<id>.json`; the arena waits for
  `queue/rep-<id>.txt` and parses it exactly like an API reply. A timeout counts as a failed child.
- The session's agent loop: a blocking `wait-for-requests` command returns the pending requests (batch of up
  to 8, since the arena proposes children in parallel); the agent writes one reply per request, then
  waits again. Every reply is logged with request id, the session's model and the time.
- Everything else (operators, mix, culling, anchors, panel) is arenaZ-1's. The panel runs elsewhere
  (arena service).
- Throughput guess: ~10-30 s per batch turn -> a few births a minute, vs ~8/min for arenaZ-1. Games run
  in parallel while the agent writes.

## What "continuous context" means: two variants

- **M1, memory without feedback**: the session sees only the requests it answers (genomes, links, its own
  past edits). It builds familiarity with the codebase and avoids repeating itself, but learns nothing
  about which edits won. Not self-tuning.
- **M2, memory with feedback**: each batch also carries the outcomes of its earlier children (accepted /
  twin / invalid, rating after N games, died or alive). The session can learn which kinds of edit work.
  This is in-search adaptation, which Cham's original rule ("fixed operator mix per run, no self-tuning
  inside the search") excludes; it needs Cham's explicit OK.

## Measure

Arena Z from the starter, same budget in births (the session costs no API $), judged on the 11-opponent
held-out panel per CPU-hour and per wall-hour, against Z-1/Z-2 (and Z-4 for the prompt). Also logged:
twin and invalid rates, edit size, genes added, and whether edit quality drifts as the context fills
(early vs late children, compaction events).

## Risks

- Context growth: hundreds of requests x ~5k tokens; the session will compact. Log compactions; M1/M2
  quality before vs after.
- Session lifetime: the container must stay active for the whole run (the agent loop keeps it busy).
- Reproducibility: replies depend on the session's whole history; log everything.
