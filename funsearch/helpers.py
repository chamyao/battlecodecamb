"""Shared helper library: `def` helpers harvested from FunSearch children that scored at least their best parent.

    python3 -m funsearch.helpers --runs RUN_DIR_OR_JSONL [...] --out funsearch/helpers.json [--md HELPERS.md]

For every valid child that scored >= its best parent, each top-level `def` is extracted, normalised (comments and
blank lines stripped, the name, parameters and local `let` names canonicalised) and deduplicated by body. Per
helper: uses (programs containing it), lines and runs it appears in, the mean score delta vs the best parent over
the children that introduced or changed it, whether its blocks executed (exec_blocks, when logged), and its
dependencies (other defs it calls, keep variables and NAME constants it reads). Ranked by mean delta x log(1 + uses);
helpers with dependencies on other defs are bundled with them. Runs whose directory name contains "oldbuild" are
skipped (scored on a stale simulator build).
"""
import argparse
import glob
import json
import math
import re
from pathlib import Path

from policygen.blocks import REGISTRY

BLOCKS = {b.name for b in REGISTRY}
KEYWORDS = {"if", "elif", "else", "and", "or", "not", "let", "keep", "def", "return", "True", "False", "end_turn"}
_IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def _code(line):
    i = line.find("#")
    return (line if i < 0 else line[:i]).rstrip()


def extract_defs(text):
    """Top-level defs as {name: (params, source lines incl. comments)}."""
    lines, out, i = text.split("\n"), {}, 0
    while i < len(lines):
        m = re.match(r"def\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*:", lines[i])
        if not m:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j].startswith((" ", "\t")) or
                                  (lines[j].lstrip().startswith("#") and j + 1 < len(lines)
                                   and lines[j + 1].startswith((" ", "\t")))):
            j += 1
        while j > i + 1 and not lines[j - 1].strip():
            j -= 1
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        out[m.group(1)] = (params, lines[i:j])
        i = j
    return out


def normalise(name, params, src):
    """Canonical body: comments and blanks dropped, def name -> F, params -> P0.., let names -> L0.."""
    code = [_code(l) for l in src]
    code = [c for c in code if c.strip()]
    ren = {name: "F", **{p: f"P{k}" for k, p in enumerate(params)}}
    lets = [m.group(1) for c in code for m in [re.match(r"\s*let\s+([A-Za-z_]\w*)\s*=", c)] if m]
    for k, v in enumerate(dict.fromkeys(lets)):
        ren.setdefault(v, f"L{k}")
    return "\n".join(_IDENT.sub(lambda m: ren.get(m.group(0), m.group(0)), c) for c in code)


def dependencies(name, params, src, text, defs):
    """Other defs called, keep variables and NAME constants referenced by the helper."""
    body = " ".join(_code(l) for l in src[1:])
    idents = set(_IDENT.findall(body)) - set(params) - BLOCKS - KEYWORDS
    keeps = set(re.findall(r"^keep\s+([A-Za-z_]\w*)\s*=", text, re.M))
    consts = set(re.findall(r"^([A-Z][A-Z0-9_]*)\s*=", text, re.M))
    lets = set(re.findall(r"\blet\s+([A-Za-z_]\w*)\s*=", body))
    used_consts = sorted(idents & consts)
    const_lines = [l for l in text.split("\n") for c in used_consts if re.match(rf"^{c}\s*=", l)]
    return dict(defs=sorted(idents & (set(defs) - {name})), keeps=sorted(idents & keeps),
                consts=used_consts, unknown=sorted(idents - set(defs) - keeps - consts - lets), const_lines=const_lines)


def load_runs(paths):
    """Yield (line, run, rows) for every programs.jsonl under the given paths."""
    files = []
    for p in map(Path, paths):
        files += [p] if p.is_file() else sorted(p.rglob("programs.jsonl"))
    for f in files:
        run = f.parent.name
        if "oldbuild" in run:
            continue
        line = next((x for x in ("hybrid", "pure", "style", "tune") if x in str(f)), "?")
        rows = [json.loads(l) for l in open(f) if l.strip()]
        yield line, run, rows


def valid(r):
    return r.get("error") is None and r.get("score") is not None and r["score"] > float("-inf")


