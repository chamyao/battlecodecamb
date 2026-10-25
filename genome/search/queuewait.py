"""Block until the arena's file queue (queuellm.py) has pending requests, then print them as JSON (the mutator agent's loop:
wait -> write DIR/rep-<seq>.txt for each -> wait).

    python3 -m genome.search.queuewait DIR [--max 8] [--timeout 600]

Pending = req-<seq>.json without rep-<seq>.txt, oldest first. Prints [] after --timeout seconds with none pending, or
{"done": true} once DIR/DONE exists (the arena has stopped).
"""
import argparse
import json
import time
from pathlib import Path


def pending(d):
    reqs = sorted(d.glob("req-*.json"), key=lambda p: int(p.stem.split("-")[1]))
    return [p for p in reqs if not (d / f"rep-{p.stem.split('-')[1]}.txt").exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=600)
    a = ap.parse_args()
    d = Path(a.dir)
    t0 = time.time()
    while True:
        p = pending(d) if d.exists() else []
        if p:
            time.sleep(1.0)  # requests come in bursts: give the rest of the burst a moment
            p = pending(d)
            print(json.dumps([json.loads(x.read_text()) for x in p[:a.max]], indent=1))
            return
        if (d / "DONE").exists():
            print(json.dumps({"done": True}))
            return
        if time.time() - t0 > a.timeout:
            print("[]")
            return
        time.sleep(1.0)


if __name__ == "__main__":
    main()
