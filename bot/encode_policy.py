"""Encode a compiled policy (.pol prefix text from policygen.compile) into the interpreter's
code stream (interp::load_program_codes) as a C++ header, so the bot does no string parsing.
Block and type order are read from interp/src/policy.cpp (INTERP_BLOCKS, kTypes).
Usage: python3 bot/encode_policy.py POLICY.pol OUT.h [SOURCE_NOTE]
"""
import re, sys, pathlib

repo = pathlib.Path(__file__).resolve().parent.parent
src = (repo / "interp/src/policy.cpp").read_text()
blocks_macro = src[src.index("#define INTERP_BLOCKS(X)"):src.index("enum class Op")]
BLOCKS = re.findall(r'X\(\w+,\s*"([^"]+)"\)', blocks_macro)
TYPES = re.findall(r'"(\w+)"', src[src.index("static const char* const kTypes[]"):src.index("constexpr int kNumTypes")])
ARITY = [0 if k[k.index("(") + 1] == ")" else k.count(",") + 1 for k in BLOCKS]
MAX_VARS = int(re.search(r"constexpr int kMaxVars = (\d+);", src).group(1))
END, END_TURN, IF, ELSE, LET, KEEP, NUM, BYTES, VAR = 0xFF00, 0xFF01, 0xFF02, 0xFF03, 0xFE00, 0xFD00, 0xFC00, 0xFB00, 0xFA00

def encode(text):
    lines = text.split("\n", 1)
    assert lines[0] == "policy v0", "missing header"
    toks = lines[1].split() if len(lines) > 1 else []
    code, nums, hexes = [], [], []
    i = 0
    while i < len(toks):
        t = toks[i]; i += 1
        if t == "END": code.append(END)
        elif t == "END_TURN": code.append(END_TURN)
        elif t == "IF": code.append(IF)
        elif t == "ELSE": code.append(ELSE)
        elif t == "CONST:Num": code += [NUM, len(nums)]; nums.append(float(toks[i])); i += 1
        elif t == "CONST:Bytes": code += [BYTES, len(hexes)]; hexes.append(toks[i]); i += 1
        elif t.startswith("LET:"): code.append(LET + TYPES.index(t[4:]))
        elif t.startswith("KEEP:"): code.append(KEEP + TYPES.index(t[5:]))
        elif t.startswith("VAR:"):
            _, ty, k = t.split(":"); code.append(VAR + TYPES.index(ty) * MAX_VARS + int(k))
        else:
            if t not in BLOCKS: sys.exit(f"unknown block {t}")
            code.append(BLOCKS.index(t))
    return code, nums, hexes

def parse(code, nums, hexes):
    """Mirror of interp/src/policy.cpp Parser over the code stream: returns (exprs, steps, top)
    in the same pool layout (args contiguous in exprs; each block's steps contiguous in steps).
    An expr is (op, var, num, bytes, args_start, args_n); a step is (kind, expr, var, then, orelse)
    with then/orelse as (start, n)."""
    nb = len(BLOCKS)
    OP_NUM, OP_BYTES, OP_VAR = nb, nb + 1, nb + 2
    exprs, steps, counts = [], [], [0] * len(TYPES)
    pos = 0
    def take():
        nonlocal pos
        if pos >= len(code): sys.exit("policy: unexpected end of input")
        pos += 1
        return code[pos - 1]
    def expr():
        t = take()
        if t == NUM: return (OP_NUM, -1, nums[take()], b"", 0, 0)
        if t == BYTES:
            h = hexes[take()]
            return (OP_BYTES, -1, 0.0, b"" if h == "-" else bytes.fromhex(h), 0, 0)
        if VAR <= t < VAR + len(TYPES) * MAX_VARS: return (OP_VAR, t - VAR, 0.0, b"", 0, 0)
        if t < nb:
            arity = ARITY[t]
            k = len(exprs)
            exprs.extend([None] * arity)
            for i in range(arity): exprs[k + i] = expr()
            return (t, -1, 0.0, b"", k if arity else 0, arity)
        sys.exit(f"policy: bad code in expression {t}")
    def block():
        nonlocal pos
        local = []
        while True:
            t = take()
            if t == END:
                start = len(steps)
                steps.extend(local)
                return (start, len(local))
            if t == END_TURN: local.append((4, (OP_NUM, -1, 0.0, b"", 0, 0), -1, (0, 0), (0, 0)))
            elif t == IF:
                e = expr(); th = block(); el = (0, 0)
                if pos < len(code) and code[pos] == ELSE:
                    pos += 1
                    el = block()
                local.append((1, e, -1, th, el))
            elif (t & 0xFF00) in (LET, KEEP):
                ty = t & 0xFF
                e = expr()
                var = ty * MAX_VARS + counts[ty]; counts[ty] += 1
                local.append((3 if (t & 0xFF00) == KEEP else 2, e, var, (0, 0), (0, 0)))
            else:
                pos -= 1
                local.append((0, expr(), -1, (0, 0), (0, 0)))
    top = block()
    if pos != len(code): sys.exit("policy: trailing tokens")
    return exprs, steps, top

