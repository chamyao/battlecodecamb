
## Aggregates over all 264 decisive fights

- first champion damage in the fight: them 77%, us 23%
- their champions damaging the victim: 2.0 median; 2+ in 74%; rounds from first hit to death 10.5 median
- victim damaged any of theirs before dying: 66%
- their hits on the victim from beyond the victim's own attack range: 33% of hits
- stun/cc landed on the victim before the kill: 66%
- stat gap at fight start, killer minus victim: strength +10, max HP +300, focus +24 (medians)
- killer unseen by all of ours in the 3 rounds before the first hit: 27%
- their side acted first in the round of the first hit: 46%
- HP fraction at fight start: victim 0.96, killer 0.96 (medians); victim below 0.75: 24%
- victim attacking a camp in the 5 rounds before the first hit: 34%
- fights starting in rounds 0-150: 27; item points killer 0 vs victim 0; gap strength -5, focus +0, max HP +0; 2+ hitters 85%; victim start HP 0.92
- fights starting in rounds 150-400: 69; item points killer 9 vs victim 3; gap strength +5, focus +10, max HP +200; 2+ hitters 81%; victim start HP 0.95
- fights starting in rounds 400-9999: 168; item points killer 46 vs victim 11; gap strength +38, focus +70, max HP +375; 2+ hitters 70%; victim start HP 0.96

## vc? on 00eight

### Vesper Vale (ours) killed by Vesper Vale, round 87; fight from round 79

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| them | Vesper Vale | (9,2) | 1000 / 1000 | 59 | 55 | 100 | {} |
| them | Vendetta | (6,11) | 1000 / 1000 | 0 | 70 | 100 | {} |
| them | Ryth | (7,10) | 1200 / 1200 | 0 | 45 | 100 | {} |
| us | Vesper Vale | (13,7) | 1000 / 1000 | 4 | 55 | 100 | {} |
| us | Ryth | (18,0) | 100 / 1200 | 4 | 45 | 100 | {} |
| us | Ren | (12,4) | 360 / 900 | 9 | 35 | 100 | {} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Vesper Vale VVVVV, Vendetta VVVVV, Ryth VVVVV

Round by round (team A acts first in round 79; teams alternate each round). Actions in engine order:

- **r77** start: Vesper* (7,4) 1000hp d6; Vendet* (7,13) 1000hp d6; Ryth* (9,12) 1200hp d5; Vesper (13,7) 1000hp d0; Ryth (18,0) 100hp d7; Ren (12,5) 540hp d2
  - us:Vesper Vale basic -> camp
  - us:Ryth Recall ->
  - us:Ren basic -> camp
- **r78** start: Vesper* (8,3) 1000hp d5; Vendet* (6,12) 1000hp d7; Ryth* (8,11) 1200hp d5; Vesper (13,7) 1000hp d0; Ryth (18,0) 100hp d7; Ren (12,5) 420hp d2
  - us:Vesper Vale basic -> camp
  - us:Ren basic -> camp
- **r79** start: Vesper* (9,2) 1000hp d5; Vendet* (6,11) 1000hp d7; Ryth* (7,10) 1200hp d6; Vesper (13,7) 1000hp d0; Ryth (18,0) 100hp d7; Ren (12,4) 360hp d3
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vesper Vale S0:reset -> Vesper Vale(them)
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - us:Vesper Vale S1:dash -> tile (12, 5)
- **r80** start: Vesper* (9,2) 960hp d4; Vendet* (6,10) 1000hp d7; Ryth* (8,9) 1200hp d5; Vesper (13,4) 1000hp d0; Ryth (18,0) 100hp d5; Ren (13,5) 190hp d1
  - us:Vesper Vale basic -> Vesper Vale(them) [Vesper Vale -55]
  - us:Ren S1:dash -> tile (15, 3)
- **r81** start: Vesper* (10,2) 905hp d3; Vendet* (7,9) 1000hp d6; Ryth* (9,8) 1200hp d4; Vesper (13,4) 940hp d0; Ryth (18,0) 100hp d5; Ren (16,2) 190hp d3
  - us:Vesper Vale basic -> Vesper Vale(them) [Vesper Vale -55]
- **r82** start: Vesper* (11,1) 850hp d3; Vendet* (8,8) 1000hp d5; Ryth* (10,7) 1200hp d3; Vesper (13,4) 880hp d0; Ryth (18,0) 100hp d5; Ren (17,1) 190hp d4
  - us:Vesper Vale basic -> Vesper Vale(them) [Vesper Vale -55]
