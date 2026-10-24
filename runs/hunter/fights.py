# Per-fight signal (style line): A's-view engagement statistics from GAME_EVENTS (library: funsearch/fights.py).
# usage: fights.py A.policy B.policy [games] [seed] [--json]
import json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from policygen.compile import to_prefix  # noqa: E402
from policygen.text import parse  # noqa: E402
from funsearch import fights  # noqa: E402


def comp(p):
    if p.startswith("builtin:"):
        return p
    fd, out = tempfile.mkstemp(suffix=".pol")
    os.write(fd, to_prefix(parse(open(p).read())).encode())
    os.close(fd)
    return out


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    s = fights.play(comp(args[0]), comp(args[1]), int(args[2]) if len(args) > 2 else 80,
                    int(args[3]) if len(args) > 3 else 1)["summary"]
    s = {k: round(v, 3) if isinstance(v, float) else v for k, v in s.items()}
    print(json.dumps(s) if "--json" in sys.argv else f"{Path(args[0]).name} vs {Path(args[1]).name}: {s}")
