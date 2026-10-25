# Z-18a mutation writer notes
Local evaluator: genome_eval (deterministic: 40 maps x 2 sides = 80 distinct games; more games / seeds repeat).
Big wins (local, vs parent):
- draft Vendetta>VV>Tavi>Ryth>Ren (VV first or HoR worse)
- casts: damage/stun at champions/camps (+7 arena pts early)
- heal on spawn before leaving; full heal slightly better
- recall only when nothing threatens (vs any 0.69); later: no recall while taking damage (HIT) (vs v23 0.29->0.41)
- shop: durability-health emblem, jungle-health emblem, then power strength (0.71 vs power-only); power-health last is much worse; bruiser after ~ +0.04
- Vendetta/Tavi/Marcella attack reset + dash travel (0.65/0.70)
- retreat home field when <0.35 under threat (deaths 28->17); threshold 0.3 best (0.4 much worse 0.30)
- retreat moves must ignore the danger penalty (raw field gain) (0.66)
- goal field cache by goal-set key (fuel), stuck-blocker attack, dead-camp-aware goals (fixes the-farm etc)
- walk_nearest goal + field_avoid around units; consider() to skip listing (fuel: suspensions 600->350 on big maps)
- skip sleeping monolith/golem camps (deaths vs v23 16->12)
Neutral/negative: bag thresholds >8 (worse), distance-scaled bag, shared-memory team target (0.10!), treasure shards, bigger retreat thresholds, many small param tweaks.