- **r83** start: Vesper* (12,0) 795hp d4; Vendet* (9,7) 1000hp d4; Ryth* (11,6) 1200hp d2; Vesper (13,4) 820hp d0; Ryth (40,14) 1300hp d27; Ren (18,0) 190hp d5
  - us:Vesper Vale basic -> Ryth(them) [Ryth -55]
  - us:Ren Recall ->
  - them:Ryth S0:aoe -> Vesper Vale(us) [Vesper Vale -100]
- **r84** start: Vesper* (13,0) 795hp d4; Vendet* (10,6) 1000hp d3; Ryth* (11,6) 1145hp d2; Vesper (13,4) 660hp d0; Ryth (39,13) 1300hp d26; Ren (18,0) 190hp d5
  - them:Vendetta S1:dash -> tile (12, 4)
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
  - them:Ryth basic -> Vesper Vale(us) [Vesper Vale -45]
  - them:Ryth S1:reset -> Ryth(them)
  - them:Ryth basic -> Vesper Vale(us) [Vesper Vale -45]
- **r85** start: Vesper* (14,0) 795hp d4; Vendet* (12,4) 1000hp d1; Ryth* (12,5) 1145hp d1; Vesper (13,4) 500hp d0; Ryth (38,12) 1300hp d25; Ren (18,0) 190hp d5
  - us:Vesper Vale basic -> Vendetta(them) [Vendetta -55]
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
  - them:Vendetta S0:reset -> Vendetta(them)
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
  - them:Ryth basic -> Vesper Vale(us) [Vesper Vale -45]
- **r86** start: Vesper* (15,0) 795hp d4; Vendet* (12,4) 945hp d1; Ryth* (12,5) 1145hp d1; Vesper (13,4) 255hp d0; Ryth (38,11) 1300hp d25; Ren (18,0) 190hp d5
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
- **r87** start: Vesper* (15,0) 775hp d3; Vendet* (13,4) 945hp d1; Ryth* (12,5) 1145hp d2; Vesper (14,3) 125hp d0; Ryth (38,10) 1300hp d24; Ren (19,0) 135hp d5
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -55]
  - them:Vesper Vale S0:reset -> Vesper Vale(them)
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -10] Vesper Vale dies

## willow best girl on 00pilgrimage

### Ryth (ours) killed by Heart of Ruin, round 845; fight from round 836

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| us | Vesper Vale | (20,52) | 1600 / 1700 | 0 | 100 | 100 | {'health': 7, 'str': 9} |
| us | Ryth | (16,53) | 960 / 1400 | 0 | 45 | 100 | {'health': 2} |
| them | Prism | (24,47) | 1720 / 1720 | 48 | 42 | 232 | {'health': 17, 'focus': 19, 'str': 3} |
| them | Heart of Ruin | (25,46) | 1702 / 1800 | 0 | 44 | 412 | {'focus': 26, 'str': 4, 'health': 8} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Prism ..VVV, Heart of Ruin ..VVV

Round by round (team B acts first in round 836; teams alternate each round). Actions in engine order:

- **r834** start: Vesper (18,53) 1600hp d4; Ryth (14,53) 960hp d0; Prism* (24,45) 1720hp d10; Heart * (26,46) 1702hp d12
  - them:Heart of Ruin Recall ->
  - them:Prism Recall ->
- **r835** start: Vesper (19,53) 1600hp d4; Ryth (15,53) 960hp d0; Prism* (24,46) 1720hp d9; Heart * (26,45) 1702hp d11
  - them:Heart of Ruin Recall ->
  - them:Prism Recall ->
- **r836** start: Vesper (20,52) 1600hp d4; Ryth (16,53) 960hp d0; Prism* (24,47) 1720hp d8; Heart * (25,46) 1702hp d9
  - them:Prism S1:aoe -> tile (20, 51) [Vesper Vale -304]
  - them:Prism Recall ->
  - them:Heart of Ruin Recall ->
- **r837** start: Vesper (21,51) 1296hp d4; Ryth (17,53) 960hp d0; Prism* (24,47) 1720hp d7; Heart * (25,47) 1702hp d8
  - them:Heart of Ruin S1:dash -> tile (22, 50) [Vesper Vale -635]
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -45]
  - them:Heart of Ruin Recall ->
  - them:Prism S0:cc -> Vesper Vale(us) [Vesper Vale -456]
  - them:Prism Recall ->
