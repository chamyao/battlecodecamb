"""GAP_LIST gem-conversion hand tests on v21 (FunSearch lead; analysis docs/GAP_LIST.md on PR #5): bank rules
(policies/candidates/tune-v21-bank-*.policy) vs v21, 2 x 400 (seeds 9681/9682): win rate, gems lost to champions,
conversion (gems submitted / gems captured), tributes per game (interp_eval capture metrics, coord/capture-metric)."""
import glob, sys
sys.path.insert(0, '.')
from funsearch.race import *

b21 = compile_file("policies/tune-v21.policy")
names = sys.argv[1:] or sorted(f.split("tune-v21-bank-")[1][:-7] for f in glob.glob("policies/candidates/tune-v21-bank-*.policy"))
for k in names:
    a = compile_file(f"policies/candidates/tune-v21-bank-{k}.policy")
    rs = [h2h(a, b21, 400, s) for s in (9681, 9682)]
    w = sum(r["win_rate"] for r in rs) / 2
    m = lambda key, i: sum(r[key][i] for r in rs) / 2
    conv = [sum(r["a_gems"] if i == 0 else r["b_gems"] for r in rs) / 2 / m("gems_captured", i) for i in (0, 1)]
    print(f"{k:10s} win {w:.4f} | lost_to_champs {m('gems_lost_to_champs', 0):.1f} (v21 {m('gems_lost_to_champs', 1):.1f}) | "
          f"conversion {conv[0]:.3f} (v21 {conv[1]:.3f}) | tributes {m('tributes', 0):.1f} (v21 {m('tributes', 1):.1f}) | "
          f"captures {m('captures', 0):.1f} ({m('captures', 1):.1f})", flush=True)
