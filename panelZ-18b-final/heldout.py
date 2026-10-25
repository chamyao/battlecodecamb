# Over-fitting check for Z-18b's screened genomes vs references, engine 648bafd:
#  (a) the 11 panel opponents with bot seeds OFF (random policy seeds 11 and 12): same maps, different game instances
#  (b) 6 held-out opponents (A-panel policies) with bot seeds (fixed games, as the panel)
import json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, "/home/user/battlecodecamb")
from genome.search.panelwatch import arena_side
U = "https://138-201-121-171.sslip.io/arena"; E = "648bafd22eb4ed36c493b95e837770b916197919"
H = {"X-Arena-Client": "genome-search", "Content-Type": "application/json"}
R = "/home/user/battlecodecamb/runs/"; Zp = R + "zpanels"; C, P = "policies/candidates", "policies"
G = {"Z462 (18b)": R + "panelZ-18b-final/panel-genomes/m1-Z462.genome", "Z400 (18b)": R + "panelZ-18b-final/panel-genomes/m1-Z400.genome",
     "Z477 (Z-5)": R + "z5-final/genomes/Z477.genome", "Z392 (Z-5)": R + "z5-final/genomes/Z392.genome",
     "Z446 (18d)": R + "panelZ-18d-final/panel-genomes/m1-Z446.genome", "Z403 (Z-15)": R + "panelZ-15/panel-genomes/m4-Z403.genome"}
PANEL = [f"{P}/fs-1.policy", f"{Zp}/fs-p2.policy", f"{P}/v4.policy", f"{P}/v7-zerogem.policy", f"{C}/hyb-t5m.policy", f"{C}/tune-v20-L1c.policy",
         f"{P}/v5.policy", f"{P}/v6.policy", f"{P}/v7.policy", f"{Zp}/fs-p1.policy", f"{Zp}/fs-p3.policy"]
HELD = [f"{C}/style-gconv1.policy", f"{C}/tune-v20-L1.policy", f"{C}/rall2-ca4-lean-g.policy", f"{P}/opp-tune5-metadraft.policy",
        f"{C}/tune-v19-L1c.policy", f"{C}/tune-r-all-v2.policy"]
def http(url, body=None):
    req = urllib.request.Request(url, data=body, headers=H, method="POST" if body else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=130).read())
def rate(a, b, bot_seeds, seed):
    for k in range(5):
        try:
            m = http(f"{U}/matches?wait=110", json.dumps({"a": a, "b": b, "engine": E, "bot_seeds": bot_seeds, "seed": seed, "priority": 0}).encode())["match"]
            while m["status"] not in ("done", "failed", "cancelled"):
                m = http(f"{U}/matches/{m['id']}?wait=110"); m = m.get("match", m)
            return m["result"]["a_wins"]
        except Exception as e:
            time.sleep(10)
    return None
jobs = []
for g, f in G.items():
    side = {"text": Path(f).read_text(), "kind": "genome"}
    for o in PANEL:
        for seed in (11, 12):
            jobs.append((g, "panel-rand", o, side, arena_side(o), False, seed))
    for o in HELD:
        jobs.append((g, "heldout", o, side, arena_side(o), True, 1))
out = open("/tmp/claude-0/-home-user-battlecodecamb/3aaf982f-351b-5fe0-9804-bf18bdd789fd/scratchpad/heldout.jsonl", "a")
def go(j):
    g, kind, o, a, b, bs, seed = j
    w = rate(a, b, bs, seed)
    out.write(json.dumps({"genome": g, "kind": kind, "opp": Path(o).stem, "seed": seed, "wins": w}) + "\n"); out.flush()
with ThreadPoolExecutor(4) as ex:
    list(ex.map(go, jobs))
print("done", len(jobs))
