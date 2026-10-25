# Arena B: the directed ladder-fix loop

First validated on v28 = a61188-mono (Oct 25): band batch 5 went 18-32 vs v27's 13-37 on the same
50 matchups (5 flips to a win, 0 to a loss, p ~0.03), monolith deaths 1.86 -> 0.58 per game.

1. **Tag the top loss cause** of the live bot from real games: ranked losses (genome lead) and the
   paired band batch (intel, `genome/intel/batch_report.py`, `paired.py`, GAPS.md). The cause needs
   a mechanism (which rule/gene, which maps), not just a correlate.
2. **Check the sim reproduces it** on the named maps (e.g. non-champion deaths on 00great-wall).
   If it doesn't, the fix can't be tested in the sim: study real replays first, or build a stress
   opponent that reproduces it.
3. **Narrow directed edit on the live genome**, grafted by gene ID (`genome/intel/tools/graft.py`).
   Try the smallest variant too.
4. **Sim gate, bot seeds** (`--bot-seeds`, 80 distinct games per pairing, pinned runtime):
   >= 40/80 vs the live bot, the target metric clearly down on the target maps, no drop > 3/80 vs
   any of the gatekeeper's anchors.
5. **Real cambc** (`genome/arenab/real_gate.sh`, both bots built on the same runtime): vs the live
   genome (>= 42/80, 0 crashes), plus a smoke on the target maps. Real cambc decides; the sim
   picks the per-game winner only ~2/3-4/5 of the time.
6. **Upload** (genome lead, under Cham's "upload first, validate later"), then switch the gate-ref
   (search session) and add the new live bot as a weight-2 anchor in Arena B.
7. **Band batch** on b1's plan (intel, 10 groups), paired vs the previous batch: record, sign test,
   the target metric. Revert if it validates worse.

Arena B's search (session-mutator relay legs on `arenab/b14-relay`) runs alongside. Its anchors
include the band-style stress opponents and the live bot, so its candidates go through steps 4-7 too.
