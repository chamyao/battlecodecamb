# Z-19d writer notes (learned from feedback + local tests)
- Casting abilities (damage/stun on champions & camps, shield/heal/reset in fights) = biggest early jump (0.5 -> 0.8 vs starter).
- Draft: ranged team (Vesper, Stellar, Tavi, Cassi, Willow) >> default/melee; draft order otherwise ~irrelevant.
- Buy strength shards (item_strength>0, cost>=30); item_passive never fires for shards (family choice not reachable).
- Exclude golem/monolith camps; gem clusters first when close (+8) is mildly positive.
- Retreat when hurt under threat + recall only when safe (threat==0): big gain (0.67-0.72 vs parent).
- Wake new camps only above 50% hp, but always finish awake camps even with a full bag: +0.1 panel.
- Home-when-hurt goal field (walk home at <30-40% hp with no gems): consistently +.
- Retreat when outnumbered by enemy champions (ne > na+1 within 5, hp<0.7): +0.06 panel over 400 games.
- Neutral/negative: clumping the team (very bad), spread-out rule, damage-race camp filter (fewer deaths, fewer gems),
  call-for-help via shared memory (worse), punishing enemy tributes (worse), jungle/treasure buys (unreachable),
  goals value tweaks (elk first, no wolves), fuel caching of threat (no change in suspensions).
- Local head-to-head vs parent misled early; panel vs 8 current top genomes predicts arena rating better.
