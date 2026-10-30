"""Mirror an arena-service run's output into remote/genome (the record of every genome-line run).

    python3 -m genome.search.mirror --run 13 --path runs/arenaB --dest arena-arenaB-7 --worktree <remote/genome clone>

Every --every seconds: copy <path> of run <run> through the files API (genomes/ files once each, the rest each
time), commit under <dest>/ in the worktree, fetch and rebase onto origin/remote/genome, push (never forced).
Stops --after seconds after the run has ended (one last copy).
"""
import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

from .gate import ARENA_URL, _http


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"X-Arena-Client": "genome-search"}),
                                timeout=120) as r:
        return r.read()


def copy(base, path, dest):
    listing = json.loads(_http(f"{base}/files/{path}/"))["dir"]
    for name in listing:
        if name.endswith("/"):
            copy(base, f"{path}/{name[:-1]}", dest / name[:-1])
            continue
        out = dest / name
        if out.exists() and "/genomes" in f"/{path}":
            continue  # genome files never change
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(get(f"{base}/files/{path}/{name}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--every", type=float, default=900)
    ap.add_argument("--after", type=float, default=60)
    a = ap.parse_args()
    base = f"{ARENA_URL}/runs/{a.run}"
    wt = Path(a.worktree)

    def git(*args):
        return subprocess.run(["git", "-C", str(wt), *args], capture_output=True, text=True)

    while True:
        status = "unknown"
        try:  # a service blip (HTTP error on the status read too) must not end the mirror
            status = json.loads(_http(base))["status"]
            copy(base, a.path, wt / a.dest)
            (wt / a.dest / "RUN.json").write_text(json.dumps({k: v for k, v in json.loads(_http(base)).items()
                                                              if k != "log_tail"}, indent=1))
            git("add", a.dest)
            if git("diff", "--cached", "--quiet").returncode != 0:
                git("commit", "-qm", f"{a.dest}: mirror of arena run {a.run} ({status}) {time.strftime('%H:%M')} UTC")
            for _ in range(4):
                git("fetch", "-q", "origin", "remote/genome")
                if git("rebase", "-q", "origin/remote/genome").returncode != 0:
                    git("rebase", "--abort")
                    break
                if git("push", "-q", "origin", "HEAD:remote/genome").returncode == 0:
                    break
                time.sleep(10)
            print(f"[{time.strftime('%H:%M:%S')}] mirrored run {a.run} ({status})", flush=True)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] mirror failed: {type(e).__name__}: {e}", flush=True)
        if status in ("exited", "failed", "stopped", "cancelled"):
            break
        time.sleep(a.every)


if __name__ == "__main__":
    main()
