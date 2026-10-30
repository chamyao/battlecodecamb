# Ladder screens (screen_v1, 30 games; SCREEN.md)

Each candidate's screen is paired with v40's games from b18base (09:57Z). Columns: v40's record on the screen games, the candidate's record, flips (to a win / to a loss), gems submitted (paired change), deaths to champions (paired change), verdict.

| screen | candidate | version (submitted / live) | bundle sha | v40 | candidate | flips | gems | deaths to champions | verdict |
|---|---|---|---|---|---|---|---|---|---|
| s1 | A11501 (genome/v0 1e8898f6, sha fb1b19cd) | v45 (10:45:04Z / 10:51:43Z) | 0eb82518 | 13-17 | 10-20 | 2 / 5 | +2.5 ± 35.5 | +1.9 ± 0.9 | down on flips, flat on gems: not promoted. Replaced by the next screen (v46), no separate revert. |
| s2 | A11696 (genome/v0 1b2f56d3, sha 380b8b4b) | v46 (11:01:00Z / 11:11:50Z) | 49d3d197 | 13-17 | 12-18 | 7 / 8 | -32.7 ± 52.2 | +1.7 ± 1.2 | neutral, a lot of churn: not promoted |
| s3 | A11599 (genome/v0 1b2f56d3, sha 068e7c98) | v47 (11:21:16Z / 11:32:06Z) | 9597bc6e | 13-17 | 11-19 | 4 / 6 | -55.3 ± 52.6 | +2.4 ± 1.3 | down (captures -4.7 ± 2.3): not promoted |
| s4 | A11791 (genome/v0 a3f131da, sha 0859ce55) | v48 (11:41:53Z / 11:51:41Z) | 90d8b4fc | 13-17 | 9-21 | 4 / 8 | -54.2 ± 47.7 | +3.0 ± 1.1 | clearly down: not promoted; replaced at once by s5 |
| s5 | v43-fix3 (genome/v0 1e8898f6 = arenab 7bb80059, sha 6760603a) | v49 (12:02:12Z / 12:11:39Z) | 3bc991c2 | 13-17 | 10-20 | 3 / 6 | -12.9 ± 36.1 | +1.2 ± 0.8 | down on flips: not promoted |
| s6 | x6-61 (genome/v0 1e8898f6, sha 513f4ef1) | v50 (12:22:05Z / 12:32:13Z) | 62102500 | 13-17 | 13-17 | 3 / 3 | +24.5 ± 26.4 | +0.8 ± 0.9 | level on flips, slightly up on gems (captures +1.9 ± 1.4): not promoted (needs up on both) |
| s7 | x7-125 (genome/v0 6d5ed41, sha 4afcd1b6) | v51 (12:42:55Z / 12:51:39Z) | 95b141b6 | 13-17 | 7-23 | 2 / 8 | -48.5 ± 36.4 | +3.1 ± 1.0 | clearly down: reverted to v40 at once (s8) |
| s8 | **v40 control** (revert; bundle 7317ef88) | v52 (13:00:29Z / 13:11:43Z) | 7317ef88 | 13-17 | 13-17 | 3 / 3 | +10.0 ± 22.4 | +0.7 ± 0.8 | control: v40 is live again |

## Reading the 7 screens (13:15Z)

- **The control sets the noise floor.** v40 against its own 09:57Z games: 16 of 30 identical, flips 3 / 3, gems +10 ± 22. Opponents drift over about 3 hours, but symmetrically.
  - A candidate's screen means something only beyond about ±3 flips each way.
  - b16 → b18base showed 55 of 60 identical over 4 hours. Today's drift is larger.
- **Inside the noise:** x6-61 (3 / 3, gems +24 ± 26) matches the v40 control almost exactly. A11696 (7 / 8) churns a lot but nets to zero.
- **Below the noise, consistently:**
  - x7-125: 2 / 8.
  - A11791: 4 / 8.
  - A11501: 2 / 5.
  - v43-fix3: 3 / 6.
  - A11599: 4 / 6.
- **Common factor:** every below-noise candidate has **+1.2 to +3.1 deaths to champions** (control +0.7). The fight-seeking edits (exploit-7 and exploit-8, and the A lineage) lose more champions to real opponents than they gain.
- **None promoted.** v40 is live (v52).
| s9 | A11976 (genome/v0 10d5db97, sha 7a753124), paired with s8 | v53 (13:22:22Z / 13:31:49Z) | 18b76f0d | 13-17 (s8) | 10-20 | 3 / 6 | -65.7 ± 42.1 | +0.6 ± 1.1 | down: deaths normal, but captures -7.6 ± 2.1. Not promoted |
| s10 | v40-join3 (genome/v0 5ce7b4bf, sha 538a1b4c), paired with s8 | v54 (13:41:02Z / 13:42:36Z) | 9457c524 | 13-17 (s8) | 8-22 | 1 / 6 | -74.4 ± 38.2 | +0.9 ± 0.7 | clearly down (captures -5.1 ± 2.3): reverted |

