"""Check the calibrated fuel model turn by turn against profiled real turns.

For every profiled turn (oracle/run_bot_profile.sh) the model in docs/fuel_calibration.json is
applied to the logged block/API features and compared with the turn's measured fuel (profiler
overhead removed). Usage: python3 oracle/tools/fuel_validate.py /tmp/prof/POLICY/MAP...
"""
import json, math, os, re, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
cal = json.load(open(f"{REPO}/docs/fuel_calibration.json"))
src = open(f"{REPO}/interp/src/policy.cpp").read()
BLOCKS = re.findall(r'X\(\w+,\s*"([^"]+)"\)', src[src.index("#define INTERP_BLOCKS(X)"):src.index("enum class Op")])
la, lb, lc = cal["turn_loop_fit"]

def mfeat(mp):
    d = json.load(open(f"{REPO}/oracle/fixtures/maps/{mp}.json"))
    W, H = d["metadata"]["width"], d["metadata"]["height"]
    return dict(H=H, ch=math.ceil(W / 8) * math.ceil(H / 8), camps=sum(len(g["camps"]) for g in d["camp_layout"]),
                groups=len(d["camp_layout"]), altars=sum(bin(x).count("1") for x in bytes.fromhex(d["masks"]["altars"])))

def model(name, f, exp, dbits, occ):
    r = cal["ops"].get(name)
    if r is None:
        return 0 if name.startswith("api:") else 200, False
    val = {"1": 1, "H": f["H"], "ch": f["ch"], "camps": f["camps"], "groups": f["groups"], "altars": f["altars"], "exp*ch": exp * f["ch"],
           "exp": exp, "dbits": dbits, "occ": occ, "occ*H": occ * f["H"]}
    return sum(c * val[t] for c, t in zip(r["coef"], r["feats"])), True

for run in sys.argv[1:]:
    run = run.rstrip("/"); mp = os.path.basename(run)
    f = mfeat(mp); ovh = None; api = None; errs = []; act_tot = pred_tot = 0
    cur_pred = 0; nsc = 0
    for line in open(f"{run}/prof.txt"):
        p = line.split()
        if not p: continue
        if p[0] == "@@OVH" and ovh is None: ovh = int(p[1])
        elif p[0] == "@@APINAMES": api = p[1].split(",")
        elif p[0] == "@@T": cur_pred = 0; nsc = 0; nblk = 0
        elif p[0] == "@@S":
            op, sf, ex, db, cex, cdb, oc = map(int, p[1:8])
            if op in (509, 510): continue
            nsc += 1; nblk += op < 1000
            name = ("api:" + api[op - 1000]) if op >= 1000 else (("exec:" if op >= 256 else "") + BLOCKS[op % 256])
            v, _ = model(name, f, ex + cex, db + cdb, oc); cur_pred += v
        elif p[0] == "@@TURN":
            cur_pred += max(0, la + lb * nblk + lc * nblk * f["H"])
            actual = int(p[1]) - nsc * ovh
            errs.append((cur_pred - actual) / max(actual, 1)); act_tot += actual; pred_tot += cur_pred
    errs.sort(); n = len(errs)
    print(f"{os.path.basename(os.path.dirname(run))}/{mp}: {n} turns, total predicted/actual {pred_tot / act_tot:.3f}, per-turn error median {errs[n // 2]:+.1%}, "
          f"10-90% [{errs[n // 10]:+.1%}, {errs[9 * n // 10]:+.1%}]")