- **r838** start: Vesper (21,51) 160hp d3; Ryth (18,53) 960hp d0; Prism* (24,47) 1720hp d6; Heart * (22,50) 1702hp d4
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -45]
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
  - them:Heart of Ruin Recall ->
  - them:Prism Recall ->
- **r839** start: Vesper (21,51) 115hp d2; Ryth (19,53) 960hp d0; Prism* (24,48) 1720hp d5; Heart * (22,50) 1702hp d3
  - them:Prism Recall ->
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -45]
  - them:Heart of Ruin Recall ->
- **r840** start: Vesper (21,52) 70hp d1; Ryth (20,52) 960hp d0; Prism* (23,47) 1720hp d5; Heart * (22,50) 1702hp d2
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -45]
  - them:Heart of Ruin Recall ->
  - them:Prism Recall ->
  - us:Vesper Vale S1:dash -> tile (19, 53)
- **r841** start: Vesper (18,53) 24hp d3; Ryth (21,51) 960hp d0; Prism* (24,48) 1720hp d3; Heart * (22,51) 1702hp d1
  - them:Heart of Ruin basic -> Ryth(us) [Ryth -45]
  - them:Heart of Ruin Recall ->
  - us:Ryth S0:aoe -> Heart of Ruin(them)
  - us:Ryth basic -> Heart of Ruin(them)
  - them:Prism basic -> Ryth(us) [Ryth -42]
  - them:Prism Recall ->
  - us:Vesper Vale Recall ->
- **r842** start: Vesper (18,53) 24hp d3; Ryth (21,51) 872hp d0; Prism* (24,48) 1720hp d3; Heart * (22,50) 1702hp d1
  - us:Ryth basic -> Heart of Ruin(them)
  - them:Prism basic -> Ryth(us) [Ryth -42]
  - them:Prism Recall ->
- **r843** start: Vesper (18,53) 24hp d3; Ryth (21,51) 830hp d0; Prism* (24,48) 1720hp d3; Heart * (22,50) 1702hp d1
  - us:Ryth basic -> Heart of Ruin(them)
  - them:Heart of Ruin basic -> Ryth(us) [Ryth -45]
  - them:Heart of Ruin Recall ->
  - them:Prism basic -> Ryth(us) [Ryth -42]
  - them:Prism Recall ->
- **r844** start: Vesper (18,53) 24hp d3; Ryth (21,51) 636hp d0; Prism* (24,48) 1720hp d3; Heart * (22,51) 1702hp d1
  - them:Heart of Ruin basic -> Ryth(us) [Ryth -45]
  - them:Heart of Ruin Recall ->
  - us:Ryth basic -> Heart of Ruin(them) [Heart of Ruin -47]
  - them:Prism basic -> Ryth(us) [Ryth -42]
  - them:Prism S1:aoe -> tile (20, 50) [Ryth -304]
  - them:Prism Recall ->
- **r845** start: Vesper (18,53) 24hp d3; Ryth (21,51) 244hp d0; Prism* (24,48) 1720hp d3; Heart * (22,50) 1655hp d1
  - them:Heart of Ruin basic -> Ryth(us) [Ryth -46]
  - them:Heart of Ruin S1:dash -> tile (20, 53) [Ryth -199] Ryth dies
  - them:Heart of Ruin Recall ->
  - them:Prism Recall ->

## Intercontinental Fish on 00corners

### Ryth (ours) killed by Vesper Vale, round 195; fight from round 192

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| them | Vesper Vale | (32,15) | 1600 / 1600 | 0 | 235 | 110 | {'str': 36, 'focus': 1, 'health': 6} |
| us | Ryth | (34,15) | 960 / 1300 | 4 | 50 | 100 | {'str': 1, 'health': 1} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Vesper Vale VVVVV

Round by round (team B acts first in round 192; teams alternate each round). Actions in engine order:

- **r190** start: Vesper* (31,15) 1600hp d5; Ryth (36,14) 960hp d0
  - them:Vesper Vale basic -> camp
- **r191** start: Vesper* (31,15) 1600hp d4; Ryth (35,14) 960hp d0
- **r192** start: Vesper* (32,15) 1600hp d2; Ryth (34,15) 960hp d0
  - them:Vesper Vale basic -> Ryth(us) [Ryth -235]
- **r193** start: Vesper* (32,15) 1600hp d2; Ryth (34,15) 725hp d0
  - them:Vesper Vale basic -> Ryth(us) [Ryth -235]
- **r194** start: Vesper* (32,15) 1600hp d2; Ryth (34,15) 490hp d0
  - them:Vesper Vale basic -> Ryth(us) [Ryth -235]
