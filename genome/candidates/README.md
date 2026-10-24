# Ladder candidates (genome line)

| genome | source | sim gate (vs live bot, 800 games) | real cambc vs live bot | status |
| --- | --- | --- | --- | --- |
| B318.genome (sha256 00e1711a5b5778c9...) | Arena B (arenaB-1, 20:00 UTC snapshot) | 0.647 at genome/v0 2356e26; anchors all up (+0.8..+10.3); 0.613 vs commit-mono | 53/80 vs interpreted v23 (style-gconv1), 0 crashes, built at genome/v0 (this commit); 110 first turns at the 200k cap, 647 capped normal turns (v23: 0), reported only | uploading Oct 24 ~20:30 UTC (Cham) |

Build: `genome/bot/sync.sh genome/candidates/B318.genome <bot dir>` at the commit that added the row.