def harvest(paths, min_introductions=2, min_delta=0.05):
    lib = {}
    for line, run, rows in load_runs(paths):
        by_id = {r["id"]: r for r in rows}
        for r in rows:
            if not valid(r):
                continue
            defs = extract_defs(r["text"])
            for name, (params, src) in defs.items():
                key = normalise(name, params, src)
                h = lib.setdefault(key, dict(name=name, params=params, source="\n".join(src), uses=0, lines=set(),
                                             runs=set(), deltas=[], executed=None, deps=None, best_score=-1e9))
                h["uses"] += 1
                h["lines"].add(line)
                h["runs"].add(f"{line}:{run}")
                if h["deps"] is None:
                    h["deps"] = dependencies(name, params, src, r["text"], defs)
                if r["score"] > h["best_score"]:
                    h.update(name=name, params=params, source="\n".join(src), best_score=r["score"])
                if r.get("model") in ("seed", "reset") or not r.get("parents"):
                    continue
                parents = [by_id[p] for p in r["parents"] if p in by_id and valid(by_id[p])]
                if not parents:
                    continue
                best_parent = max(parents, key=lambda p: p["score"])
                parent_keys = {normalise(n, pp, s) for n, (pp, s) in extract_defs(best_parent["text"]).items()}
                if key in parent_keys:
                    continue  # inherited, not introduced or changed here
                delta = r["score"] - best_parent["score"]
                if r["score"] >= best_parent["score"]:
                    h["deltas"].append(delta)
                    blocks = r.get("metrics", {}).get("exec_blocks")
                    if blocks is not None:
                        used = set(_IDENT.findall(" ".join(_code(l) for l in src))) & BLOCKS
                        h["executed"] = bool(used) and used <= set(blocks)
    out = []
    for key, h in lib.items():
        if not h["deltas"]:
            continue
        mean = sum(h["deltas"]) / len(h["deltas"])
        # inherited copies are not evidence: rank on introductions only, and require 2 of them or a clear delta
        if len(h["deltas"]) < min_introductions and mean < min_delta:
            continue
        out.append(dict(name=h["name"], params=h["params"], source=h["source"], normalised=key, uses=h["uses"],
                        introduced=len(h["deltas"]), mean_delta=round(mean, 4),
                        rank=round(mean * math.log(1 + len(h["deltas"])), 4), lines=sorted(h["lines"]),
                        runs=sorted(h["runs"]), executed=h["executed"], deps=h["deps"],
                        self_contained=not (h["deps"]["defs"] or h["deps"]["keeps"] or h["deps"]["unknown"])))
    out.sort(key=lambda h: -h["rank"])
    by_name = {h["name"]: h for h in out}
    for h in out:  # bundle def dependencies when they are in the library too
        h["bundle"] = [by_name[d]["source"] for d in h["deps"]["defs"] if d in by_name]
    return out


def markdown(lib, top=20):
    lines = ["# Shared helper library", "",
             "Harvested by `python3 -m funsearch.helpers` from children that scored >= their best parent. Ranked by",
             "mean score delta (child vs best parent, over the children that introduced or changed the helper) x",
             "log(1 + introductions); kept with >= 2 introductions or a mean delta >= 0.05. Library code: paste and call;",
             "mind fuel.", ""]
    for k, h in enumerate(lib[:top], 1):
        deps = ", ".join(f"{t}: {', '.join(v)}" for t, v in h["deps"].items() if v and t != "const_lines") or "none"
        lines += [f"## {k}. `{h['name']}({', '.join(h['params'])})`: rank {h['rank']}",
                  f"mean delta {h['mean_delta']:+.4f} over {h['introduced']} introductions; used in {h['uses']} "
                  f"programs; lines {', '.join(h['lines'])}; executed {h['executed']}; deps {deps}", "",
                  "```policy", *h["deps"].get("const_lines", []), h["source"], "```", ""]
    return "\n".join(lines)


def prompt_section(lib, budget=2500):
    """The prompt's "shared helpers" section: top self-contained helpers until the character budget is spent."""
    from policygen.text import parse
    parts, used, names = [], 0, set()
    for h in lib:
        if not h["self_contained"] or h["mean_delta"] <= 0 or h["name"] in names:
            continue  # one def per name, so pasted helpers never clash
        src = "\n".join(h["deps"].get("const_lines", []) + [h["source"]])
        if used + len(src) > budget:
            continue
        try:
            parse(src + "\nend_turn()\n")
        except Exception:
            continue
        parts.append(src)
        names.add(h["name"])
        used += len(src)
    if not parts:
        return ""
    return ("# Shared helpers (library code from earlier winning children; paste a def at top level and call it "
            "where useful; each call costs fuel like its blocks)\n" + "\n\n".join(parts) + "\n")


def lib_keys(lib):
    return {h["normalised"]: h["name"] for h in lib}


def tag(text, keys):
    """Names of library helpers present in a policy (normalised match)."""
    return sorted({keys[k] for n, (p, s) in extract_defs(text).items() for k in [normalise(n, p, s)] if k in keys})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True, help="run directories or programs.jsonl files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", default="")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-introductions", type=int, default=2)
    ap.add_argument("--min-delta", type=float, default=0.05)
    args = ap.parse_args()
    runs = [x for r in args.runs for x in (sorted(glob.glob(r)) or [r])]
    lib = harvest(runs, args.min_introductions, args.min_delta)
    Path(args.out).write_text(json.dumps(lib, indent=1))
    if args.md:
        Path(args.md).write_text(markdown(lib, args.top))
    print(f"{len(lib)} helpers kept; top {min(args.top, len(lib))}:")
    for h in lib[: args.top]:
        print(f"  {h['rank']:+.4f}  {h['name']}  delta {h['mean_delta']:+.4f} x{h['introduced']}  uses {h['uses']}  "
              f"{','.join(h['lines'])}  self-contained {h['self_contained']}")


if __name__ == "__main__":
    main()
