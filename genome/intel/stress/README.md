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
