# Z best vs the A line: 80 distinct games (bot seeds) per pair, Z genome as side A, on engines ca5180b (e3ac822a) and 648bafd.
import json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
D = Path("/tmp/claude-0/-home-user-battlecodecamb/3aaf982f-351b-5fe0-9804-bf18bdd789fd/scratchpad/zvA")
U = "https://138-201-121-171.sslip.io/arena"; H = {"X-Arena-Client": "genome-search", "Content-Type": "application/json"}
E = {"ca5180b": "e3ac822acf88eda913c0fc28876bae10b7e9f5f3", "648bafd": "648bafd22eb4ed36c493b95e837770b916197919"}
Z = ["Z462", "Z400", "Z407"]; OPP = ["starter", "v23", "A61188", "A81582", "A93208", "v33"]
g = lambda n: {"text": (D / f"{n}.genome").read_text(), "kind": "genome"}
def http(url, body=None):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, data=body, headers=H, method="POST" if body else "GET"), timeout=130).read())
def rate(job):
    z, o, en = job
    for k in range(5):
        try:
            m = http(f"{U}/matches?wait=110", json.dumps({"a": g(z), "b": g(o), "engine": E[en], "bot_seeds": True, "priority": 1}).encode())["match"]
            while m["status"] not in ("done", "failed", "cancelled"):
                m = http(f"{U}/matches/{m['id']}?wait=110"); m = m.get("match", m)
            r = m.get("result") or {}
            return {"z": z, "opp": o, "engine": en, "status": m["status"], "wins": r.get("a_wins"), "games": r.get("games"),
                    "a_gems": r.get("a_gems"), "b_gems": r.get("b_gems"), "error": m.get("error")}
        except Exception as e:
            time.sleep(10)
    return {"z": z, "opp": o, "engine": en, "status": "error"}
jobs = [(z, o, en) for en in E for z in Z for o in OPP]
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(rate, jobs))
json.dump(res, open(D / "results.json", "w"), indent=1)
print("done", len(res))
