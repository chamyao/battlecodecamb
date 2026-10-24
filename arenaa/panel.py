"""Play genomes vs outside opponents on the arena service (simulator, genome_eval).

    python3 arenaa/panel.py --engine db3f945 --games 400 --seed 31337 --out panel.jsonl g1.genome g2.genome ...
"""
import argparse
import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = os.environ.get("ARENA_URL", "https://138-201-121-171.sslip.io/arena")
PANEL = ["repo:policies/candidates/style-gconv1.policy", "repo:policies/candidates/tune-v20-L1.policy",
         "repo:policies/candidates/rall2-ca4-lean-g.policy", "repo:policies/v7.policy",
         "repo:policies/opp-tune5-metadraft.policy", "repo:policies/candidates/tune-v20-L1c.policy"]


def call(method, path, body=None):
    req = urllib.request.Request(URL + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "X-Arena-Client": "arenaA-lead"})
    with urllib.request.urlopen(req, timeout=150) as r:
        return json.loads(r.read())


def match(job, args):
    text, name, opp = job
    m = call("POST", "/matches?wait=110", {"a": {"text": text, "kind": "genome"}, "b": opp, "games": args.games,
                                           "seed": args.seed, "engine": args.engine})
    while m.get("status") not in ("done", "failed", "cancelled"):
        m = call("GET", f"/matches/{m['id']}?wait=110")
    return name, opp, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("genomes", nargs="+")
    ap.add_argument("--engine", default="genome/v0")
    ap.add_argument("--games", type=int, default=400)
    ap.add_argument("--seed", type=int, default=31337)
    ap.add_argument("--out")
    args = ap.parse_args()
    jobs = [(open(p).read(), os.path.basename(p).rsplit(".", 1)[0], b) for p in args.genomes for b in PANEL]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda j: match(j, args), jobs))
    out = open(args.out, "a") if args.out else None
    for name, opp, m in res:
        rec = {"genome": name, "opponent": opp.split("/")[-1].replace(".policy", ""), "engine": args.engine,
               "seed": args.seed, "games": args.games, "status": m.get("status"), "result": m.get("result"),
               "error": m.get("error")}
        print(json.dumps(rec)[:300])
        if out:
            out.write(json.dumps(rec) + "\n")


if __name__ == "__main__":
    main()
