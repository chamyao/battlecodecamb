"""Compile a genome to a shared object the simulator loads (genome_eval --a genome:<path.so>).

    python3 -m genome.build my.genome            # prints the .so path (cached by source hash)
    GENOME_DEFS="GENOME_PROF" python3 -m genome.build my.genome   # extra -D flags (a GENOME_PROF genome_eval: build-prof/)

The generated C++ goes through the same compiler for every child, so compile errors mean a bug in
genome/lang.py, not in the genome: the type checker rejects bad genomes first.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import lang

ROOT = Path(__file__).resolve().parent.parent
RT = ROOT / "genome" / "runtime"
CACHE = Path(os.environ.get("GENOME_CACHE", ROOT / "genome" / "build" / "so"))
EVAL = ROOT / "genome" / "build" / "genome_eval"
FLAGS = ["-std=c++20", "-O2", "-mpopcnt", "-mbmi", "-mbmi2", "-mlzcnt", "-ffp-contract=off", "-fPIC", "-shared", "-w", f"-I{ROOT / 'sim' / 'include'}", f"-I{RT}"]


def build(source, op_fuel=None):
    """Genome source text -> path of the compiled .so. Raises lang.GenomeError on an invalid genome,
    RuntimeError on a compiler failure."""
    genome = lang.parse(source)
    cpp = lang.to_cpp(genome)
    extra = [f"-DGENOME_OP_FUEL={op_fuel}"] if op_fuel is not None else []
    extra += [f"-D{d}" for d in os.environ.get("GENOME_DEFS", "").split()]
    key = hashlib.sha256((cpp + " ".join(FLAGS + extra) + _rt_stamp()).encode()).hexdigest()[:20]
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"{key}.so"
    if out.exists():
        return out
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "genome.cpp"
        src.write_text(cpp)
        tmp = Path(td) / "genome.so"
        r = subprocess.run(["g++", *FLAGS, *extra, str(src), "-o", str(tmp)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("C++ compile failed:\n" + r.stderr[-4000:])
        os.replace(tmp, out)
    return out


def _rt_stamp():
    # the simulator's headers too: genomes inline cbs::Api (charges, layout)
    hs = sorted(RT.glob("*.h")) + sorted((ROOT / "sim" / "include" / "cbs").glob("*.h"))
    return "".join(hashlib.sha256(p.read_bytes()).hexdigest() for p in hs)


if __name__ == "__main__":
    print(build(Path(sys.argv[1]).read_text()))
