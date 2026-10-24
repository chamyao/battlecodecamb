# Jobs for remote-server: style line

Written by the FunSearch lead session (the style line no longer has its own session); read by
remote-server when woken (docs/REMOTE_WORKER.md). Clone: `~/bc/style`, branch `funsearch/style`.

## Job S1 (2026-10-24 04:50 UTC): let style6-{a,b,c} run to their end. Do not start style7.

- style6 runs to its budget and validates on its own; keep it as it is.
- When each island's league exits (budget spent or a promotion), push state to `remote/style` and
  comment on PR #3 with that island's validation lines ("h2h", "cambc", "PROMOTED").
- Do not launch style7 or any new run: the line is out of budget until the lead writes a new job here.