- **r195** start: Vesper* (32,15) 1600hp d3; Ryth (35,14) 255hp d0
  - them:Vesper Vale basic -> Ryth(us) [Ryth -235]
  - them:Vesper Vale S0:reset -> Vesper Vale(them)
  - them:Vesper Vale basic -> Ryth(us) [Ryth -20] Ryth dies

## Intercontinental Fish on 00collision

### Tavi (ours) killed by Vendetta, round 112; fight from round 106

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| them | Vesper Vale | (12,10) | 1540 / 1600 | 45 | 120 | 110 | {'str': 13, 'focus': 1, 'health': 6} |
| them | Heart of Ruin | (15,10) | 1300 / 1300 | 11 | 30 | 100 | {'health': 3} |
| them | Vendetta | (13,9) | 660 / 1000 | 4 | 70 | 100 | {} |
| us | Vesper Vale | (17,11) | 880 / 1000 | 21 | 55 | 100 | {} |
| us | Tavi | (19,12) | 660 / 900 | 19 | 45 | 110 | {} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Vesper Vale VVVVV, Heart of Ruin VVVVV, Vendetta VVVVV

Round by round (team B acts first in round 106; teams alternate each round). Actions in engine order:

- **r104** start: Vesper* (12,10) 1540hp d7; Heart * (13,8) 1300hp d6; Vendet* (13,9) 680hp d6; Vesper (17,11) 900hp d2; Tavi (19,12) 700hp d0
  - them:Vesper Vale basic -> camp
  - us:Vesper Vale basic -> camp
  - us:Tavi basic -> camp
  - them:Vendetta basic -> camp
  - them:Vendetta S0:reset -> Vendetta(them)
  - them:Vendetta basic -> camp
- **r105** start: Vesper* (12,10) 1540hp d7; Heart * (14,9) 1300hp d5; Vendet* (14,10) 680hp d5; Vesper (17,11) 880hp d2; Tavi (19,12) 680hp d0
  - them:Vesper Vale basic -> camp
  - us:Vesper Vale basic -> Heart of Ruin(them)
  - us:Tavi basic -> camp
- **r106** start: Vesper* (12,10) 1540hp d7; Heart * (15,10) 1300hp d4; Vendet* (13,9) 660hp d6; Vesper (17,11) 880hp d2; Tavi (19,12) 660hp d0
  - them:Vesper Vale basic -> camp
  - us:Vesper Vale basic -> Heart of Ruin(them) [Heart of Ruin -55]
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -31]
  - us:Tavi S1:cc -> Heart of Ruin(them) [Heart of Ruin -154]
  - us:Tavi basic -> Heart of Ruin(them) [Heart of Ruin -45]
  - them:Vendetta S1:dash -> tile (15, 11)
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
- **r107** start: Vesper* (12,10) 1540hp d7; Heart * (16,11) 1026hp d3; Vendet* (16,12) 660hp d3; Vesper (17,11) 779hp d2; Tavi (19,12) 640hp d0
  - them:Vesper Vale S1:dash -> tile (14, 11)
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -120]
  - us:Vesper Vale basic -> Vendetta(them) [Vendetta -55]
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
  - us:Tavi basic -> Vendetta(them) [Vendetta -45]
- **r108** start: Vesper* (14,11) 1540hp d5; Heart * (16,11) 1006hp d3; Vendet* (16,12) 560hp d3; Vesper (17,11) 589hp d2; Tavi (19,12) 620hp d0
  - them:Vendetta basic -> Vesper Vale(us) [Vesper Vale -70]
  - us:Vesper Vale basic -> Vendetta(them) [Vendetta -55]
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -120]
  - them:Vesper Vale S0:reset -> Vesper Vale(them)
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -120]
  - us:Tavi basic -> Vendetta(them) [Vendetta -45]
  - them:Heart of Ruin basic -> Vesper Vale(us) [Vesper Vale -33]
  - them:Heart of Ruin S1:dash -> tile (18, 11) [Vesper Vale -167, Tavi -167]
- **r109** start: Vesper* (14,11) 1540hp d5; Heart * (18,11) 1006hp d1; Vendet* (16,12) 460hp d3; Vesper (17,11) 59hp d2; Tavi (19,12) 433hp d0
  - them:Vesper Vale basic -> Vesper Vale(us) [Vesper Vale -59] Vesper Vale dies
  - them:Heart of Ruin basic -> Tavi(us) [Tavi -33]
