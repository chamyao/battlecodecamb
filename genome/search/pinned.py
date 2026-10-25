"""Run a module from a pinned, patched checkout (for arena-service runs, whose ref is a single commit): builds
<base> + patches + copied genome/search files + <runtime>'s runtime files in a git worktree, then runs the module there.

    python3 -m genome.search.pinned --base 7e40b6f --runtime 648bafd --patch rng-salt.patch \
        [--copy a1op.py ...] [--dry] -- genome.search.arena --out runs/arenaZ-7/arena ... --rng-salt 2

Patches and copied files come from this checkout's genome/search (patches/ and the module files). --out and other
relative paths after "--" stay relative to the directory this was started in (the run's workdir), so the service
collects the outputs as usual.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

from funsearch.evaluate import ROOT

RUNTIME = ["sim", "interp", "policygen", "genome/runtime", "genome/lang.py", "genome/build.py", "genome/tools",
           "genome/CMakeLists.txt"]
HERE = Path(__file__).resolve().parent


def sh(*cmd, cwd=None, log=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if log:
        log.write(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
        log.flush()
    if r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)} failed: {r.stderr[-800:]}")
    return r.stdout


def main():
    argv = sys.argv[1:]
    if "--" not in argv:
        raise SystemExit("usage: pinned.py [options] -- module args...")
    i = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--patch", action="append", default=[], help="file in genome/search/patches/")
    ap.add_argument("--copy", action="append", default=[], help="genome/search module file to copy in")
    ap.add_argument("--dir", default="", help="checkout directory (default: pinned-<base>-<runtime> under the cwd)")
    ap.add_argument("--dry", action="store_true", help="build the checkout and stop")
    a = ap.parse_args(argv[:i])
    module, margs = argv[i + 1], argv[i + 2:]
    start = Path.cwd()
    d = Path(a.dir or start / f"pinned-{a.base[:8]}-{a.runtime[:8]}").resolve()
    log = open(start / "pinned-setup.log", "a")
    if not (d / ".pinned-ok").exists():
        for ref in (a.base, a.runtime):
            if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{ref}^{{commit}}"]).returncode != 0:
                sh("git", "-C", str(ROOT), "fetch", "-q", "origin", ref, log=log)
        if d.exists():
            sh("git", "-C", str(ROOT), "worktree", "remove", "--force", str(d), log=log)
        sh("git", "-C", str(ROOT), "worktree", "add", "-q", "--detach", str(d), a.base, log=log)
        for p in a.patch:
            sh("git", "apply", str(HERE / "patches" / p), cwd=d, log=log)
        for f in a.copy:
            (d / "genome" / "search" / f).write_text((HERE / f).read_text())
        sh("git", "checkout", "-q", a.runtime, "--", *RUNTIME, cwd=d, log=log)
        sh("cmake", "-S", "genome", "-B", "genome/build", "-DCMAKE_BUILD_TYPE=Release", cwd=d, log=log)
        sh("cmake", "--build", "genome/build", f"-j{os.cpu_count() or 4}", "--target", "genome_eval", cwd=d, log=log)
        (d / ".pinned-ok").write_text(f"{a.base} {a.runtime} {a.patch} {a.copy}\n")
    log.write(sh("git", "diff", "--stat", cwd=d))
    log.close()
    if a.dry:
        print(f"pinned checkout ready: {d}")
        return
    # relative paths in the module's args stay relative to the start directory
    fixed = []
    for x in margs:
        p = start / x
        fixed.append(str(p) if (not x.startswith("-") and ("/" in x) and not Path(x).is_absolute()
                                and (p.exists() or p.parent.exists() or x.startswith("runs/"))) else x)
    for k, x in enumerate(fixed):  # output dirs that do not exist yet
        if k and fixed[k - 1] in ("--out", "--llm-queue") and not Path(x).is_absolute():
            fixed[k] = str(start / x)
    os.chdir(d)
    os.execvp(sys.executable, [sys.executable, "-m", module, *fixed])


if __name__ == "__main__":
    main()
