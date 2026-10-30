"""Ladder gate for arena genomes, and a gatekeeper that applies it to running arenas from their pushed state.

Every game is fixed by its map and side: genome-vs-genome games do not depend on the seed, and policies are
seeded as deployed (--bot-seeds). So a pair has exactly 80 distinct games (40 maps x 2 sides), and the gate
plays each once (SE ~5.6 points at 50%); repeating them adds no evidence. Variety comes from maps and opponents.

Gate (outside selection), for one genome:
1. head to head vs the live bot (--ref): the 80 games; passes at >= --min-wins (default 43/80 = 53.75%);
2. every fixed anchor: its 80 games; no drop > --regress vs the live bot's own rate there;
3. fuel x10 re-play of the head to head (behavioural vs fuel-only strength), logged.

Gatekeeper (works on arenas that are already running, without restarting them):

    python3 -m genome.search.gate --out $OUT --arena arenaA-1/arena --arena arenaB-1/arena --every 600

Every --every seconds it fetches origin/remote/genome, and for each arena takes the top --top live genomes by
rating with >= --min-games games that have not been screened yet, and gates them. Results: <out>/gates.jsonl,
passing genomes in <out>/candidates/. Stops when every arena's job has an rc file, or after --max-hours.
"""
import argparse
import json
import math
import re
import os
import urllib.request
import subprocess
import time
from pathlib import Path

from funsearch.evaluate import MAPS, ROOT

NG = 2 * len(MAPS)  # distinct games per pair: every map once from each side (80 on engine 1.0.3, 140 on 2.0.0)


GENE_HEAD = re.compile(r"""^@gene\(\s*['"]([^'"]+)['"]""")


def gene_blocks(text):
    """{gene id: (start, end)} line spans: the @gene line, its def line and the indented body (trailing blanks excluded)."""
    lines, spans, i = text.split("\n"), {}, 0
    while i < len(lines):
        m = GENE_HEAD.match(lines[i])
        if not m:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and (lines[j].startswith("@") or lines[j].startswith("def ")):
            j += 1  # further decorators and the def line
        while j < len(lines) and (not lines[j].strip() or lines[j][:1].isspace()):
            j += 1
        while j > i + 1 and not lines[j - 1].strip():
            j -= 1
        spans[m.group(1)] = (i, j)
        i = j
    return spans


def graft(text, donor, ids):
    """text with each gene in ids replaced by the donor's version of it (genes the text lacks are left out).
    Returns (new text, ids actually changed)."""
    lines, dl = text.split("\n"), donor.split("\n")
    have, give, done = gene_blocks(text), gene_blocks(donor), []
    for g in sorted((g for g in ids if g in have and g in give), key=lambda g: -have[g][0]):
        (a, b), (c, d) = have[g], give[g]
        if lines[a:b] != dl[c:d]:
            lines[a:b] = dl[c:d]
            done.append(g)
    return "\n".join(lines), sorted(done)

from .. import build as gbuild
from .score import Scorer

SEED = 1  # irrelevant to the outcome (games are fixed by map and side); kept for the command line
ANCHORS = ("policies/v7.policy", "policies/candidates/tune-v20-L1.policy",
           "policies/candidates/rall2-ca4-lean-g.policy", "policies/opp-tune5-metadraft.policy")
REF = "policies/candidates/style-gconv1.policy"


def rate(a, b, threads, fuel_mult=1.0):
    """(wins, games) of side spec a vs b over the 80 distinct games: every map once from each side."""
    maps = sorted(MAPS)
    st = Scorer([], threads=threads, fuel_mult=fuel_mult, bot_seeds=True).play(a, b, SEED, 2 * len(maps), maps=maps)
    if "error" in st:
        raise RuntimeError(st["error"])
    return st["a_wins"], st["games"]


ARENA_URL = os.environ.get("ARENA_URL", "https://138-201-121-171.sslip.io/arena")


def _http(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"X-Arena-Client": "genome-search"}),
                                timeout=60) as r:
        return r.read().decode()


def spec_of(path_or_text, kind=None):
    return Scorer([], threads=1)._spec(path_or_text, kind)