- **r110** start: Vesper* (14,11) 1522hp d5; Heart * (18,11) 1006hp d1; Vendet* (17,12) 460hp d2; Tavi (19,12) 380hp d0
  - them:Vendetta basic -> Tavi(us) [Tavi -70]
  - us:Tavi basic -> Vendetta(them) [Vendetta -45]
  - them:Heart of Ruin basic -> Tavi(us) [Tavi -33]
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
- **r111** start: Vesper* (15,12) 1504hp d4; Heart * (18,11) 1006hp d1; Vendet* (18,13) 415hp d1; Tavi (19,12) 256hp d0
  - them:Heart of Ruin basic -> Tavi(us) [Tavi -33]
  - them:Vendetta basic -> Tavi(us) [Tavi -70]
- **r112** start: Vesper* (16,13) 1504hp d2; Heart * (19,11) 1006hp d1; Vendet* (18,13) 395hp d1; Tavi (18,12) 153hp d0
  - them:Vesper Vale basic -> Tavi(us) [Tavi -120]
  - them:Vendetta basic -> Tavi(us) [Tavi -13] Tavi dies
  - them:Vendetta S0:reset -> Vendetta(them)

## vc? on 00contest

### Ren (ours) killed by Marcella, round 45; fight from round 34

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| them | Vesper Vale | (27,17) | 1000 / 1000 | 0 | 55 | 100 | {} |
| them | Vendetta | (27,14) | 1000 / 1000 | 0 | 70 | 100 | {} |
| them | Marcella | (27,15) | 1200 / 1200 | 0 | 45 | 60 | {} |
| them | Heart of Ruin | (26,21) | 1000 / 1000 | 0 | 30 | 100 | {} |
| us | Vendetta | (28,22) | 1000 / 1000 | 0 | 70 | 100 | {} |
| us | Ryth | (30,22) | 1200 / 1200 | 0 | 45 | 100 | {} |
| us | Ren | (29,22) | 900 / 900 | 0 | 35 | 100 | {} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Vesper Vale ....., Vendetta ....., Marcella ....., Heart of Ruin ....b

Round by round (team B acts first in round 34; teams alternate each round). Actions in engine order:

- **r32** start: Vesper* (25,15) 1000hp d7; Vendet* (27,16) 1000hp d6; Marcel* (26,17) 1200hp d6; Heart * (26,19) 1000hp d6; Vendet (31,22) 1000hp d1; Ryth (31,23) 1200hp d1; Ren (32,22) 900hp d0
- **r33** start: Vesper* (26,16) 1000hp d6; Vendet* (27,15) 1000hp d7; Marcel* (27,16) 1200hp d6; Heart * (26,20) 1000hp d6; Vendet (31,22) 1000hp d1; Ryth (31,23) 1200hp d1; Ren (32,22) 900hp d0
  - us:Ren S1:dash -> tile (30, 22)
  - us:Vendetta S1:dash -> tile (29, 23)
- **r34** start: Vesper* (27,17) 1000hp d5; Vendet* (27,14) 1000hp d8; Marcel* (27,15) 1200hp d7; Heart * (26,21) 1000hp d3; Vendet (28,22) 1000hp d1; Ryth (30,22) 1200hp d1; Ren (29,22) 900hp d0
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
- **r35** start: Vesper* (27,17) 1000hp d5; Vendet* (28,13) 1000hp d9; Marcel* (27,16) 1200hp d6; Heart * (26,21) 1000hp d2; Vendet (27,21) 970hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
  - us:Vendetta basic -> Heart of Ruin(them)
- **r36** start: Vesper* (26,18) 1000hp d4; Vendet* (27,14) 1000hp d8; Marcel* (26,17) 1200hp d5; Heart * (26,21) 1000hp d2; Vendet (27,21) 940hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
  - us:Vendetta basic -> Heart of Ruin(them)
