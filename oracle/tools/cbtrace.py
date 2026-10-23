"""Parse tracer bundles into structured turns.

A turn is a dict: round, champ, team ('a'/'b'), slot (global timeline index),
obs = {'O': [...lines], 'P': [...lines]}, actions = [(call, args, results)].
"""
import re
import zipfile

def read_team(z, team):
    """Yield (slot, line) for every oracle line in a team's stdout.

    NUL bytes are timeline markers interleaved with output (possibly mid-line); the
    slot of a line is the number of markers seen before the line starts.
    """
    data = z.read(f"team-{team}.stdout")
    slot = 0
    for raw in data.split(b"\n"):
        start = slot
        i = raw.find(b"@@")
        lead = raw[:i] if i >= 0 else raw
        start = slot + lead.count(b"\x00")
        slot += raw.count(b"\x00")
        if i >= 0:
            yield start, raw[i + 2:].replace(b"\x00", b"").decode("latin-1")


def parse_action(line):
    # "A move 3 4 -> 0 1"
    body, _, res = line[2:].partition(" -> ")
    parts = body.split()
    return parts[0], [int(x) if re.fullmatch(r"-?\d+", x) else x for x in parts[1:]], [int(x) for x in res.split()]


def load(path):
    z = zipfile.ZipFile(path)
    turns, drafts = [], []
    for team in "ab":
        cur = None
        phase = None
        for slot, line in read_team(z, team):
            if line.startswith("draft "):
                drafts.append(dict(team=team, slot=slot, line=line, actions=[]))
                cur = None
                continue
            if line.startswith("T "):
                _, r, c = line.split()
                cur = dict(round=int(r), champ=int(c), team=team, slot=slot, obs={"O": [], "P": []}, actions=[])
                turns.append(cur)
                phase = None
                continue
            if line.startswith("A "):
                if cur is None:
                    drafts[-1]["actions"].append(parse_action(line))
                else:
                    cur["actions"].append(parse_action(line))
                continue
            if cur is None:
                continue
            if line[:2] in ("O ", "P "):
                phase = line[0]
            if phase:
                cur["obs"][phase].append(line)
    turns.sort(key=lambda t: (t["slot"], t["team"]))
    drafts.sort(key=lambda d: (d["slot"], d["team"]))
    return turns, drafts


def fields(line):
    """'self 0 alive=1 pos=3,4 ...' -> {'_': ['self','0'], 'alive': '1', 'pos': '3,4'}"""
    out = {"_": []}
    for tok in line.split():
        if "=" in tok:
            k, _, v = tok.partition("=")
            out[k] = v
        else:
            out["_"].append(tok)
    return out
