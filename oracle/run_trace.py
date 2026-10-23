#!/usr/bin/env python3
"""Differential test: play the tracer bot in cambc and replay the trace in the simulator.

Usage: run_trace.py MAP SEED [SEED...] [--ws ~/ws] [--out /tmp/traces] [--rounds N]

For each seed: writes the tracer's config.h, runs `cambc run tracer tracer` with
statistics, converts the bundle into a replay script (oracle/tools/make_script.py)
and runs sim/build/replay on it. Prints one summary line per run.
"""
import argparse, glob, json, os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "oracle", "tools"))


def run(map_name, seed, ws, out, rounds, keep_going=False):
    cfg = os.path.join(REPO, "oracle", "bots", "tracer", "src", "config.h")
    with open(cfg, "w") as f:
        f.write(f"#pragma once\n#define TRACER_SEED {seed}ull\n#define TRACER_DRAFT_MEMORY 1\n")
    d = os.path.join(out, f"{map_name}-{seed}")
    os.makedirs(d, exist_ok=True)
    for old in glob.glob(os.path.join(d, "*.repl26a")):
        os.remove(old)
    stats = os.path.join(d, "stats.json")
    cmd = ["cambc", "run", "tracer", "tracer", "--release", "--map", map_name, "--fuel", "1000000000", "--log-limit", "2000000000",
           "-o", d, "--statistics", stats, "--json"]
    if rounds:
        cmd += ["--rounds", str(rounds)]
    env = dict(os.environ, SSL_CERT_FILE=os.environ.get("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt"))
    p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, env=env)
    bundle = glob.glob(os.path.join(d, "*.repl26a"))
    if not bundle:
        return f"{map_name} seed={seed}: cambc failed\n{p.stdout[-2000:]}{p.stderr[-2000:]}"
    script = os.path.join(d, "script.txt")
    with open(script, "w") as f:
        subprocess.run([sys.executable, os.path.join(REPO, "oracle", "tools", "make_script.py"), bundle[0], map_name], stdout=f, check=True)
    if os.path.exists(stats):
        st = json.load(open(stats))
        with open(script, "a") as f:
            gems = ",".join(t["submittedGems"] for t in st["teams"])
            f.write(f"\nRESULT {st['match']['outcome']} {st['match']['roundsCompleted']} {gems}\n")
    rp = subprocess.run([os.path.join(REPO, "sim", "build", "replay"), os.path.join(REPO, "maps", map_name + ".map26a"), script,
                         "--max-diffs", "8"], capture_output=True, text=True)
    lines = rp.stdout.strip().splitlines()
    summary = [l for l in lines if l.startswith("replayed") or l.startswith("sim result") or l.startswith("RESULT") or l.startswith("WARNING")]
    head = "" if rp.returncode == 0 and not keep_going else "\n".join(lines[:40])
    return f"{map_name} seed={seed}: " + " | ".join(summary) + ("\n" + head if head else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("seeds", nargs="+", type=int)
    ap.add_argument("--ws", default=os.path.expanduser("~/ws"))
    ap.add_argument("--out", default="/tmp/traces")
    ap.add_argument("--rounds", type=int, default=0)
    a = ap.parse_args()
    for s in a.seeds:
        print(run(a.map, s, a.ws, a.out, a.rounds), flush=True)