- **r37** start: Vesper* (25,19) 1000hp d3; Vendet* (26,15) 1000hp d7; Marcel* (25,18) 1200hp d4; Heart * (26,21) 1000hp d2; Vendet (27,21) 910hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -60]
- **r38** start: Vesper* (26,18) 1000hp d4; Vendet* (25,16) 1000hp d6; Marcel* (25,19) 1200hp d3; Heart * (26,21) 940hp d2; Vendet (27,21) 880hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -32]
- **r39** start: Vesper* (26,19) 1000hp d3; Vendet* (25,17) 1000hp d5; Marcel* (25,20) 1200hp d3; Heart * (26,21) 870hp d2; Vendet (27,21) 848hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -32]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
- **r40** start: Vesper* (27,18) 1000hp d4; Vendet* (24,18) 1000hp d4; Marcel* (25,21) 1200hp d3; Heart * (26,21) 800hp d2; Vendet (27,21) 816hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - them:Marcella S1:damage -> Vendetta(us) [Vendetta -120]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -34]
- **r41** start: Vesper* (26,19) 1000hp d3; Vendet* (25,19) 1000hp d3; Marcel* (25,21) 1200hp d3; Heart * (26,21) 730hp d2; Vendet (27,21) 662hp d1; Ryth (29,23) 1200hp d1; Ren (28,22) 900hp d0
  - us:Ren S1:dash -> tile (26, 20)
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -34]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
- **r42** start: Vesper* (27,18) 1000hp d1; Vendet* (25,20) 1000hp d2; Marcel* (26,22) 1200hp d3; Heart * (26,21) 660hp d2; Vendet (27,21) 628hp d2; Ryth (28,22) 1200hp d3; Ren (27,19) 800hp d0
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vesper Vale S0:reset -> Vesper Vale(them)
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vendetta basic -> Ren(us) [Vendetta -20, Ren -70]
  - them:Vendetta S0:reset -> Vendetta(them)
  - them:Vendetta basic -> Ren(us) [Vendetta -20, Ren -70]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -35]
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
  - us:Vendetta basic -> Heart of Ruin(them)
- **r43** start: Vesper* (27,18) 960hp d1; Vendet* (26,20) 960hp d1; Marcel* (25,21) 1200hp d2; Heart * (26,21) 660hp d2; Vendet (27,21) 593hp d2; Ryth (28,22) 1200hp d3; Ren (27,19) 550hp d0
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vendetta basic -> Ren(us) [Vendetta -20, Ren -70]
  - them:Heart of Ruin basic -> Ren(us) [Ren -35]
  - us:Ren S0:cc -> Heart of Ruin(them) [Heart of Ruin -15]
  - us:Ren basic -> Heart of Ruin(them) [Heart of Ruin -35]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
- **r44** start: Vesper* (27,18) 940hp d1; Vendet* (26,20) 940hp d1; Marcel* (25,21) 1200hp d2; Heart * (27,20) 540hp d1; Vendet (27,21) 593hp d2; Ryth (28,22) 1200hp d3; Ren (27,19) 390hp d0
  - us:Ren basic -> Heart of Ruin(them) [Heart of Ruin -35]
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vendetta basic -> Ren(us) [Vendetta -20, Ren -70]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]
- **r45** start: Vesper* (27,18) 920hp d1; Vendet* (26,20) 920hp d1; Marcel* (25,21) 1200hp d2; Heart * (27,20) 435hp d1; Vendet (27,21) 593hp d2; Ryth (28,22) 1200hp d3; Ren (27,19) 175hp d0
  - them:Vesper Vale basic -> Ren(us) [Vesper Vale -20, Ren -55]
  - them:Vendetta basic -> Ren(us) [Vendetta -20, Ren -70]
  - them:Marcella basic -> Ren(us) [Marcella -20, Ren -45]
  - them:Marcella S0:reset -> Marcella(them)
  - them:Marcella basic -> Ren(us) [Marcella -20, Ren -5] Ren dies
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -38]
  - us:Vendetta basic -> Heart of Ruin(them) [Heart of Ruin -70]

## willow best girl on 00packs

### Vendetta (ours) killed by Vesper Vale, round 114; fight from round 110

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| them | Prism | (9,9) | 700 / 700 | 16 | 35 | 144 | {'focus': 8} |
| them | Vesper Vale | (15,14) | 820 / 1000 | 0 | 110 | 100 | {'str': 11} |
| them | Heart of Ruin | (11,17) | 920 / 1000 | 0 | 30 | 136 | {'focus': 3} |
| us | Vendetta | (14,18) | 640 / 1200 | 12 | 70 | 100 | {'health': 2} |
| us | Vesper Vale | (14,19) | 1200 / 1200 | 6 | 60 | 100 | {'str': 1, 'health': 2} |
| us | Tavi | (17,25) | 975 / 975 | 6 | 50 | 110 | {'str': 1, 'health': 1} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Prism ....., Vesper Vale ..VVV, Heart of Ruin ..VVV

Round by round (team B acts first in round 110; teams alternate each round). Actions in engine order:

