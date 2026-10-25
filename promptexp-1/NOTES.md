# promptexp-1 notes

- Type-check bug (found 00:09 UTC Oct 25, fixed in genome/search 1bcb3d44): T4/T5 tell the model that B "stays for its other
  callers". When A was B's only caller, A no longer calling B leaves B unused and apply_mutation's prune deletes it; the
  check then rejected the child ("the link's genes must stay in the program") although the reply did what was asked.
  Count from children.jsonl: 14 of A1's 19 T4/T5 type-check rejections (after the retry) were this message. Those
  children were rejected before scoring, so the primary result (A0 39/120 vs A1 21/120 better, McNemar p = 0.999) is
  unchanged as run; with the fixed check A1's T4+T5 yield would have been up to ~39 valid of 48 instead of 25.
- Null caveat: the 40 nulls on 648bafd are degenerate (17 exactly 0, only 2 positive), so null p95 = 0 and "better" means
  anchor diff > 0. Counts above fixed bars (> +5: A0 10, A1 3; > +10: 3 vs 2; > +20: 1 vs 1).
- panel.jsonl: the 13 children above +5 and their parents vs panel-A3-db2's 13 opponents. On the 7 held-out opponents
  alone 7 of 13 gain and 6 lose; only c64 (A0 T3, +16 of 560) clearly gains.
