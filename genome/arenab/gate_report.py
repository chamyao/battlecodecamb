"""gate_report.py OUT CAND REF: summarise a real_gate.sh run (gate parts b and c).

Wins come from run-batch's result lines; fuel from each bundle's team-*.fuel
(oracle/tools/fuel_file.py). Crashes: failed matches or non-empty stderr-like
debug output mentioning a trap/panic.
"""
import re, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "oracle" / "tools"))
from fuel_file import turns

out, cand, ref = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
log = (out / "batch.log").read_text(errors="replace")
res = {}  # replay name -> winner label
for m in re.finditer(r"\[\+\] (TEAM A WIN|TEAM B WIN|DRAW)[^\n]*\n\s*Replay: (\S+)", log):
    res[Path(m.group(2)).name] = m.group(1)
wins = draws = 0
stats = {cand: {"first": 0, "first200": 0, "cap": 0, "crash": 0}, ref: {"first": 0, "first200": 0, "cap": 0, "crash": 0}}
missing = []
for side in "AB":
    for rp in sorted(out.glob(f"{side}-*.repl26a")):
        r = res.get(rp.name)
        if r is None:
            missing.append(rp.name)
        cteam, rteam = ("team-a", "team-b") if side == "A" else ("team-b", "team-a")
        if r == f"TEAM {'A' if side == 'A' else 'B'} WIN":
            wins += 1
        elif r == "DRAW":
            draws += 1
        z = zipfile.ZipFile(rp)
        for bot, team in ((cand, cteam), (ref, rteam)):
            _, used = turns(rp, team)
            play = used[5:]
            # the first 5 play turns are the champions' first turns (200k budget); the rest have 100k
            if play:
                stats[bot]["first"] = max(stats[bot]["first"], max(play[:5]))
                stats[bot]["first200"] += sum(x >= 200000 for x in play[:5])
            stats[bot]["cap"] += sum(x >= 100000 for x in play[5:])
            dbg = z.read(f"{team}.debug").decode(errors="replace") + z.read(f"{team}.stdout").decode(errors="replace")
            if re.search(r"trap|panic|abort|unreachable|crash", dbg, re.I):
                stats[bot]["crash"] += 1
failed = re.findall(r"(\d+) failed", log)
n = len(list(out.glob("*.repl26a")))
print(f"{cand} vs {ref}: {wins}/{n} wins ({draws} draws); bar >= 42/80 -> {'PASS' if wins >= 42 and n == 80 else 'FAIL'}")
for bot, s in stats.items():
    print(f"  {bot}: crashes {s['crash']}, first turns max {s['first']} (at the 200k cap: {s['first200']}), normal turns >= 100k {s['cap']}")
ok = n == 80 and stats[cand]["crash"] == 0 and stats[cand]["first"] < 200000 and stats[cand]["cap"] <= stats[ref]["cap"]
print(f"  safety -> {'PASS' if ok else 'FAIL'}; batch failed: {failed[-1] if failed else '?'}; unparsed results: {len(missing)}")
