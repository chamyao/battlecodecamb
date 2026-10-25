# Stress opponents (anchors, not arena children)

Calibration: sim, --bot-seeds, /80, runtime genome/v0 b5d606b. "As A" is the stress genome's own play against B792;
"B792 vs it" is B792 (ladder v26) against it. The band signature is from real games b1-b3 (GAPS.md, "The 5 band teams").

| genome | B792 vs it | its gems per capture / tributes / kills on B792 | B792's gems per capture | band signature |
|---|---|---|---|---|
| hunter (commit + chase carriers) | 57 | — / — / 6.5 | — | hunter type (kills); our deaths ~10 |
| hunter-carry (B318 + chase + fed Vesper Vale) | 57 | — / — / 6.0 | — | fed carry: killer/victim item points 53/16 (not reached) |
| **farmer** (rich groups 21+ only, bank at 45, no cast-ahead) | **43** | 21.4 / 23 / 7.3 | 9.9 | NotSoLonely 1-14: 30.4 per capture, bag 45, 6.7 kills |
| deathball (non-Vendettas within 3 of the Vendetta, chase, bank at 80) | 52 | 11.9 / 15 / 8.6 | 10.6 | Sloppy Joe 3-12: spread 7.9, 18.6 kills, 11 tributes |
| rushbank (bank 3+ until the team has banked, chase from r150) | 49 | 10.6 / 38 / 8.6 | 11.2 | noobers 4-11: first tribute r37, 12.3 kills |
| lockall (seed + lock every altar) | — | — | — | altar locks (23 of 50 b1 games) |

The farmer is the hardest for B792 and reproduces the real loss shape: we capture at under half their gems per capture
(9.9 vs 21.4; real 10 vs 30), and the gems end even. Deathball and rushbank do not reach the band's kill rates (8.6
vs 18.6 and 12.3). Like hunter-carry, B792-based rules do not fight as well as the band.

Calibration sweeps:
- farmer: RICH 14 with no fights: B792 61/80 (the farmer died 11.1 times a game); RICH 21 with no fights: 66; RICH 21 fighting back in reach: 43 (kept).
- deathball: BALL_R 4: 58; 6: 54; 3: 52 (kept).

## Gate row for a61188-mono (directed/a61188-mono.genome; --bot-seeds /80, runtime genome/v0 ca5180b)

a61188-mono = A61188 (ladder v27) + the mono edit by gene ID (`tools/graft.py mono`: s14, r14, r13 and a0 use
`farmable`, i1). The result is 41/80 vs A61188. A monolith-only variant (skip only the monolith itself, not its group) scores 39/80.

| map (2 games vs B792) | A61188 non-champion deaths | a61188-mono |
|---|---|---|
| 00great-wall | 25.0 | 15.0 |
| 01shortcut | 17.5 | 9.5 |
| 01boss-battle | 21.0 | 22.0 (the monolith push, r15, fires there: its only altar is next to the monolith) |
| 00lanes (control) | 0 | 0 |

| anchor | L1c | gconv1 | v7 | L1 | rall2 | metadraft | hunter | hunter-carry | farmer | deathball | rushbank | lockall | B318 | B792 | v23 seed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A61188 | 53 | 60 | 76 | 55 | 58 | 74 | 61 | 56 | 47 | 62 | 50 | 68 | 52 | 48 | 56 |
| a61188-mono | 55 | 60 | 77 | 58 | 60 | 76 | 65 | 59 | 50 | 63 | 53 | 68 | 53 | 52 | 57 |

No anchor drops (+0 to +4).
