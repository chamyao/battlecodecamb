"""Summarise a replay bundle's team-*.fuel file: per-turn fuel used by each bot instance.

Format (cambc 3.0.5): 13-byte header, then little-endian u64s: 8 budget values
(draft first/normal, champion first/normal, twice), then the fuel used by every turn in
order (draft turns first, then champion turns in play order).
Usage: python3 oracle/tools/fuel_file.py BUNDLE.repl26a [team-a|team-b] [--draft-turns N]
"""
import io, struct, sys, zipfile

def turns(path, team="team-a"):
    z = zipfile.ZipFile(path)
    d = z.read(f"{team}.fuel")
    n = (len(d) - 13) // 8
    v = struct.unpack_from(f"<{n}Q", d, 13)
    return v[:8], list(v[8:])

if __name__ == "__main__":
    path = sys.argv[1]
    team = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "team-a"
    nd = int(sys.argv[sys.argv.index("--draft-turns") + 1]) if "--draft-turns" in sys.argv else 5
    budgets, used = turns(path, team)
    play = used[nd:]
    if not play:
        sys.exit("no play turns")
    srt = sorted(play)
    print(f"{team}: budgets {budgets[:4]} draft {used[:nd]}")
    print(f"play turns {len(play)}: mean {sum(play)/len(play):.0f} median {srt[len(srt)//2]} p99 {srt[int(len(srt)*0.99)]} max {srt[-1]}"
          f"; turns >= 100k: {sum(x >= 100000 for x in play)}")