def cxx_bytes(b):
    return "std::string_view(\"" + "".join(f"\\{c:03o}" for c in b) + f"\", {len(b)})"

def cxx_expr(e):
    op, var, num, b, k, n = e
    args = f"{{kPolicyExprs + {k}, {n}}}" if n else "{nullptr, 0}"
    return f"{{static_cast<interp::Op>({op}), {var}, {num!r}, {cxx_bytes(b) if b else 'std::string_view()'}, {args}}}"

def cxx_span(sp):
    return f"{{kPolicySteps + {sp[0]}, {sp[1]}}}" if sp[1] else "{nullptr, 0}"

KINDS = ["interp::Step::do_", "interp::Step::if_", "interp::Step::let_", "interp::Step::keep_", "interp::Step::end_turn"]

if __name__ == "__main__":
    code, nums, hexes = encode(pathlib.Path(sys.argv[1]).read_text())
    note = sys.argv[3] if len(sys.argv) > 3 else sys.argv[1]
    out = [f"// Generated by bot/encode_policy.py from {note}; do not edit.", "#pragma once", "#include <cstddef>", "#include <cstdint>",
           f"inline constexpr std::uint16_t kPolicyCode[] = {{{', '.join(str(c) for c in code)}}};",
           f"inline constexpr double kPolicyNums[] = {{{', '.join(repr(x) for x in nums) or '0.0'}}};",
           f"inline constexpr std::size_t kPolicyNumCount = {len(nums)};",
           f"inline constexpr const char* kPolicyBytes[] = {{{', '.join(chr(34) + h + chr(34) for h in hexes) or 'nullptr'}}};",
           f"inline constexpr std::size_t kPolicyBytesCount = {len(hexes)};"]
    # The same program pre-parsed into constant-initialised node arrays (load_program_static):
    # a champion's first turn then spends nothing on parsing.
    exprs, steps, top = parse(code, nums, hexes)
    out += ['#include <string_view>', '#include "interp/program.h"',
            f"inline constexpr std::size_t kPolicyExprCount = {len(exprs)};",
            f"inline constexpr interp::Expr kPolicyExprs[{max(1, len(exprs))}] = {{" + (", ".join(cxx_expr(e) for e in exprs) or "{}") + "};",
            f"inline constexpr interp::Step kPolicySteps[{max(1, len(steps))}] = {{" +
            (", ".join(f"{{{KINDS[k]}, {cxx_expr(e)}, {v}, {cxx_span(th)}, {cxx_span(el)}}}" for k, e, v, th, el in steps) or "{}") + "};",
            f"inline constexpr std::size_t kPolicyTopStart = {top[0]};",
            f"inline constexpr std::size_t kPolicyTopCount = {top[1]};"]
    pathlib.Path(sys.argv[2]).write_text("\n".join(out) + "\n")
    print(f"{len(code)} codes, {len(nums)} numbers, {len(hexes)} byte strings")
