"""Summarise bot/tools/pool.sh output: per map result, crashes and team-a per-turn fuel.
The first play turn of each champion (2x budget) is reported separately from the rest."""
import glob, os, re, struct, sys, zipfile

out = sys.argv[1]
rows = []
for d in sorted(glob.glob(f"{out}/*/")):
    m = os.path.basename(d.rstrip("/"))
    log = open(f"{d}/log.txt", errors="replace").read()
    res = "?"
    mm = re.search(r"Team ([AB]) \((\S+)\) wins: (.*)", log)
    if mm: res = ("WIN " if mm.group(1) == "A" else "loss") + " " + mm.group(3)[:38]
    crash = re.search(r"^\s+A\s+\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)", log, re.M)
    bundles = glob.glob(f"{d}/*.repl26a")
    if not bundles:
        rows.append((m, res, None)); continue
    z = zipfile.ZipFile(bundles[0])
    data = z.read("team-a.fuel")
    n = (len(data) - 13) // 8
    v = struct.unpack_from(f"<{n}Q", data, 13)
    used = list(v[8:])
    nd = 5
    play = used[nd:]
    rounds = re.findall(r"round (\d+)", log)
    rounds = max(int(r) for r in rounds) if rounds else 2000
    k = max(1, min(8, round(len(play) / max(1, rounds))))  # champion instances
    first, rest = play[:k], play[k:]
    rest_s = sorted(rest) or [0]
    stdout = z.read("team-a.stdout").replace(b"\0", b"").decode(errors="replace")
    errs = stdout.count("bot error")
    rows.append((m, res, dict(n=len(rest), mean=sum(rest) / max(1, len(rest)), p99=rest_s[int(len(rest_s) * .99)], mx=rest_s[-1],
                               cap=sum(x >= 100000 for x in rest), first=max(first or [0]), crashes=int(crash.group(1)) if crash else -1, errs=errs)))
print(f"{'map':24s} {'result':46s} {'turns':>6s} {'mean':>6s} {'p99':>6s} {'max':>7s} {'>=100k':>6s} {'first':>7s} crash err")
wins = 0
for m, res, s in rows:
    wins += res.startswith("WIN")
    if s is None:
        print(f"{m:24s} {res:46s} (no replay)"); continue
    print(f"{m:24s} {res:46s} {s['n']:6d} {s['mean']:6.0f} {s['p99']:6d} {s['mx']:7d} {s['cap']:6d} {s['first']:7d} {s['crashes']:5d} {s['errs']:3d}")
print(f"wins {wins}/{len(rows)}")
