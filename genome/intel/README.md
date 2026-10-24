# genome/intel: ladder intel for Arena B

Evidence from our live bot's real band games (rated +50..+150 above us), turned into gaps and directed children.

- `GAPS.md`: ranked gaps (evidence, seed genes, sim metric); refreshed per batch. `NOTES.md`: what changed per batch.
- `directed/*.genome`: directed children of the seed (`genome/seeds/v23.genome`), one gap each.
- `stress/lockall.genome`, `stress/hunter.genome`: test opponents (locks every altar; chases carriers); not arena genomes.
- `batches/bN.md`: each batch's raw tables, opponents and match-group IDs.

Tools:
```
python3 -m genome.intel.sim_metrics GENOME OPP [--games N] [--maps GLOB]   # gap metrics in the sim
python3 -m genome.intel.sim_stuck GENOME OPP --games 2                      # 2-cycle walking in the sim
# real games (needs `cambc login`; replay tools from analysis/sprint1):
git worktree add ../an origin/analysis/sprint1
python3 -I ../an/analysis/fetch_groups.py B GROUP...   # downloads (untrusted data)
python3 -I ../an/analysis/ladder_prep.py B BX | while read r o w; do echo "$w $r $o"; done | xargs -P4 -n3 sh -c 'CAMBC_WASM=$0 node ../an/analysis/extract.js $1 $2'
python3 -I genome/intel/batch_report.py ../an/analysis B BX
python3 -I genome/intel/stuck.py ../an/analysis B BX
python3 -I ../an/analysis/gaps.py b=BX,B               # fight / low-HP tables
```