- **r108** start: Prism* (7,7) 700hp d13; Vesper* (15,13) 820hp d7; Heart * (11,17) 920hp d5; Vendet (16,20) 640hp d0; Vesper (15,20) 1200hp d1; Tavi (18,24) 975hp d4
  - us:Tavi S1:cc -> camp
  - them:Heart of Ruin basic -> camp
  - them:Heart of Ruin Recall ->
  - us:Vesper Vale basic -> camp
  - them:Vesper Vale basic -> camp
  - them:Vesper Vale Recall ->
  - them:Prism Recall ->
- **r109** start: Prism* (8,8) 700hp d11; Vesper* (15,13) 820hp d6; Heart * (11,17) 920hp d4; Vendet (15,19) 640hp d0; Vesper (15,20) 1200hp d1; Tavi (18,24) 975hp d5
  - them:Heart of Ruin Recall ->
  - them:Vesper Vale Recall ->
  - them:Prism Recall ->
- **r110** start: Prism* (9,9) 700hp d9; Vesper* (15,14) 820hp d4; Heart * (11,17) 920hp d3; Vendet (14,18) 640hp d0; Vesper (14,19) 1200hp d1; Tavi (17,25) 975hp d7
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
  - them:Heart of Ruin Recall ->
  - us:Tavi basic -> camp
  - them:Vesper Vale basic -> Vendetta(us) [Vendetta -110]
  - them:Vesper Vale Recall ->
  - us:Vesper Vale basic -> Heart of Ruin(them)
  - them:Prism Recall ->
- **r111** start: Prism* (10,10) 700hp d7; Vesper* (15,14) 820hp d3; Heart * (11,17) 920hp d2; Vendet (13,17) 530hp d0; Vesper (14,19) 1200hp d2; Tavi (17,25) 935hp d8
  - them:Heart of Ruin Recall ->
  - them:Vesper Vale basic -> Vendetta(us) [Vendetta -110]
  - them:Vesper Vale Recall ->
  - us:Tavi basic -> camp
  - them:Prism Recall ->
  - us:Vesper Vale basic -> Heart of Ruin(them)
- **r112** start: Prism* (10,11) 700hp d5; Vesper* (15,14) 820hp d3; Heart * (11,17) 920hp d1; Vendet (12,16) 420hp d0; Vesper (14,19) 1200hp d3; Tavi (17,25) 895hp d9
  - us:Vendetta basic -> Heart of Ruin(them)
  - them:Prism S1:aoe -> tile (11, 15) [Vendetta -168]
  - them:Prism Recall ->
  - us:Tavi basic -> camp
  - them:Vesper Vale basic -> Vendetta(us) [Vendetta -110]
  - them:Vesper Vale Recall ->
  - us:Vesper Vale basic -> Heart of Ruin(them) [Heart of Ruin -46]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -32]
  - them:Heart of Ruin Recall ->
- **r113** start: Prism* (10,11) 700hp d5; Vesper* (15,14) 820hp d3; Heart * (11,17) 874hp d1; Vendet (12,16) 110hp d0; Vesper (14,19) 1200hp d3; Tavi (17,25) 855hp d9
  - them:Vesper Vale basic -> Vendetta(us) [Vendetta -110]
  - them:Vesper Vale Recall ->
  - us:Vendetta S1:dash -> tile (14, 14)
  - them:Heart of Ruin Recall ->
  - us:Tavi basic -> camp
  - them:Prism Recall ->
  - us:Vesper Vale basic -> Heart of Ruin(them) [Heart of Ruin -60]
- **r114** start: Prism* (11,12) 700hp d4; Vesper* (15,14) 820hp d1; Heart * (11,17) 814hp d4; Vendet (15,15) 0hp d0; Vesper (14,19) 1200hp d4; Tavi (17,25) 815hp d10
  - them:Prism Recall ->
  - us:Tavi basic -> camp
  - them:Heart of Ruin Recall ->
  - us:Vesper Vale basic -> Heart of Ruin(them) [Heart of Ruin -60]
  - them:Vesper Vale basic -> Vendetta(us)  Vendetta dies
  - them:Vesper Vale Recall ->

## vc? on 00gemfight

### Vendetta (ours) killed by Vendetta, round 96; fight from round 87

Champions within 10 tiles at the start (stats rebuilt from purchases):

| side | champion | pos | HP / max | gems | strength | focus | items (points by stat) |
|---|---|---|---|---|---|---|---|
| us | Vendetta | (8,1) | 1100 / 1100 | 10 | 76 | 100 | {'str': 1, 'health': 1} |
| them | Vesper Vale | (10,10) | 575 / 1000 | 0 | 55 | 100 | {} |
| them | Vendetta | (11,0) | 1000 / 1000 | 7 | 70 | 100 | {} |
| them | Marcella | (12,0) | 1200 / 1200 | 0 | 45 | 60 | {} |
| them | Heart of Ruin | (13,0) | 1000 / 1000 | 0 | 30 | 100 | {} |

