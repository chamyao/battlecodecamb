"""Racing evaluation for the tuning/draft line (no LLM calls).

Candidates are played head to head against a base policy on the full map list
(every map, both sides, per-game seeds). Screen all candidates on a shared seed,
keep the top few, then confirm the survivors on fresh seeds, so the screening
noise that picked them (winner's curse) does not count toward promotion.
"""
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from policygen.compile import to_prefix
from policygen.text import parse

ROOT = Path(__file__).resolve().parent.parent
EVAL_BIN = ROOT / "interp" / "build" / "interp_eval"
MAPS = sorted(str(p) for p in (ROOT / "maps").glob("*.map26a"))
GAUNTLET = ("v4", "locker", "fs-2", "starter")


def compile_text(text):
    """Compile policy text to a temp .pol file; returns its path."""
    fd, out = tempfile.mkstemp(suffix=".pol", prefix="race-")
    with open(fd, "w") as f:
        f.write(to_prefix(parse(text)))
    return out


def compile_file(path):
    return compile_text(Path(path).read_text())


def h2h(a_pol, b_pol, games, seed, threads=4):
    """Win rate of A vs B over `games` games cycling the map list (pairs swap sides)."""
    out = subprocess.run([str(EVAL_BIN), "--a", a_pol, "--b", b_pol, "--games", str(games),
                          "--threads", str(threads), "--seed", str(seed), *MAPS],
                         capture_output=True, text=True, timeout=3600)
    stats = json.loads(out.stdout.strip().splitlines()[-1])
    if "error" in stats:
        raise RuntimeError(stats["error"])
    return stats


def screen(cands, base_pol, games=200, seed=11, workers=1, threads=4, log=print):
    """cands: {name: text}. Returns [(win_rate, name)] best first."""
    def one(item):
        name, text = item
        pol = compile_text(text)
        try:
            return h2h(pol, base_pol, games, seed, threads)["win_rate"], name
        finally:
            Path(pol).unlink(missing_ok=True)

    res = []
    with ThreadPoolExecutor(workers) as ex:
        for wr, name in ex.map(one, cands.items()):
            log(f"screen {name}: {wr:.3f}")
            res.append((wr, name))
    return sorted(res, reverse=True)


def confirm(text, base_pol, seeds=(9001, 9002), games=400, gauntlet=GAUNTLET, base_text=None, log=print):
    """Head to head vs base on fresh seeds, plus the gauntlet delta against the base's own scores."""
    pol = compile_text(text)
    try:
        hh = [h2h(pol, base_pol, games, s)["win_rate"] for s in seeds]
        out = {"h2h": hh, "h2h_mean": sum(hh) / len(hh), "gauntlet": {}}
        bpol = compile_text(base_text) if base_text else None
        for g in gauntlet:
            gp = compile_file(ROOT / "policies" / f"{g}.policy")
            mine = sum(h2h(pol, gp, games, s)["win_rate"] for s in seeds) / len(seeds)
            theirs = sum(h2h(bpol, gp, games, s)["win_rate"] for s in seeds) / len(seeds) if bpol else None
            out["gauntlet"][g] = (mine, theirs)
            Path(gp).unlink(missing_ok=True)
        if bpol:
            Path(bpol).unlink(missing_ok=True)
        log(json.dumps(out))
        return out
    finally:
        Path(pol).unlink(missing_ok=True)


def set_draft(text, body):
    """Replace the policy's draft section (between the draft and every-turn markers)."""
    start = text.index("# ---- draft ----")
    end = text.index("# ---- every turn ----")
    return text[:start] + "# ---- draft ----\n" + body.rstrip() + "\n\n" + text[end:]


def chain_draft(order, fallback="pick( random_champion(pool) )"):
    """Draft body for a fixed preference order of champion names."""
    lines = ["if is_draft():", "    let pool = unpicked_champions()"]
    for i, c in enumerate(order):
        kw = "if" if i == 0 else "elif"
        lines += [f"    {kw} available(pool, champ_{c}()):", f"        pick(champ_{c}())"]
    lines += ["    else:", f"        {fallback}", "    end_turn()"]
    return "\n".join(lines)
