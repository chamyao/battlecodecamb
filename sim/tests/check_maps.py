"""Compare the C++ map decoder (maptest) with engine dumps for every pool map."""
import glob, json, os, subprocess, sys
CAMPS = ["wolf", "elk", "gem_cluster", "gold_cluster", "monolith", "golem"]
exe, repo = sys.argv[1], sys.argv[2]
bad = 0
for path in sorted(glob.glob(os.path.join(repo, "maps", "*.map26a"))):
    name = os.path.basename(path)[:-7]
    f = json.load(open(os.path.join(repo, "oracle", "fixtures", "maps", name + ".json")))
    out = subprocess.run([exe, path], capture_output=True, text=True, check=True).stdout.splitlines()
    got = {"masks": {}, "spawn": {}, "groups": []}
    for line in out:
        p = line.split()
        if p[0] == "dims": got["dims"] = [int(p[1]), int(p[2])]
        elif p[0] == "symmetry": got["symmetry"] = int(p[1])
        elif p[0] == "mask": got["masks"][p[1]] = p[2]
        elif p[0] == "spawn": got["spawn"][p[1]] = [int(x) for x in p[2:]]
        elif p[0] == "group":
            camps = [dict(zip(["handle", "type", "x", "y"], map(int, c.split(":")))) for c in p[5:]]
            for c in camps: c["type"] = CAMPS[c["type"]]
            got["groups"].append(dict(group=int(p[1]), gold=int(p[2]), gems=int(p[3]), respawn=int(p[4]), camps=camps))
    errs = []
    if got["dims"] != [f["metadata"]["width"], f["metadata"]["height"]]: errs.append("dims")
    if got["symmetry"] != f["symmetry"]: errs.append("symmetry")
    if got["masks"] != f["masks"]: errs.append("masks")
    if got["spawn"] != f["spawn"]: errs.append("spawn")
    if got["groups"] != f["camp_layout"]: errs.append("groups")
    if errs:
        bad += 1
        print(name, errs)
print(f"{bad} map(s) differ")
sys.exit(1 if bad else 0)
