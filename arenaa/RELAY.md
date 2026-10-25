# Relay arena (Arena Z on short Claude Code sessions), Oct 25

Cloud sessions finish short jobs reliably but long-lived containers get recycled. A relay runs one arena
as a chain of short legs: each leg is a fresh session that resumes the arena from the state on a git
branch, plays ~50 births, pushes the state and stops; the Arena A lead starts the next leg.

- Code: arenaZ-5's checkout (genome/search patches/setup_z5.sh: 7e40b6f + file-queue patch, runtime
  648bafd). The session itself writes the mutations and crossovers through the file queue (no API key in
  sessions), with the M2 feedback in each request.
- Difference from Z-5: Z-5 is one session with one continuous context (memory across all 475 births);
  the relay's writer memory resets every leg (~50 births). So arenaZ-10 (relay) vs arenaZ-5 measures the
  value of a continuous context; both vs Z-1/Z-2/Z-7 measure "session-written" vs API-written.
- State branch: arenaa/z10-relay, path arenaZ-10/arena (+ arenaZ-10/queue for the request/reply log).
  Leg k runs --max-births 50*k. Files are gitignored: always `git add -f`.
- Panel: as for the other Z runs (arena service), following the branch.