Their visibility to us in the 5 rounds before the first hit (V seen, . unseen, b unseen in a bush): Vesper Vale VVVV., Vendetta VVVVV, Marcella VVVVV, Heart of Ruin VVVVV

Round by round (team A acts first in round 87; teams alternate each round). Actions in engine order:

- **r85** start: Vendet (8,1) 1100hp d0; Vesper* (10,8) 575hp d7; Vendet* (13,0) 1000hp d5; Marcel* (14,0) 1200hp d6; Heart * (15,0) 1000hp d7
- **r86** start: Vendet (8,1) 1100hp d0; Vesper* (10,9) 575hp d8; Vendet* (12,0) 1000hp d4; Marcel* (13,0) 1200hp d5; Heart * (14,0) 1000hp d6
  - them:Vesper Vale S1:dash -> tile (11, 11)
- **r87** start: Vendet (8,1) 1100hp d0; Vesper* (10,10) 575hp d9; Vendet* (11,0) 1000hp d3; Marcel* (12,0) 1200hp d4; Heart * (13,0) 1000hp d5
  - them:Vendetta S1:dash -> tile (9, 0)
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - us:Vendetta basic -> Vendetta(them) [Vendetta -76]
  - them:Marcella S1:damage -> Vendetta(us) [Vendetta -120]
- **r88** start: Vendet (8,1) 910hp d0; Vesper* (9,9) 575hp d8; Vendet* (9,0) 924hp d1; Marcel* (12,0) 1200hp d4; Heart * (12,1) 1000hp d4
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - them:Vendetta S0:reset -> Vendetta(them)
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - them:Heart of Ruin S0:shield -> Heart of Ruin(them)
  - us:Vendetta basic -> Vendetta(them) [Vendetta -76]
- **r89** start: Vendet (8,1) 770hp d0; Vesper* (10,8) 575hp d7; Vendet* (9,0) 848hp d1; Marcel* (11,0) 1200hp d3; Heart * (11,1) 1000hp d3
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - us:Vendetta basic -> Vendetta(them) [Vendetta -76]
  - them:Heart of Ruin S1:dash -> tile (9, 1) [Vendetta -150]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
- **r90** start: Vendet (8,1) 520hp d0; Vesper* (10,9) 575hp d8; Vendet* (9,0) 772hp d1; Marcel* (10,0) 1200hp d2; Heart * (9,1) 1000hp d1
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
- **r91** start: Vendet (8,1) 420hp d0; Vesper* (9,8) 575hp d7; Vendet* (9,0) 772hp d1; Marcel* (10,0) 1200hp d2; Heart * (9,1) 1000hp d1
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - us:Vendetta basic -> Vendetta(them) [Vendetta -76]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
- **r92** start: Vendet (8,1) 320hp d0; Vesper* (10,9) 575hp d8; Vendet* (9,0) 696hp d1; Marcel* (10,0) 1200hp d2; Heart * (9,1) 1000hp d1
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - them:Heart of Ruin basic -> Vendetta(us) [Vendetta -30]
  - us:Vendetta S1:dash -> tile (6, 0)
- **r93** start: Vendet (5,0) 220hp d0; Vesper* (9,8) 575hp d8; Vendet* (9,0) 696hp d4; Marcel* (10,0) 1200hp d5; Heart * (9,1) 1000hp d4
  - us:Vendetta Recall ->
- **r94** start: Vendet (5,0) 220hp d0; Vesper* (8,9) 575hp d9; Vendet* (8,0) 696hp d3; Marcel* (9,0) 1200hp d4; Heart * (8,1) 1000hp d3
- **r95** start: Vendet (5,0) 220hp d0; Vesper* (9,10) 575hp d10; Vendet* (7,0) 696hp d2; Marcel* (8,0) 1200hp d3; Heart * (7,1) 1000hp d2
  - them:Vendetta basic -> Vendetta(us) [Vendetta -70]
  - them:Marcella S1:damage -> Vendetta(us) [Vendetta -120]
- **r96** start: Vendet (4,0) 30hp d0; Vesper* (9,11) 575hp d11; Vendet* (6,0) 696hp d2; Marcel* (8,0) 1200hp d4; Heart * (6,1) 1000hp d2
  - them:Vendetta basic -> Vendetta(us) [Vendetta -30] Vendetta dies
