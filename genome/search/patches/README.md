# Inline patches on 7e40b6f (the Arena A / Z code), as applied by the EC2 jobs on jobs/genome

- arenaA5-eval.patch: distinct-games matchmaking + --bot-seeds in every match (arenaA-5, arenaZ-3).
- rng-salt.patch: --rng-salt N shifts the arena's random stream (arenaZ-2: 1, arenaZ-7: 2).
- a1-mutate.patch: --a1-mutate, every mutation through a1op.py (arenaZ-4; needs a1op.py and promptexp.py copied in).
- no-ladder-obs.patch: drops funsearch.catalog's "Observations from today's top-12 ladder games" block from the operator
  system prompt (arenaZ-6).
- arenaZ5-queue.patch: --llm-queue DIR / --queue-timeout / --max-births, every Claude call through queuellm.py (arenaZ-5,
  M2 session mutator; needs queuellm.py and queuewait.py copied in). setup_z5.sh builds such a checkout at runtime 648bafd.