class ArenaRater:
    """Plays a gate's matches on the arena service (POST /matches: 80 games, every map from both sides, bot seeds)
    instead of locally: no run or EC2 slot needed."""

    def __init__(self, engine, priority=1):
        self.engine, self.priority = engine, priority  # gates go ahead of bulk scoring (priority 0)

    def side(self, text_or_path, kind=None):
        if kind == "genome":
            return {"text": text_or_path, "kind": "genome"}
        if str(text_or_path).endswith(".genome"):  # genome files go inline (they need not exist in the engine's tree)
            return {"text": Path(text_or_path).read_text(), "kind": "genome"}
        p = Path(text_or_path)
        rel = p.resolve().relative_to(ROOT) if p.is_absolute() or p.resolve().is_relative_to(ROOT) else p
        return f"repo:{rel.as_posix()}"

    def rate(self, a, b, threads=None, fuel_mult=1.0):
        body = json.dumps({"a": a, "b": b, "engine": self.engine, "fuel_mult": fuel_mult, "bot_seeds": True,
                           "priority": self.priority}).encode()
        req = urllib.request.Request(f"{ARENA_URL}/matches?wait=110", data=body, method="POST",
                                     headers={"X-Arena-Client": "genome-search", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=130) as r:
            m = json.loads(r.read())["match"]
        while m["status"] not in ("done", "failed", "cancelled"):
            m = json.loads(_http(f"{ARENA_URL}/matches/{m['id']}?wait=110"))
            m = m.get("match", m)
        if m["status"] != "done":
            raise RuntimeError(f"arena match {m['id']} {m['status']}")
        return m["result"]["a_wins"], m["result"]["games"]


class LocalRater:
    def side(self, text_or_path, kind=None):
        return spec_of(text_or_path, kind)

    def rate(self, a, b, threads, fuel_mult=1.0):
        return rate(a, b, threads, fuel_mult)

    def games(self, a, b, threads):
        """{(map, side of a): 1 if a won else 0} over the 80 distinct games (deterministic by map and side)."""
        from .score import EVAL
        maps = sorted(MAPS)
        out = subprocess.run([str(EVAL), "--a", a, "--b", b, "--games", str(2 * len(maps)), "--threads", str(threads),
                              "--seed", str(SEED), "--bot-seeds", "--details", *maps],
                             capture_output=True, text=True, timeout=3600)
        if out.returncode != 0:
            raise RuntimeError(f"genome_eval exit {out.returncode}: {out.stderr[-300:]}")
        g = {}
        for line in out.stdout.splitlines():
            d = json.loads(line) if line.strip().startswith("{") else {}
            if "a_side" in d:
                g[(Path(d["map"]).stem, d["a_side"])] = int(d["winner"] == (1 if d["a_side"] == "B" else 0))
        return g


def sign_p(drops, gains):
    """One-sided paired sign test: P(at least `drops` drops among the diverging games | no real difference)."""
    n = drops + gains
    return sum(math.comb(n, k) for k in range(drops, n + 1)) / 2 ** n if n else 1.0


SOLO_CAP = 4000


def solo_farm(spec, threads, with_deaths=False):
    """Rounds to 1000 gems per map vs builtin:idle (the 80 distinct games, bot seeds), the mean of the two sides. A game
    that ends at round 2000 short of 1000 gems counts 2000 + (1000 - gems) / (gems / 2000), i.e. extrapolated at its own
    average rate, capped at SOLO_CAP (also for 0 gems)."""
    from .score import EVAL
    maps = sorted(MAPS)
    out = subprocess.run([str(EVAL), "--a", spec, "--b", "builtin:idle", "--games", str(2 * len(maps)), "--threads",
                          str(threads), "--seed", str(SEED), "--bot-seeds", "--details", *maps],
                         capture_output=True, text=True, timeout=3600)
    if out.returncode != 0:
        raise RuntimeError(f"genome_eval exit {out.returncode}: {out.stderr[-300:]}")
    per, deaths = {}, []
    for line in out.stdout.splitlines():
        d = json.loads(line) if line.strip().startswith("{") else {}
        if "a_side" not in d:
            continue
        g = d["gems"][1 if d["a_side"] == "B" else 0]
        deaths.append(d["deaths"][1 if d["a_side"] == "B" else 0])  # vs idle: camps, monoliths, ...
        r = d["rounds"] if g >= 1000 else min(SOLO_CAP, 2000 + (1000 - g) * 2000 / g) if g > 0 else SOLO_CAP
        per.setdefault(Path(d["map"]).stem, []).append(r)
    per = {m: round(sum(v) / len(v), 1) for m, v in sorted(per.items())}
    return (per, round(sum(deaths) / max(1, len(deaths)), 2)) if with_deaths else per


def solo_check(cand, ref, max_slower=150, offset=3.0):
    """Block if the total rounds to 1000 gems is worse than the live bot's. A map > max_slower rounds slower blocks only
    if the total gain is < offset x that map's loss; otherwise it is a warning."""
    deltas = {m: round(cand[m] - ref[m], 1) for m in ref if m in cand}
    total_c, total_r = round(sum(cand.values()), 1), round(sum(ref.values()), 1)
    gain = total_r - total_c
    slow = {m: d for m, d in deltas.items() if d > max_slower}
    block_maps = {m: d for m, d in slow.items() if gain < offset * d}
    warn_maps = {m: d for m, d in slow.items() if m not in block_maps}
    return {"total": total_c, "ref_total": total_r, "gain": round(gain, 1), "max_slower": max_slower,
            "block_maps": block_maps, "warn_maps": warn_maps, "deltas": deltas, "total_worse": total_c > total_r,
            "blocks": total_c > total_r or bool(block_maps), "warns": bool(warn_maps)}


def gate_paired(text, ref, anchors, threads=5, min_wins=43, sign_alpha=0.1, exclude=(), bars=None, rater=None,
                solo=True, early_exit=True, ensemble=()):
    """The paired rule: head-to-head vs the live bot >= min_wins over all 80 games; an anchor blocks only if a one-sided
    sign test on the diverging games (same map and side, candidate vs ref) gives p < sign_alpha for a drop. Maps in
    `exclude` are left out of the anchor rows only. With solo, the solo-farm check (solo_farm/solo_check) runs first and,
    with early_exit, a block there skips the anchor rows. Needs a rater with per-game results (local).
    With ensemble (fuel multipliers), the head-to-head is the mean wins over those fuel levels: games are chaotic, so one
    1x sample of a candidate picked for a high one overrates it (winner's curse); h2h_1x keeps the 1x sample."""
    R = rater or LocalRater()
    spec, rspec = R.side(text, "genome"), R.side(ref)
    w, n = R.rate(spec, rspec, threads)
    rec = {"h2h_1x": w}
    if ensemble:
        ens = {str(fm): w if fm == 1.0 else R.rate(spec, rspec, threads, fuel_mult=fm)[0] for fm in ensemble}
        w = round(sum(ens.values()) / len(ens), 1)
        rec["h2h_ensemble"] = ens
    rec.update({"h2h_wins": w, "h2h_games": n, "h2h": w / n, "clear": w >= min_wins, "rule": "paired sign test",
                "sign_alpha": sign_alpha, "anchor_rows_exclude": list(exclude)})
    bars = {} if bars is None else bars
    if solo:  # the solo-farm check (vs builtin:idle) runs before the anchor rows: it is cheap and fails early
        key = f"{Path(ref).name}|solo"
        if key not in bars:
            bars[key] = solo_farm(rspec, threads)
        rec["solo_farm"] = solo_check(solo_farm(spec, threads), bars[key])
        if rec["solo_farm"]["blocks"] and early_exit:
            rec.update(anchor_deltas={}, blocked_by=["solo_farm"], passed=False,
                       warnings=[f"solo_farm {m} +{d}" for m, d in rec["solo_farm"]["warn_maps"].items()])
            return rec
    rows = {}
    for anc in anchors:
        key = f"{Path(ref).name}|{Path(anc).name}|games"
        if key not in bars:
            bars[key] = R.games(rspec, R.side(anc), threads)
        rg, cg = bars[key], R.games(spec, R.side(anc), threads)
        ks = [k for k in cg if k in rg and k[0] not in exclude]
        drops = sum(1 for k in ks if rg[k] and not cg[k])
        gains = sum(1 for k in ks if cg[k] and not rg[k])
        pv = sign_p(drops, gains)
        rows[Path(anc).stem] = {"wins": sum(cg[k] for k in ks), "ref_wins": sum(rg[k] for k in ks), "games": len(ks),
                                "diverging": drops + gains, "drops": drops, "gains": gains, "p": round(pv, 4),
                                "blocks": pv < sign_alpha}
    rec["anchor_deltas"] = rows
    rec["blocked_by"] = [a for a, r in rows.items() if r["blocks"]] + (["solo_farm"] if rec.get("solo_farm", {}).get("blocks") else [])
    rec["warnings"] = [f"solo_farm {m} +{d}" for m, d in rec.get("solo_farm", {}).get("warn_maps", {}).items()]
    fw, fn = R.rate(spec, rspec, threads, fuel_mult=10.0)
    rec.update(h2h_fuel10_wins=fw, h2h_fuel10=fw / fn)
    rec["passed"] = rec["clear"] and not rec["blocked_by"]
    return rec


def gate(text, ref, anchors, threads=5, min_wins=43, regress=0.03, bars=None, log=print, rater=None):
    """Gate one genome (source text). bars: cache {key: (wins, games)} of the reference's own anchor rates."""
    R = rater or LocalRater()
    spec, rspec = R.side(text, "genome"), R.side(ref)
    w, n = R.rate(spec, rspec, threads)
    rec = {"h2h_wins": w, "h2h_games": n, "h2h": w / n, "clear": w >= min_wins}
    bars = {} if bars is None else bars
    drops = {}
    for anc in anchors:
        key = f"{Path(ref).name}|{Path(anc).name}|{NG}"
        if key not in bars:
            bars[key] = R.rate(rspec, R.side(anc), threads)
        bw, bn = bars[key]
        cw, cn = R.rate(spec, R.side(anc), threads)
        drops[Path(anc).stem] = {"wins": cw, "ref_wins": bw, "games": cn, "delta": round((cw - bw) / cn, 3)}
    rec["anchor_deltas"] = drops
    fw, fn = R.rate(spec, rspec, threads, fuel_mult=10.0)
    rec.update(h2h_fuel10_wins=fw, h2h_fuel10=fw / fn)
    rec["passed"] = rec["clear"] and min((d["delta"] for d in drops.values()), default=0.0) >= -regress
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--arena", action="append", required=True,
                    help="arena dir on remote/genome, a chain of resumed jobs' dirs joined by +, or a job prefix "
                         "ending in * (arenaA-*: every arenaA-N job on jobs/genome, finished when all have an rc); "
                         "(e.g. arenaB-1/arena+arenaB-2/arena): the latest pushed one is read, and the chain is "
                         "finished when its last job has an rc file; or branch:<branch>:<dir>:<finished-marker path> "
                         "for an arena mirrored to a branch")
    ap.add_argument("--ref", default=str(ROOT / REF), help="the live ladder bot")
    ap.add_argument("--anchors", action="append", default=None,
                    help="comma list of anchors for the drop check; may be repeated (lists are joined)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--min-games", type=int, default=200)
    ap.add_argument("--every", type=float, default=600)
    ap.add_argument("--threads", type=int, default=5)
    ap.add_argument("--min-wins", type=int, default=43, help="head-to-head wins out of 80 to pass")
    ap.add_argument("--regate-from", default="", help="OLDREF:N: genomes gated vs OLDREF (file stem) with fewer than "
                                                      "N head-to-head wins are not re-gated vs the new --ref")
    ap.add_argument("--arena-engine", default="", help="play the gate's matches on the arena service at this engine "
                                                      "(commit sha or ref) instead of locally")
    ap.add_argument("--sign-alpha", type=float, default=0.0,
                    help="> 0: the paired rule (an anchor blocks only if a one-sided sign test on the diverging games "
                         "gives p < this); plays locally, since it needs per-game results")
    ap.add_argument("--fuel-ensemble", default="",
                    help="with --sign-alpha: comma-separated fuel multipliers; the head-to-head is the mean wins over them "
                         "(e.g. 0.96,0.98,1.0,1.02,1.04); the key gets +ens")
    ap.add_argument("--graft", default="",
                    help="comma-separated gene ids copied from the reference into every gated genome before gating "
                         "(e.g. w1: a fix the live bot carries that the arena lineage lacks); the key gets +graft:<ids>")
    ap.add_argument("--exclude-anchor-maps", default="01boss-battle",
                    help="with --sign-alpha: maps left out of the anchor rows (kept in the head-to-head)")
    ap.add_argument("--max-hours", type=float, default=12)
    ap.add_argument("--fresh", action="store_true",
                    help="ignore earlier gatekeepers' gates (a new runtime: every genome is gated again)")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "candidates").mkdir(parents=True, exist_ok=True)
    anchors = [a for part in (args.anchors or [",".join(str(ROOT / a) for a in ANCHORS)]) for a in part.split(",") if a]
    seen, bars = set(), {}
    gates = out / "gates.jsonl"
    if gates.exists():
        seen = {json.loads(l)["key"] for l in open(gates)}
    # genomes earlier gatekeeper jobs already gated stay gated
    ls = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", "origin/remote/genome"],
                        capture_output=True, text=True).stdout.split()
    for path in ([] if args.fresh else ls):
        if path.startswith("gatekeeper-") and path.endswith("/gates.jsonl"):
            txt = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/remote/genome:{path}"],
                                 capture_output=True, text=True).stdout
            seen |= {json.loads(l)["key"] for l in txt.splitlines() if l.strip()}
            if args.regate_from:  # after a live-bot change: re-gate only genomes that beat the old live bot
                old, _, need = args.regate_from.partition(":")
                for l in txt.splitlines():
                    r = json.loads(l) if l.strip() else {}
                    if f"@{old}/{NG}" in r.get("key", "") and r.get("h2h_wins", 0) < int(need or 43):
                        seen.add(r["key"].replace(f"@{old}/{NG}", f"@{Path(args.ref).stem}/{NG}"))
    ref_text = Path(args.ref).read_text() if args.ref.endswith(".genome") else None

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)

    def git(*a):
        return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)

    t_end = time.time() + args.max_hours * 3600
    while time.time() < t_end:
        t0 = time.time()
        f = git("fetch", "-q", "origin", "remote/genome")
        if f.returncode != 0:
            log(f"fetch failed: {f.stderr.strip()[:200]}")
        finished = 0
        git("fetch", "-q", "origin", "jobs/genome")
        for chain in args.arena:
            if chain.startswith("jobs:"):  # same as <prefix>* (for callers that refuse '*' in arguments)
                chain = chain[5:] + "*"
            if chain.startswith("api:"):  # an arena-service run: api:<run id>:<dir under the worktree>[=<key name>]
                spec, _, keyname = chain[4:].partition("=")
                run_id, _, rdir = spec.partition(":")
                base = f"{ARENA_URL}/runs/{run_id}"
                try:
                    status = json.loads(_http(base))["status"]
                    s = json.loads(_http(f"{base}/files/{rdir}/state.json"))
                except Exception as e:
                    log(f"{chain}: {type(e).__name__}: {e}")
                    continue
                finished += status in ("exited", "failed", "stopped", "cancelled")
                fetch = lambda p, base=base, rdir=rdir: _http(f"{base}/files/{rdir}/{p}")
                dirs, arena, job = [keyname or chain], chain, f"run{run_id}"
            elif chain.startswith("branch:"):  # a mirrored arena: branch:<branch>:<dir>:<file that marks it finished>
                br, rdir, donef = (chain[7:].split(":") + [""])[:3]
                git("fetch", "-q", "origin", br)
                st = git("show", f"origin/{br}:{rdir}/state.json")
                if st.returncode != 0:
                    log(f"{chain}: no state yet")
                    continue
                s = json.loads(st.stdout)
                finished += bool(donef) and git("cat-file", "-e", f"origin/{br}:{donef}").returncode == 0

                def fetch(p, br=br, rdir=rdir):
                    g = git("show", f"origin/{br}:{rdir}/{p}")
                    if g.returncode != 0:
                        raise FileNotFoundError(p)
                    return g.stdout
                dirs, arena, job = [rdir], chain, rdir.split("/")[0]
            elif chain.startswith("files:"):  # every .genome file in a branch dir: files:<branch>:<dir>[:<finished marker>]
                br, rdir, donef = (chain[6:].split(":") + [""])[:3]
                git("fetch", "-q", "origin", br)
                names = [n for n in git("ls-tree", "--name-only", f"origin/{br}", f"{rdir}/").stdout.split()
                         if n.endswith(".genome")]
                finished += bool(donef) and git("cat-file", "-e", f"origin/{br}:{donef}").returncode == 0
                s = {"members": {}}
                for n in names:  # one entry per file content, so an edited file is gated again
                    sha = git("rev-parse", f"origin/{br}:{n}").stdout.strip()[:12]
                    nm = f"{Path(n).stem}#{sha}"
                    s["members"][nm] = {"name": nm, "kind": "genome", "alive": True, "games": 10 ** 9, "mu": 0.0,
                                        "path": Path(n).name}

                def fetch(p, br=br, rdir=rdir):
                    g = git("show", f"origin/{br}:{rdir}/{p}")
                    if g.returncode != 0:
                        raise FileNotFoundError(p)
                    return g.stdout
                dirs, arena, job = [rdir], chain, rdir.split("/")[0]
            elif chain.endswith("*"):  # every job <prefix>N on jobs/genome, in order: a chain of resumes
                import re
                names = git("ls-tree", "--name-only", "origin/jobs/genome").stdout.split()
                jobs = sorted({n[:-3] for n in names if n.startswith(chain[:-1]) and n.endswith(".sh")},
                              key=lambda j: int(re.sub(r"\D", "", j[len(chain) - 1:]) or 0))
                dirs = [f"{j}/arena" for j in jobs]
                done = all(git("cat-file", "-e", f"origin/remote/genome:{j}/rc").returncode == 0 for j in jobs)
            else:
                dirs = chain.split("+")
                done = git("cat-file", "-e", f"origin/remote/genome:{dirs[-1].split('/')[0]}/rc").returncode == 0
            if not chain.startswith(("api:", "branch:", "files:")):
                if not dirs:
                    continue
                finished += done
                have = [d for d in dirs if git("cat-file", "-e", f"origin/remote/genome:{d}/state.json").returncode == 0]
                arena = have[-1] if have else dirs[0]
                job = arena.split("/")[0]
                st = git("show", f"origin/remote/genome:{arena}/state.json")
                if st.returncode != 0:
                    log(f"{arena}: no state yet")
                    continue
                s = json.loads(st.stdout)

                def fetch(p, arena=arena):
                    g = git("show", f"origin/remote/genome:{arena}/{p}")
                    if g.returncode != 0:
                        raise FileNotFoundError(p)
                    return g.stdout
            live = [m for m in s["members"].values() if m["kind"] == "genome" and m["alive"]
                    and m["games"] >= args.min_games]
            for m in (live if chain.startswith("files:") else sorted(live, key=lambda m: -m["mu"])[:args.top]):
                # one key per genome across a chain of resumed jobs, per reference bot
                key = (f"{dirs[0]}:{m['name']}@{Path(args.ref).stem}/{NG}" + ("/paired" if args.sign_alpha > 0 else "")
                       + (f"+graft:{args.graft}" if args.graft else "") + ("+ens" if args.fuel_ensemble else ""))
                if key in seen:
                    continue
                seen.add(key)
                if ref_text is not None and m.get("path") and fetch(m["path"]).strip() == ref_text.strip():
                    continue  # the live bot itself
                try:
                    text = fetch(m["path"])
                except Exception:
                    log(f"{key}: genome file missing")
                    continue
                grafted = []
                if args.graft and ref_text is not None:
                    text, grafted = graft(text, ref_text, args.graft.split(","))
                    if text.strip() == ref_text.strip():
                        continue  # the live bot once grafted
                log(f"gate {key} (mu {m['mu']:.2f}, {m['games']} games)" + (f" grafted {grafted}" if grafted else ""))
                try:
                    if args.sign_alpha > 0:
                        rec = gate_paired(text, args.ref, anchors, args.threads, args.min_wins, args.sign_alpha,
                                          tuple(filter(None, args.exclude_anchor_maps.split(","))), bars=bars,
                                          ensemble=tuple(float(x) for x in args.fuel_ensemble.split(",") if x))
                    else:
                        rec = gate(text, args.ref, anchors, args.threads, args.min_wins, bars=bars, log=log,
                                   rater=ArenaRater(args.arena_engine) if args.arena_engine else None)
                except Exception as e:
                    log(f"{key}: {type(e).__name__}: {e}")
                    continue
                rec = {"key": key, "arena": arena, "name": m["name"], "mu": m["mu"], "games": m["games"],
                       "ref": Path(args.ref).name, "t": round(time.time()), **({"grafted": grafted} if args.graft else {}), **rec}
                with open(gates, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
                log(f"{key}: {json.dumps({k: v for k, v in rec.items() if k not in ('key', 'arena', 't')})}"
                    f" -> {'CANDIDATE' if rec['passed'] else 'no'}")
                if rec["passed"]:
                    (out / "candidates" / f"{job}-{m['name']}.genome").write_text(text)
        if finished == len(args.arena):
            log("all arenas finished")
            break
        time.sleep(max(0, args.every - (time.time() - t0)))


if __name__ == "__main__":
    main()