**Revert after s10:** v40 bundle 7317ef88 re-verified and submitted 13:53:16Z as **v55**; live by 14:02:12Z.

**Queue finished.** 9 candidates screened (s1-s7, s9, s10) plus the v40 control (s8): none beat v40.
- **A11976** (survival-first) fixed the excess deaths (+0.6), but lost captures (-7.6).
- **v40-join3** (fight cohesion) lost captures (-5.1) and gems (-74).
- So both directions away from v40's balance (more fighting, or more caution and grouping) cost more on the ladder than they gain.
| s11c | **v40 control** (live v55, no submit), paired with s8 | v55 (- / screened 16:20:49Z) | 7317ef88 | 13-17 (s8) | 10-20 | 2 / 5 | -54.9 ± 33.4 | +1.2 ± 0.8 | **opponent drift**: v40 lost 3 wins between 13:11Z and 16:20Z. A fresh control is needed at the start of every screen session |
| s11 | d-out2b (genome/v0 4787e102, sha b072d8bc; v40 + retreat when outnumbered), paired with s11c | v56 (16:31:29Z / 16:43:32Z) | 63f4d4e6 | 10-20 (s11c) | 12-18 | 4 / 2 | +1.1 ± 28.2 | **-0.8 ± 0.7** | up on flips, gems level, fewer deaths (gems lost on death -14 ± 8): **promoted to the full band b19** |

**b19 (full band, d-out2b as v56, 16:55Z) vs b19base (v40 as v57, 17:02Z): 31-29 vs 30-30.** Flips 6 to a win / 5 to a loss; gems -7.2 ± 25.3; deaths to champions -0.8 ± 0.6; gems lost on death **-14.5 ± 6.9**; captures -1.1 ± 1.5. This meets the genome lead's bar (up on flips; gems and deaths no worse), so **d-out2b is the new live choice**. The d2-tout screen (s12) runs first, then the better of d2-tout and d-out2b goes live.
| s12 | d2-tout (genome/v0 97637588, sha 404637c9; d-out2b + Tavi retreats whenever outnumbered), paired with b19base (v40 screen subset, 10-20) | v58 (17:28:39Z / 17:33:08Z) | b71709aa | 10-20 | 12-18 | 6 / 4 | -40.1 ± 46.3 | -1.6 ± 1.0 | vs **d-out2b** (b19 subset, 12-18): flips 4 / 4, gems -41.3 ± 34.1, deaths -0.8 ± 0.6, captures -2.5 ± 2.3. Not better than d-out2b |

**Live: d-out2b as v59** (bundle 63f4d4e6, identical to v56). Submitted 17:43:09Z, live by 17:45:54Z. **The new baseline is b19** (d-out2b's 60 band games, 16:55Z).
| s13c | **d-out2b control** (live v59, no submit), paired with b19 | v59 (- / screened 17:5xZ) | 63f4d4e6 | 12-18 (b19) | 12-18 | 0 / 0 | +0.0 | +0.0 | all 30 games identical to b19: no opponent drift this hour |
| s13 | d4-marc (genome/v0 39315389, sha 170c4ecf; d-out2b with an enemy Marcella counted twice), paired with s13c | v60 (18:03:32Z / 18:05:36Z) | a2a0c192 | 12-18 | 10-20 | 2 / 4 | -10.2 ± 25.2 | -0.4 ± 1.0 | not up: **reverted to d-out2b** (v61, submitted 18:13:17Z, live 18:21:53Z). Deaths to Marcella 109 → 71 (-35%), but total deaths to champions 329 → 318: the deaths moved to other killers |
| s14 | s-hunt3 (genome/v0 d29d9ed3, sha 5cfbfb64; d-out2b + Hunter Str emblem bought 3rd), paired with s13c | v62 (18:28:22Z / 18:31:49Z) | 99ae17b5 | 12-18 | 7-23 | 1 / 6 | -61.5 ± 28.8 | +0.7 ± 0.6 | clearly down (captures -4.0 ± 1.8). Kill gold per game 183 → 208 (Hunter bonus +38/game). **Reverted to d-out2b** (v63, submitted 18:41:23Z, live 18:44:08Z) |
