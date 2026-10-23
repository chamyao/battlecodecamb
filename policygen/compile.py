"""Compile a policy to the prefix format the C++ interpreter (interp/) loads.

One token per line, in the same pre-order as `grammar.encode`; a constant
token is followed by its value (`CONST:Num 0.35`, `CONST:Bytes <hex>` with
`-` for empty).
"""
import sys

from .grammar import Vocab, encode
from .text import parse

HEADER = "policy v0"


def to_prefix(steps, vocab=None):
    vocab = vocab or Vocab()
    ids, consts = encode(steps, vocab)
    lines, ci = [HEADER], 0
    for i in ids:
        tok = vocab.tokens[i]
        if tok == "CONST:Num":
            lines.append(f"{tok} {float(consts[ci])!r}")
            ci += 1
        elif tok == "CONST:Bytes":
            lines.append(f"{tok} {consts[ci].hex() or '-'}")
            ci += 1
        else:
            lines.append(tok)
    return "\n".join(lines) + "\n"


def main(argv):
    """python3 -m policygen.compile IN.policy OUT.pol"""
    src, dst = argv
    with open(src) as f:
        steps = parse(f.read())
    with open(dst, "w") as f:
        f.write(to_prefix(steps))


if __name__ == "__main__":
    main(sys.argv[1:])
