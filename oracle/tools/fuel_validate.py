"""Check the calibrated fuel model against the deploy bot's real fuel, round by round.

For every run of oracle/run_bot_profile.sh, the model in docs/fuel_calibration.json (per-call
fits, the step loop and the profiler-distortion correction) is applied to each logged turn's
blocks and API calls, and each fully logged round (every champion logs on the same turns) is
compared with the real fuel the unpatched bot used in that round of the identical game
(plain/*.repl26a). Runs without a plain game are compared with the profile's own turn totals
(profiler overhead removed; uncorrected model).
Usage: python3 oracle/tools/fuel_validate.py /tmp/prof/POLICY/MAP...
"""
import glob, json, math, os, re, sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fuel_file import turns as fuel_turns
cal = json.load(open(f"{REPO}/docs/fuel_calibration.json"))
src = open(f"{REPO}/interp/src/policy.cpp").read()
BLOCKS = re.findall(r'X\(\w+,\s*"([^"]+)"\)', src[src.index("#define INTERP_BLOCKS(X)"):src.index("enum class Op")])
la, lb, lc = cal["turn_loop_fit"]
dist = cal.get("distortion", dict(scale=1, per_block=0, per_api=0, per_turn=0))

def mfeat(mp):
    d = json.load(open(f"{REPO}/oracle/fixtures/maps/{mp}.json"))
    W, H = d["metadata"]["width"], d["metadata"]["height"]
    return dict(H=H, ch=math.ceil(W / 8) * math.ceil(H / 8), camps=sum(len(g["camps"]) for g in d["camp_layout"]),
                groups=len(d["camp_layout"]), altars=sum(bin(x).count("1") for x in bytes.fromhex(d["masks"]["altars"])))

def model(name, f, exp, dbits, occ):
    r = cal["ops"].get(name)
    if r is None:
        return 0
    val = {"1": 1, "H": f["H"], "ch": f["ch"], "camps": f["camps"], "groups": f["groups"], "altars": f["altars"], "exp*ch": exp * f["ch"],
           "exp": exp, "dbits": dbits, "occ": occ, "occ*H": occ * f["H"], "occ*ch": occ * f["ch"]}
    return sum(c * val[t] for c, t in zip(r["coef"], r["feats"]))

def profile_turns(run, f):
    """[(turn_no, model fuel, blocks, api calls, profile fuel)] per logged turn."""
    ovh = api = None
    out = []
    for line in open(f"{run}/prof.txt"):
        p = line.split()
        if not p: continue
        if p[0] == "@@OVH" and ovh is None: ovh = int(p[1])
        elif p[0] == "@@APINAMES": api = p[1].split(",")
        elif p[0] == "@@T": tno = int(p[1]); m = 0; nb = na = 0
        elif p[0] == "@@S":
            op, sf, ex, db, cex, cdb, oc = map(int, p[1:8])
            if op in (509, 510): continue
            if op >= 1000: na += 1
            else: nb += 1
            name = ("api:" + api[op - 1000]) if op >= 1000 else (("exec:" if op >= 256 else "") + BLOCKS[op % 256])
            m += model(name, f, ex + cex, db + cdb, oc)
        elif p[0] == "@@TURN":
            m += la + lb * nb + lc * nb * f["H"]
            out.append((tno, m, nb, na, int(p[1]) - (nb + na) * ovh))
    return out

def summary(label, pairs):
    errs = sorted((p - a) / max(a, 1) for p, a in pairs); n = len(errs)
    tp, ta = sum(p for p, _ in pairs), sum(a for _, a in pairs)
    print(f"{label}: {n} rounds, total predicted/actual {tp / ta:.3f}, per-round error median {errs[n // 2]:+.1%}, "
          f"10-90% [{errs[n // 10]:+.1%}, {errs[9 * n // 10]:+.1%}]")

for run in sys.argv[1:]:
    run = run.rstrip("/"); mp = os.path.basename(run); label = f"{os.path.basename(os.path.dirname(run))}/{mp}"
    f = mfeat(mp); T = profile_turns(run, f)
    pz = glob.glob(f"{run}/*-vs-*.repl26a"); qz = glob.glob(f"{run}/plain/*-vs-*.repl26a")
    if not (pz and qz) or fuel_turns(pz[0], "team-b")[1] != fuel_turns(qz[0], "team-b")[1]:
        summary(label + " (profile fuel, no plain game)", [(m, a) for _, m, _, _, a in T])
        continue
    real = fuel_turns(qz[0])[1]
    nd = 1
    while nd < len(T) and T[nd][0] == T[nd - 1][0] + 1: nd += 1
    champ = T[nd:]; C = sum(1 for t in champ if t[0] == champ[0][0])
    per = {}
    for tno, m, nb, na, _ in champ:
        x = per.setdefault(tno, [0, 0])
        x[0] += max(0, dist["scale"] * m + dist["per_block"] * nb + dist["per_api"] * na + dist["per_turn"]); x[1] += 1
    pairs = [(p, sum(real[nd + C * (t - 1):nd + C * t])) for t, (p, c) in sorted(per.items()) if c == C and nd + C * t <= len(real)]
    summary(label, pairs)
