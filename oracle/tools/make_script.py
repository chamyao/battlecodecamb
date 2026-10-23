"""Convert a tracer bundle into an ordered replay script for sim/tools/replay.

Usage: make_script.py BUNDLE.repl26a MAPNAME > script.txt
"""
import sys
import cbtrace as trace

path, mapname = sys.argv[1], sys.argv[2]
turns, drafts = trace.load(path)
out = [f"MAP {mapname}"]
for d in drafts:
    out.append(f"DRAFT {0 if d['team'] == 'a' else 1}")
    out.append("L " + d["line"])
    for name, args, res in d["actions"]:
        out.append("A " + " ".join([name] + [str(a) for a in args] + ["->"] + [str(r) for r in res]))
    out.append("END")
for t in turns:
    out.append(f"TURN {0 if t['team'] == 'a' else 1} {t['round']} {t['champ']}")
    for line in t["obs"]["O"]:
        out.append("O " + line)
    for name, args, res in t["actions"]:
        out.append("A " + " ".join([name] + [str(a) for a in args] + ["->"] + [str(r) for r in res]))
    for line in t["obs"]["P"]:
        out.append("P " + line)
    out.append("END")
print("\n".join(out))
